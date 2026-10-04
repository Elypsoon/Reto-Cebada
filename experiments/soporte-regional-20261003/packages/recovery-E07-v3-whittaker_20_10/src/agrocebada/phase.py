"""Orquestación secuencial de experimentos congelados y su registro incremental."""
import argparse
from dataclasses import asdict
from pathlib import Path
import os
import shutil
import subprocess
import sys
import time
import traceback
import importlib.util
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import psutil
from threadpoolctl import threadpool_limits
from .common import ROOT,WORKSPACE,PROCESSED,ARTIFACTS,ID,TARGET,SEED,CUTOFF,sha256,write_json,dependencies,code_hash
from . import modeling as m,robust as r,variants as v
from .tracking import Registry,read,atomic_json,snapshot_code,compare_frames,LIMITATION,manifest

EXPERIMENTS=['E00','E01a','E01b','E02','E03','E04a','E04b','E05','E06','E07','E08']
HYPOTHESES={'E00':'Reproducción del control regional','E01a':'Atenuación dura con menos de diez etiquetas estatales','E01b':'Atenuación gradual por tamaño estatal','E02':'Centrado de predictores y selección dentro del estado','E03':'Sustitución de Whittaker nube 20 por nube 40','E04a':'Conservación de segmentos temporales respaldados','E04b':'AUC respaldada EVI/MSAVI','E05':'Ablación de sensores y conteos de adquisición','E06':'Ruido GPR y optimización acotada','E07':'Candidato TabPFN-2.5','E08':'Combinación predeclarada E01a+E02+E04a'}

def prepare():
    registry=Registry(ROOT)
    if (ROOT/'registry/catalog.json').exists():raise ValueError('La fase ya está congelada')
    master=gpd.read_parquet(PROCESSED/'parcels.parquet');r.validate_population(master)
    from .segments import prepare_segment_tables
    prepare_segment_tables(master,pd.read_parquet(PROCESSED/'satellite.parquet'))
    assignments=pd.read_csv(Path(WORKSPACE['legacy_root'])/'artifacts/schemes.csv')
    labeled=master[master[TARGET].notna()].copy();groups=pd.Series(index=labeled[ID],dtype=int)
    for state,part in labeled.groupby('Estado'):
        groups.loc[part[ID]]=r.canonical_groups(part,3)
    extra=pd.DataFrame({ID:labeled[ID].to_numpy(),'scheme':'intraestado-3','fold':groups.reindex(labeled[ID]).to_numpy(dtype=int)})
    pd.concat([assignments,extra],ignore_index=True).to_csv(ROOT/'registry/schemes.csv',index=False)
    write_json(ROOT/'registry/scheme-validation.json',{name:{'counts':g.fold.value_counts().sort_index().to_dict(),'valid':bool(g.fold.value_counts().min()>=15 and 138-g.fold.value_counts().max()>=80)} for name,g in pd.concat([assignments,extra]).groupby('scheme')})
    digest=snapshot_code(ROOT)
    catalog={'schema_version':1,'phase_id':ROOT.name,'code_hash':digest,'scheme_hash':sha256(ROOT/'registry/schemes.csv'),'data_hashes':{n:sha256(PROCESSED/n) for n in ['parcels.parquet','satellite.parquet','source-manifest.json']},'experiments':[],'combined':['E01a','E02','E04a'],'promotion_experiment':'E08','activated':False}
    all_tables,all_external,_=m.load_tables(master)
    v.configure('E00');common_policy=r.policy()
    for experiment in EXPERIMENTS:
        v.configure(experiment)
        keys=v.keys_for(experiment)
        grid=[asdict(c) for c in m.candidate_grid({key:all_tables[key] for key in keys})] if experiment!='E07' else []
        protocol={'experiment':experiment,'hypothesis':HYPOTHESES[experiment],'keys':keys,'candidates':grid,'routes':['official','selected'] if experiment in ['E00','E08'] else ['official'],'schemes':r.SCHEMES+(['intraestado-3'] if experiment in ['E00','E08'] else []),'support':'hard' if experiment in ['E01a','E08'] else 'soft' if experiment=='E01b' else 'none','centered':experiment in ['E02','E08'],'seed':SEED,'cutoff':CUTOFF,'data_hashes':catalog['data_hashes'],'code_hash':digest,'dependency_manifest':dependencies(),'scheme_hash':catalog['scheme_hash'],'feature_manifest':{key:sha256(PROCESSED/f'features_{key}.parquet') for key in keys},'admission':{'rmse_ratio':.98,'better_folds':2,'state_n':10,'state_mae_ratio':1.1},'optional':experiment=='E07','combined':['E01a','E02','E04a'] if experiment=='E08' else None}
        protocol.update(external_manifest={s:sha256(PROCESSED/f'external_{s}.parquet') for s in all_external} if experiment in ['E00','E08'] else {},population={'total':197,'labeled':138,'hidden':59},ensembles=common_policy['ensembles'],external_ablations=common_policy['external_ablations'] if experiment in ['E00','E08'] else [],promotion=common_policy['promotion'],interval=common_policy['interval'],grid=grid,mandatory=experiment!='E07',max_candidates=160)
        if experiment=='E07':protocol['optional_preflight']=read(ROOT/'optional/tabpfn-2.5/preflight.json')
        control='H01-regional' if experiment=='E00' else 'E04a' if experiment=='E04b' else 'E00'
        folder=registry.create(experiment,protocol,control=control,run_id=experiment)
        if experiment=='E07' and protocol['optional_preflight']['available']:
            for key in keys:
                child={**protocol,'keys':[key],'parent_experiment':'E07','optional_config':key}
                registry.create('E07',child,control='E00',parent='E07',run_id='E07-'+key)
        catalog['experiments'].append({'experiment':experiment,'run_id':folder.name,'control':control,'protocol_hash':sha256(folder/'protocol.json'),'optional':experiment=='E07'})
    atomic_json(ROOT/'registry/catalog.json',catalog)
    atomic_json(ROOT/'registry/catalog-receipt.json',{'sha256':sha256(ROOT/'registry/catalog.json')})
    atomic_json(ROOT/'registry/historical-schemes.json',{'source_hash':sha256(legacy/'artifacts/schemes.csv') if (legacy:=Path(WORKSPACE['legacy_root'])) else None,'expected_hash':'b988b4e089c298c1442808b1aa549251448a17dbcbba0437f120cfb6f98b23c0'})
    assert sha256(legacy/'artifacts/schemes.csv')=='b988b4e089c298c1442808b1aa549251448a17dbcbba0437f120cfb6f98b23c0'
    labeled.to_crs(32614).merge(extra,on=ID,validate='one_to_one').to_parquet(ROOT/'registry/intraestado-zones.parquet',index=False)
    active=Path(WORKSPACE['active_root']);legacy=Path(WORKSPACE['legacy_root'])
    assert sha256(active/'artifacts/validation.json')=='2ecea854357a4a63f4f846aa420fecc42c0642a7e6301f53bcf0cddd1359d4b7'
    assert sha256(legacy/'artifacts/phase-comparison.json')=='a95c481a1e528a46e40d38545b5e00955403bbd8366d51de55fda5a00392370a'
    for experiment,root in [('H00-vigente',active),('H01-regional',legacy)]:
        if experiment=='H00-vigente':
            data=read(root/'artifacts/validation.json');metrics={'selected':{'principal-5':data['metrics']['selected']},'official':{'principal-5':data['metrics']['official']}}
        else:
            data=read(root/'artifacts/phase-comparison.json');metrics={route:{scheme:values[route] for scheme,values in data['schemes'].items()} for route in ['selected','official']}
        source_report=root/'artifacts'/('validation.json' if experiment=='H00-vigente' else 'phase-comparison.json')
        registry.import_history(experiment,metrics,{'root':str(root),'report_hash':sha256(source_report),'source_modified_utc':__import__('datetime').datetime.fromtimestamp(source_report.stat().st_mtime,__import__('datetime').timezone.utc).isoformat(),'version_manifest':str(ROOT/('active-manifest.json' if experiment=='H00-vigente' else 'baseline-source-manifest.json'))})
    diagnostic={}
    for scheme in r.SCHEMES:
        old=pd.read_csv(legacy/f'artifacts/oof-{scheme}.csv');tlax=old[old.Estado.eq('Tlaxcala')]
        diagnostic[scheme]={'tlaxcala_bias':float((tlax.selected-tlax[TARGET]).mean()),'source_hash':sha256(legacy/f'artifacts/oof-{scheme}.csv'),'train_counts_by_fold':{str(fold):labeled.set_index(ID).reindex(old.loc[old.spatial_group.ne(fold),ID]).Estado.value_counts().to_dict() for fold in sorted(old.spatial_group.unique())}}
    atomic_json(ROOT/'registry/diagnostic-antecedents.json',{'missing_s2_peak_labeled':int(all_tables['whittaker_20_10'].reindex(labeled[ID]).s2_peak_doy.isna().sum()),'state_counts':labeled.Estado.value_counts().to_dict(),'diagnostics':diagnostic,'future_data':read(legacy/'artifacts/future-data-priorities.json')})
    v.configure('E00');r.active_intact();print('Catálogo y controles congelados; todos los experimentos pendientes',flush=True)

def control_frame(experiment,scheme,route,control_id=None):
    if experiment=='E00':return pd.read_csv(Path(WORKSPACE['legacy_root'])/f'artifacts/oof-{scheme}.csv') if scheme in r.SCHEMES else None
    control=control_id or ('E04a' if experiment=='E04b' else 'E00')
    path=ROOT/'runs'/control/f'artifacts/oof-{scheme}.csv'
    if not path.exists():raise ValueError('Control pendiente o incompatible')
    return pd.read_csv(path)

def verify_run(run_id):
    from .inference import Predictor,official_export
    folder=ROOT/'runs'/run_id;protocol=read(folder/'protocol.json');Registry(ROOT).validate_protocol(run_id)
    result={'passed':True,'routes':{},'metrics':True}
    for route in protocol['routes']:
        predictor=Predictor(route);generated=official_export(predictor)
        name='predictions_59.csv' if route=='selected' else 'predictions_official_only_59.csv'
        saved=pd.read_csv(ARTIFACTS/name)
        if not generated[ID].equals(saved[ID]) or not np.allclose(generated[TARGET],saved[TARGET],atol=1e-10,rtol=0):raise ValueError('Predicciones no reproducibles')
        for pid in generated[ID].iloc[:3]:
            _,explanation=predictor.explain(pid)
            if not np.isclose(explanation['reference_total']+explanation['correction_total'],explanation['prediction'],atol=1e-10):raise ValueError('Explicación incompatible')
        if not np.allclose(predictor.predict(generated[ID]).PRODUCCION_T,predictor.predict(generated[ID])[TARGET]*predictor.predict(generated[ID]).AREA_HA):raise ValueError('Producción incompatible')
        result['routes'][route]={'predictions':59,'hash':sha256(ARTIFACTS/name),'contract':sha256(ARTIFACTS/f'contract_{route}.json')}
    for scheme in protocol['schemes']:
        frame=pd.read_csv(ARTIFACTS/f'oof-{scheme}.csv');report=read(ARTIFACTS/f'validation-{scheme}.json')
        for name,expected in report['metrics'].items():
            if any(not np.isclose(value,expected[key],atol=1e-10) for key,value in m.metric(frame[TARGET],frame[name]).items()):raise ValueError('Métricas no reproducibles')
    atomic_json(ARTIFACTS/'fresh-process-check.json',result);print(result,flush=True);return result

def run(run_id):
    registry=Registry(ROOT);folder=ROOT/'runs'/run_id
    protocol=registry.validate_protocol(run_id);experiment=protocol['experiment'];v.configure(experiment)
    if sha256(ROOT/'registry/catalog.json')!=read(ROOT/'registry/catalog-receipt.json')['sha256']:raise ValueError('Catálogo alterado')
    if ARTIFACTS!=folder/'artifacts':raise ValueError('Destino de ejecución incompatible')
    if experiment=='E07':
        evidence=protocol['optional_preflight']
        atomic_json(ARTIFACTS/'optional-preflight.json',evidence)
        if not evidence['available']:
            registry.transition(run_id,'skipped',evidence['reason']);print('E07 omitido:',evidence,flush=True);return
        from .optional import run_optional
        return run_optional(protocol,run_id)
    old=read(folder/'run.json')
    resume=old['status'] in ['running','interrupted']
    if resume:
        if old['status']=='running' and psutil.pid_exists(old.get('pid',-1)):raise ValueError('Ya existe un escritor en marcha')
        registry.recover(run_id,protocol)
    else:registry.transition(run_id,'running')
    started=time.perf_counter()
    try:
        master=gpd.read_parquet(PROCESSED/'parcels.parquet');r.validate_population(master)
        tables,external,location=m.load_tables(master);tables={key:tables[key] for key in protocol['keys']}
        if json.loads(json.dumps([asdict(c) for c in m.candidate_grid(tables)]))!=protocol['candidates']:raise ValueError('Grilla diferente del protocolo')
        external=external if experiment in ['E00','E08'] else {}
        assignments=pd.read_csv(ROOT/'registry/schemes.csv');assignments.to_csv(ARTIFACTS/'schemes.csv',index=False)
        shutil.copy2(folder/'protocol.json',ARTIFACTS/'selection-policy.json')
        receipt={'policy_hash':sha256(ARTIFACTS/'selection-policy.json'),'scheme_hash':sha256(ARTIFACTS/'schemes.csv')}
        atomic_json(ARTIFACTS/'freeze-receipt.json',receipt)
        indices=np.flatnonzero(master[TARGET].notna());hidden=np.flatnonzero(master[TARGET].isna());y=master[TARGET].to_numpy();states=master.Estado.to_numpy();reports={};groups_by_scheme={};metrics={route:{} for route in protocol['routes']};peak=psutil.Process().memory_info().rss
        with threadpool_limits(limits=2):
            for scheme in protocol['schemes']:
                groups=np.full(len(master),-1);groups[indices]=assignments[assignments.scheme.eq(scheme)].set_index(ID).reindex(master.iloc[indices][ID]).fold.to_numpy();groups_by_scheme[scheme]=groups
                if np.bincount(groups[indices]).min()<15 or len(indices)-np.bincount(groups[indices]).max()<80:raise ValueError('Esquema no viable')
                completed=read(ARTIFACTS/'checkpoint.json')['completed_schemes'] if resume and (ARTIFACTS/'checkpoint.json').exists() else []
                reports[scheme]=read(ARTIFACTS/f'validation-{scheme}.json') if scheme in completed else r.evaluate(scheme,master,tables,external,location,groups,indices)
                peak=max(peak,psutil.Process().memory_info().rss)
                frame=pd.read_csv(ARTIFACTS/f'oof-{scheme}.csv')
                for route in protocol['routes']:
                    values={**m.metric(frame[TARGET],frame[route]),'bias':float((frame[route]-frame[TARGET]).mean())}
                    control=control_frame(experiment,scheme,route,old['control_run_id'])
                    if control is not None:
                        paired=compare_frames(frame,control,route);paired.to_csv(ARTIFACTS/f'comparison-{scheme}-{route}.csv',index=False)
                        values['control_delta_rmse']=values['rmse']-m.metric(control[TARGET],control[route])['rmse']
                        if experiment=='E00':
                            for name in ['selected','official','regional_mean','gpr','catboost']:
                                if not np.allclose(frame[name],control[name],atol=1e-10,rtol=0):raise ValueError(f'E00 no reproduce {scheme}/{name}')
                    values['regional_rmse']=m.metric(frame[TARGET],frame.regional_mean)['rmse'];metrics[route][scheme]=values
                checkpoint_files={name:digest for name,digest in manifest(ARTIFACTS).items() if name!='checkpoint.json'}
                atomic_json(ARTIFACTS/'checkpoint.json',{'completed_schemes':list(reports),'protocol_hash':sha256(folder/'protocol.json'),'manifest':checkpoint_files})
            groups=groups_by_scheme[r.SCHEMES[0]]
            official=m.select(indices,y,groups,states,tables,external,location,False)
            selected=m.select(indices,y,groups,states,tables,external,location,True,base_scores=official['_raw_scores']) if external else official
            cal=m.calibrate(indices,y,groups,states,tables,external,location)
            ok=bool(reports[r.SCHEMES[0]]['interval']['valid_n']==138 and reports[r.SCHEMES[0]]['interval']['coverage']>=.85 and cal and cal['calibration_n']>=25)
            reports[r.SCHEMES[0]]['interval'].update(available=ok,calibration_min=25,limitation='Cobertura empírica de desarrollo; sin garantía temporal ni estatal')
            for route,s in [('official',official),('selected',selected)]:
                route_cal=cal if route=='selected' or not external else m.calibrate(indices,y,groups,states,tables,{},location) if experiment=='E08' else None
                interval_stats=reports[r.SCHEMES[0]]['interval_by_route'][route]
                route_ok=bool(route_cal and (ok if route=='selected' or not external else interval_stats['valid_n']==138 and interval_stats['coverage']>=.85))
                interval_stats['available']=route_ok if experiment!='E00' or route=='selected' else False
                model=m.fit_selection(s,indices,y,tables,external,location);r.save_bundle(route,s,model,route_cal if route_ok and (experiment!='E00' or route=='selected') else None,tables,external,location,receipt)
                values=m.predict_selection(model,s,hidden,tables,external,location)
                if not np.isfinite(values).all() or (values<0).any():raise ValueError('Predicciones inválidas; no se recortan')
                pd.DataFrame({ID:master.iloc[hidden][ID].to_numpy(),TARGET:values}).sort_values(ID).to_csv(ARTIFACTS/('predictions_59.csv' if route=='selected' else 'predictions_official_only_59.csv'),index=False)
                if experiment=='E00':
                    expected=pd.read_csv(Path(WORKSPACE['legacy_root'])/'artifacts'/('predictions_59.csv' if route=='selected' else 'predictions_official_only_59.csv'))
                    got=pd.read_csv(ARTIFACTS/('predictions_59.csv' if route=='selected' else 'predictions_official_only_59.csv'))
                    if not got[ID].equals(expected[ID]) or not np.allclose(got[TARGET],expected[TARGET],rtol=0,atol=1e-10):raise ValueError('E00 no reproduce ajuste final')
            if experiment=='E08':r.stress(master,tables,external,location,groups,indices)
        atomic_json(ARTIFACTS/'resources.json',{'seconds':time.perf_counter()-started,'max_rss_at_scheme_end_mb':peak/1024**2,'cpu_threads':2,'gpu':False})
        pd.read_csv(ARTIFACTS/'oof-principal-5.csv').to_csv(ARTIFACTS/'oof.csv',index=False)
        pd.read_csv(ARTIFACTS/'selected-features-principal-5.csv').to_csv(ARTIFACTS/'selected-features.csv',index=False)
        write_json(ARTIFACTS/'validation.json',{**reports[r.SCHEMES[0]],'by_state':{s:z['selected'] for s,z in reports[r.SCHEMES[0]]['by_state'].items()},'final_selection':r.serial(selected)})
        result={'hypothesis':protocol['hypothesis'],'procedure':{key:protocol[key] for key in ['keys','support','centered','routes','combined']},'model_final':{route:read(ARTIFACTS/f'contract_{route}.json')['selection'] for route in protocol['routes']},'folds':{scheme:[{'fold':f['fold'],'selection':f['selection']['candidates'],'outer_statistics':f['outer_component_statistics'],'state_counts':f['state_training_counts']} for f in report['folds']] for scheme,report in reports.items()},'model_hashes':{route:sha256(ARTIFACTS/f'model_{route}.joblib') for route in protocol['routes']},'control_run_id':read(folder/'run.json')['control_run_id'],'model_absent':False}
        control_id=result['control_run_id'];control_folder=ROOT/'runs'/control_id
        control_protocol=read(control_folder/'protocol.json')
        result['procedure_delta']={key:{'before':control_protocol.get(key),'after':protocol.get(key)} for key in protocol if control_protocol.get(key)!=protocol.get(key)}
        result['final_statistics']={route:read(ARTIFACTS/f'contract_{route}.json')['component_statistics'] for route in protocol['routes']}
        result['model_by_fold_route']={scheme:[{'fold':f['fold'],'statistics':f['statistics_by_route'],'selections':{route:f['selection' if route=='selected' else 'official_selection'] for route in protocol['routes']}} for f in report['folds']] for scheme,report in reports.items()}
        previous_root=Path(control_protocol.get('origin',{}).get('root',control_folder))
        result['previous_model_hashes']={route:sha256(previous_root/f'artifacts/model_{route}.joblib') if (previous_root/f'artifacts/model_{route}.joblib').exists() else None for route in protocol['routes']}
        result['recovery']={'code_snapshot':str(ROOT/'versions'/protocol['code_hash']),'data_manifest':manifest(PROCESSED),'dependency_manifest':protocol['dependency_manifest'],'artifact_root':str(ARTIFACTS),'workspace_manifest':sha256(ROOT/'workspace.json')}
        frequencies=[]
        for scheme,report in reports.items():
            for fold in report['folds']:
                for route in protocol['routes']:
                    for c in fold['selection' if route=='selected' else 'official_selection']['candidates']:frequencies.append({'scheme':scheme,'fold':fold['fold'],'route':route,**c})
        pd.DataFrame(frequencies).to_csv(ARTIFACTS/'selection-frequencies.csv',index=False)
        quality={key:{'table_hash':sha256(PROCESSED/f'features_{key}.parquet'),'columns':len(t.columns),'missing_by_state':t.iloc[indices].isna().groupby(states[indices]).sum().to_dict(orient='index')} for key,t in tables.items()}
        atomic_json(ARTIFACTS/'feature-quality.json',quality)
        pd.DataFrame([{'scheme':scheme,'fold':f['fold'],**score['candidate'],'inner_rmse':score['rmse']} for scheme,report in reports.items() for f in report['folds'] for score in f['official_selection']['scores']]).to_csv(ARTIFACTS/'inner-candidate-diagnostics.csv',index=False)
        env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),AGROCEBADA_ARTIFACTS=str(ARTIFACTS),PYTHONDONTWRITEBYTECODE='1')
        subprocess.run([sys.executable,'-m','agrocebada.phase','verify','--run-id',run_id],cwd=ROOT,env=env,check=True)
        verification=read(ARTIFACTS/'fresh-process-check.json')
        decisions={}
        if experiment=='E08':
            for route in protocol['routes']:
                copy={}
                for scheme in r.SCHEMES:
                    report=reports[scheme];copy[scheme]={**report,'metrics':{**report['metrics'],'selected':report['metrics'][route]},'by_state':{state:{**stats,'selected':stats[route]} for state,stats in report['by_state'].items()}}
                decision=r.promotion(copy,True);decisions[route]={**decision,'eligible':decision['promote'],'activated':False};atomic_json(ARTIFACTS/f'eligibility-{route}.json',decisions[route])
            historic=pd.read_csv(Path(WORKSPACE['active_root'])/'artifacts/oof.csv')
            for route in protocol['routes']:compare_frames(pd.read_csv(ARTIFACTS/'oof-principal-5.csv'),historic,route).to_csv(ARTIFACTS/f'comparison-H00-{route}.csv',index=False)
            primary=reports[r.SCHEMES[0]]
            atomic_json(ARTIFACTS/'eligibility-thresholds.json',{'primary_rmse_max':.98*primary['metrics']['regional_mean']['rmse'],'state_mae_max':{state:1.1*z['regional_mean']['mae'] for state,z in primary['by_state'].items() if z['n']>=10}})
        atomic_json(ARTIFACTS/'phase-comparison.json',{'schemes':{s:z['metrics'] for s,z in reports.items()},'decision':decision if experiment=='E08' else {'promote':False},'limitation':LIMITATION})
        decision={'promotion_scope':'E08' if experiment=='E08' else 'exploratorio','activated':False,'by_route':decisions,'reason':'Elegibilidad separada de activación; conservar activa'}
        lines=[f'# {experiment}: {protocol["hypothesis"]}','',LIMITATION,'',f'Control: {read(folder/"run.json")["control_run_id"]}.','', '| ruta | esquema | RMSE | MAE | sesgo | cambio RMSE |','| --- | --- | --- | --- | --- | --- |']
        for route,schemes in metrics.items():
            for scheme,z in schemes.items():lines.append(f'| {route} | {scheme} | {z["rmse"]:.6f} | {z["mae"]:.6f} | {z["bias"]:.6f} | {z.get("control_delta_rmse",0):.6f} |')
        lines+=['','Cambios, selección por ajuste y modelos finales: [changes.json](changes.json).','', 'Decisión: '+str(decision),'','Tiempo y memoria: [resources.json](artifacts/resources.json).']
        lines+=['','## Resultados por estado','', '| ruta | esquema | estado | n | RMSE | MAE | sesgo | MAE regional |','| --- | --- | --- | --- | --- | --- | --- | --- |']
        regions={}
        for scheme in protocol['schemes']:
            frame=pd.read_csv(ARTIFACTS/f'oof-{scheme}.csv');regions[scheme]={}
            for state,part in frame.groupby('Estado'):
                regions[scheme][state]={route:{**m.metric(part[TARGET],part[route]),'bias':float((part[route]-part[TARGET]).mean()),'n':len(part),'regional_mae':m.metric(part[TARGET],part.regional_mean)['mae']} for route in protocol['routes']}
                for route,z in regions[scheme][state].items():lines.append(f'| {route} | {scheme} | {state} | {z["n"]} | {z["rmse"]:.6f} | {z["mae"]:.6f} | {z["bias"]:.6f} | {z["regional_mae"]:.6f} |')
        atomic_json(ARTIFACTS/'regional-results.json',regions)
        (folder/'result.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        r.active_intact();registry.finish(run_id,metrics,verification,result,decision)
        print('COMPLETADO',run_id,metrics,flush=True)
    except BaseException as error:
        atomic_json(ARTIFACTS/'failure.json',{'error':repr(error),'traceback':traceback.format_exc(),'model_absent':not (ARTIFACTS/'model_official.joblib').exists()})
        registry.transition(run_id,'interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',repr(error));raise

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run','verify','report']);parser.add_argument('--run-id');args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='run':run(args.run_id)
    elif args.action=='verify':verify_run(args.run_id)
    else:Registry(ROOT).publish()

if __name__=='__main__':main()
