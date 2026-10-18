"""Protocolo congelado: tres evaluaciones de desarrollo y promoción separada."""
from pathlib import Path
from dataclasses import asdict
import json
import time
from collections import Counter
import numpy as np
import pandas as pd
import geopandas as gpd
import joblib
from threadpoolctl import threadpool_limits
from .common import ROOT,PROCESSED,ARTIFACTS,WORKSPACE,DATASET,ID,TARGET,SEED,CUTOFF,write_json,sha256,code_hash,dependencies
from . import modeling as m

SCHEMES=['principal-5','balanceado-4','rotado-45-5']

def active_intact():
    origin=Path(WORKSPACE['active_root']);expected=json.loads((ROOT/'active-manifest.json').read_text(encoding='utf-8'))
    assert all((origin/p).exists() and sha256(origin/p)==h for p,h in expected.items()),'Se modificó la versión activa'
    return True

def canonical_groups(master,n,angle=0):
    pts=master.to_crs(32614).geometry.representative_point();xy=np.column_stack([pts.x,pts.y]);xy-=xy.mean(axis=0)
    a=np.deg2rad(angle);xy=xy@np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
    ids=master[ID].to_numpy();blocks=[np.arange(len(master))]
    while len(blocks)<n:
        i=max(range(len(blocks)),key=lambda i:len(blocks[i]));b=blocks.pop(i)
        axis=int(np.ptp(xy[b],axis=0).argmax());order=b[np.lexsort((ids[b],xy[b,axis]))];mid=len(order)//2
        blocks.extend([order[:mid],order[mid:]])
    groups=np.empty(len(master),int)
    for i,b in enumerate(blocks):groups[b]=i
    return groups

def policy():
    return {'run_id':WORKSPACE['run_id'],'seed':SEED,'grid':[asdict(c) for c in m.candidate_grid(['monthly_20_10','whittaker_20_10'])],
        'external_ablations':[{'family':f,'sources':s} for f in ['gpr','catboost'] for s in [['nasa'],['siap'],['nasa','siap']]],
        'ensembles':[['gpr','catboost'],['regional_mean','gpr'],['regional_mean','catboost'],['regional_mean','gpr','catboost']],
        'admission':{'rmse_ratio':.98,'better_inner_folds':2,'state_min_n':10,'state_mae_ratio':1.1,'source_order':'independiente, pareado contra ganador oficial'},
        'promotion':{'principal_ratio':.98,'min_improved_schemes':2,'mean_ratio':.98,'max_ratio':1.05,'state_mae_ratio':1.1,'all_schemes_valid':True,'verification_required':True},
        'schemes':SCHEMES,'outer_min_validation':15,'outer_min_train':80,'inner':'leave-one-existing-group-out','stress':['leave-one-state-out','buffer_1000m'],
        'interval':{'nominal':.9,'min_calibration':25,'min_principal_coverage':.85},'data_version':sha256(PROCESSED/'parcels.parquet'),'created_before_training':True,
        'limitation':'Desarrollo sobre las mismas 138 etiquetas; sin test independiente, campaña adicional ni evaluación oficial'}

def freeze():
    active_intact();ARTIFACTS.mkdir(parents=True,exist_ok=True)
    p=ARTIFACTS/'selection-policy.json'
    # Copied historic policy is archived locally once; never replace this frozen policy.
    if p.exists() and json.loads(p.read_text(encoding='utf-8')).get('run_id')!=WORKSPACE['run_id']:
        p.rename(ARTIFACTS/'historic-selection-policy.json')
    expected=json.loads(json.dumps(policy(),ensure_ascii=False))
    if p.exists():assert json.loads(p.read_text(encoding='utf-8'))==expected,'Política congelada modificada'
    else:write_json(p,expected)
    master=gpd.read_parquet(PROCESSED/'parcels.parquet');labeled=master[master[TARGET].notna()].copy()
    original=pd.read_csv(Path(WORKSPACE['snapshot'])/'artifacts/folds.csv').set_index(ID)
    assignments={'principal-5':original.reindex(labeled[ID]).spatial_group.to_numpy(),
        'balanceado-4':canonical_groups(labeled,4),'rotado-45-5':canonical_groups(labeled,5,45)}
    rows=[];validity={}
    for name,groups in assignments.items():
        counts=pd.Series(groups).value_counts();valid=bool(groups.shape==(138,) and np.isfinite(groups).all() and counts.min()>=15 and 138-counts.max()>=80)
        validity[name]={'valid':valid,'counts':counts.sort_index().to_dict(),'minimum_train':int(138-counts.max())}
        rows.extend({ID:pid,'scheme':name,'fold':int(group)} for pid,group in zip(labeled[ID],groups))
    dest=ARTIFACTS/'schemes.csv';frame=pd.DataFrame(rows)
    if dest.exists():pd.testing.assert_frame_equal(pd.read_csv(dest),frame)
    else:frame.to_csv(dest,index=False)
    receipt={'policy_hash':sha256(p),'scheme_hash':sha256(dest),'data_hash':sha256(PROCESSED/'parcels.parquet'),'validity':validity,'frozen_before_first_fit':True}
    receipt_path=ARTIFACTS/'freeze-receipt.json'
    if receipt_path.exists():
        old=json.loads(receipt_path.read_text(encoding='utf-8'))
        assert all(old[k]==receipt[k] for k in ['policy_hash','scheme_hash','data_hash']),'Protocolo alterado después de congelar'
    else:write_json(receipt_path,receipt)
    print('Protocolo congelado:',receipt,flush=True);return receipt

def validate_population(master):
    labeled=master[TARGET].notna();valid=np.isfinite(master.loc[labeled,TARGET])&master.loc[labeled,TARGET].gt(0)
    if len(master)!=197 or not master[ID].is_unique or labeled.sum()!=138 or (~labeled).sum()!=59 or not valid.all():
        raise ValueError('Bloqueado: deben conservarse 197 identificadores, 138 etiquetas válidas y 59 ocultos')
    if not (master.loc[labeled,'CONJUNTO']=='ENTRENAMIENTO').all() or not (master.loc[~labeled,'CONJUNTO']=='PREDICCION').all():raise ValueError('Separación oficial incompatible')

def validate_corrections(records,master):
    validate_population(master)
    for row in records:
        required=['id','field','old','new','source','reason','date','original_hash','derived_hash','evidence','version']
        if any(k not in row for k in required) or not row['evidence'] or row['reason']=='high_residual':raise ValueError('Corrección sin evidencia del original')
        path=Path(row['source'])
        if not path.is_file() or sha256(path)!=row['original_hash']:raise ValueError('Original alterado o inexistente')
        if row.get('action')=='drop_parcel':raise ValueError('Retirar parcelas de evaluación está prohibido')
        if row['id'] not in set(master[ID]):raise ValueError('Identificador no oficial')
    return True

def diagnostics(oof,tag):
    master=gpd.read_parquet(PROCESSED/'parcels.parquet').drop(columns='geometry');validate_population(master)
    labeled=master[master[TARGET].notna()]
    assert len(oof)==138 and oof[ID].is_unique and set(oof[ID])==set(labeled[ID])
    d=labeled.merge(oof[[ID,'selected','regional_mean']],on=ID,validate='one_to_one')
    for key in ['monthly_20_10','whittaker_20_10']:
        q=pd.read_parquet(PROCESSED/f'quality_{key}.parquet')
        assert not q.duplicated([ID,'sensor']).any()
        wide=q.pivot(index=ID,columns='sensor',values=['usable','observations','missing_cloud']);wide.columns=[f'{key}__{a}__{b}' for a,b in wide.columns]
        d=d.merge(wide,on=ID,validate='one_to_one')
        x=pd.read_parquet(PROCESSED/f'features_{key}.parquet');d[f'{key}__missing_variables']=d[ID].map(x.isna().sum(axis=1))
        missing=x.reindex(d[ID]).isna();missing.index=pd.Index(d.Estado)
        missing.groupby(level=0).sum().to_csv(ARTIFACTS/f'diagnostic-{tag}-{key}-missing.csv')
    coverage=pd.read_parquet(PROCESSED/'parcel-raster-coverage.parquet');assert not coverage.duplicated([ID,'variable']).any()
    support=coverage.groupby(ID).coverage.agg(['min','mean']).rename(columns={'min':'raster_coverage_min','mean':'raster_coverage_mean'})
    d=d.merge(support,on=ID,validate='one_to_one');assert len(d)==138 and d.raster_coverage_mean.notna().all()
    d['error']=d.selected-d[TARGET];d['abs_error']=d.error.abs();d['squared_error']=d.error**2;d['squared_error_share']=d.squared_error/d.squared_error.sum()
    d.to_csv(ARTIFACTS/f'diagnostic-{tag}-parcels.csv',index=False)
    results={}
    for level in ['Estado','Municipio']:
        rows=[]
        for labels,part in d.groupby(['Estado'] if level=='Estado' else ['Estado','Municipio']):
            labels=labels if isinstance(labels,tuple) else (labels,)
            row=dict(zip(['Estado'] if level=='Estado' else ['Estado','Municipio'],labels));row.update(n=len(part),small_sample=len(part)<10,squared_error_share=part.squared_error.sum()/d.squared_error.sum(),**m.metric(part[TARGET],part.selected))
            row.update({c:float(part[c].mean()) for c in d if '__' in c or c.startswith('raster_coverage')});rows.append(row)
        frame=pd.DataFrame(rows);frame.to_csv(ARTIFACTS/f'diagnostic-{tag}-{level}.csv',index=False);results[level]=rows
    write_json(ARTIFACTS/f'diagnostic-{tag}.json',results);return d

def audit_originals(d):
    source=DATASET/'Data/ID_area_rendimiento_70_30_Reto_AgroCebada.csv';original=pd.read_csv(source).set_index(ID)
    from .data import load_master
    geo=load_master().set_index(ID);review=[]
    for _,r in d[d.Estado.eq('Hidalgo')].nlargest(10,'abs_error').iterrows():
        pid=r[ID];fields={TARGET:{'processed':r[TARGET],'original':float(original.loc[pid,TARGET])},'AREA_HA':{'processed':r.AREA_HA,'original':float(original.loc[pid,'AREA_HA'])},'Estado':{'processed':r.Estado,'original':geo.loc[pid,'Estado']},'Municipio':{'processed':r.Municipio,'original':geo.loc[pid,'Municipio']}}
        discrepancies=[f for f,v in fields.items() if v['processed']!=v['original']]
        shp=next(DATASET.rglob('*.shp'))
        review.append({'id':pid,'fields':fields,'source':str(source),'source_hash':sha256(source),'geometry_source':str(shp),'geometry_source_hash':sha256(shp),'discrepancies':discrepancies,'finding':'Sin evidencia de discrepancia' if not discrepancies else 'Discrepancia de transformación demostrada','high_residual_is_evidence':False})
    write_json(ARTIFACTS/'hidalgo-original-review.json',review)
    if any(r['discrepancies'] for r in review):raise ValueError('Discrepancia demostrada: requiere transformación registrada antes de entrenar')
    records=[];validate_corrections(records,gpd.read_parquet(PROCESSED/'parcels.parquet'))
    manifest=json.loads((PROCESSED/'source-manifest.json').read_text(encoding='utf-8'))
    origin=Path(WORKSPACE['active_root'])
    for entry in manifest:
        if sha256(origin/entry['path'])!=entry['sha256']:raise ValueError('Un archivo original fue alterado')
    write_json(ARTIFACTS/'originals-check.json',{'verified_files':len(manifest),'same_hashes':True})
    write_json(ARTIFACTS/'corrections-v1.json',{'version':'v1','date':'2026-10-03','records':records,'data_hash':sha256(PROCESSED/'parcels.parquet'),'original_label_hash':sha256(source),'conclusion':'Sin correcciones verificadas; se mantienen las 138 etiquetas, ningún residuo justifica retirar casos'})
    return review

def promotion(reports,verified=False):
    ratios={};regional_fail=[];invalid=[]
    for name in SCHEMES:
        report=reports.get(name)
        if not report or not report.get('valid',False):invalid.append(name);continue
        ref=report['metrics']['regional_mean']['rmse'];model=report['metrics']['selected']['rmse']
        if not np.isfinite(ref) or ref<=0 or not np.isfinite(model):invalid.append(name+': referencia inválida');continue
        ratios[name]=model/ref
        for state,values in report['by_state'].items():
            if values['n']>=10 and values['selected']['mae']>1.1*values['regional_mean']['mae']+1e-12:regional_fail.append({'scheme':name,'state':state,**values})
    checks={'three_valid_schemes':not invalid and len(ratios)==3,'principal_gain_2pct':ratios.get(SCHEMES[0],np.inf)<=.98,'at_least_two_gains':sum(v<=.98 for v in ratios.values())>=2,
        'mean_ratio_098':len(ratios)==3 and np.mean(list(ratios.values()))<=.98,'none_above_105':len(ratios)==3 and max(ratios.values())<=1.05,'regional_protection':not regional_fail,'verification':bool(verified)}
    return {'promote':all(checks.values()),'checks':{k:bool(v) for k,v in checks.items()},'ratios':ratios,'mean_ratio':float(np.mean(list(ratios.values()))) if len(ratios)==3 else None,'invalid':invalid,'regional_failures':regional_fail}

def serial(s):
    return {**m._serial_selection(s),'training_indices':s.get('training_indices',[])}

def interval_report(frame):
    valid=np.isfinite(frame.interval_low)&np.isfinite(frame.interval_high)
    return {'n':len(frame),'valid_n':int(valid.sum()),'coverage':float(((frame[TARGET]>=frame.interval_low)&(frame[TARGET]<=frame.interval_high))[valid].mean()) if valid.any() else None,'mean_width':float((frame.interval_high-frame.interval_low)[valid].mean()) if valid.any() else None}

def evaluate(name,master,tables,external,location,groups,indices):
    target=master[TARGET].to_numpy();states=master.Estado.to_numpy();preds={k:np.full(len(master),np.nan) for k in ['selected','official','global_mean','regional_mean','gpr','catboost']};lo=preds['selected'].copy();hi=lo.copy();records=[];features=[]
    for group in sorted(np.unique(groups[indices])):
        tr=indices[groups[indices]!=group];va=indices[groups[indices]==group]
        print(f'{name} fold {group}: train={len(tr)}, validación={len(va)}',flush=True)
        official=m.select(tr,target,groups,states,tables,external,location,False)
        selected=m.select(tr,target,groups,states,tables,external,location,True,base_scores=official['_raw_scores']) if external else official
        for route,s in [('official',official),('selected',selected)]:
            model=m.fit_selection(s,tr,target,tables,external,location);preds[route][va]=m.predict_selection(model,s,va,tables,external,location)
            if route=='selected':features.extend({'scheme':name,'fold':int(group),'component':j,'feature':c} for j,component in enumerate(model.models) for c in m.component_columns(component))
        for key,p in m.baseline_predictions(target[tr],states[tr],states[va]).items():
            if key in preds:preds[key][va]=p
        for family in ['gpr','catboost']:
            best=m.pick_score([s for s in official['_raw_scores'] if s['candidate'].family==family]);s={'candidates':[best['candidate']],'weights':np.ones(1)}
            model=m.fit_selection(s,tr,target,tables,external,location);preds[family][va]=m.predict_selection(model,s,va,tables,external,location)
        cal=m.calibrate(tr,target,groups,states,tables,external,location)
        if cal:
            center=m.predict_selection(cal['model'],cal['selection'],va,tables,external,location);lo[va]=center-cal['radius'];hi[va]=center+cal['radius']
        records.append({'fold':int(group),'train':len(tr),'validation':len(va),'selection':serial(selected),'official_selection':serial(official),'metrics':m.metric(target[va],preds['selected'][va]),'calibration_n':cal['calibration_n'] if cal else 0,'calibration_indices':cal['calibration_ids'] if cal else []})
        write_json(ARTIFACTS/f'progress-{name}.json',{'completed':len(records),'total':len(np.unique(groups[indices]))})
    frame=master.loc[indices,[ID,'Estado','Municipio','AREA_HA',TARGET]].copy();frame['spatial_group']=groups[indices]
    for key,p in preds.items():frame[key]=p[indices]
    frame['interval_low']=lo[indices];frame['interval_high']=hi[indices]
    assert len(frame)==138 and frame[ID].is_unique and np.isfinite(frame[list(preds)]).all().all()
    frame.to_csv(ARTIFACTS/f'oof-{name}.csv',index=False)
    by_state={s:{'n':len(d),**{k:m.metric(d[TARGET],d[k]) for k in ['selected','official','regional_mean']}} for s,d in frame.groupby('Estado')}
    area=pd.qcut(frame.AREA_HA,3,labels=['pequeña','mediana','grande']);by_area={str(b):{k:m.metric(d[TARGET],d[k]) for k in ['selected','official','regional_mean']} for b,d in frame.groupby(area,observed=True)}
    report={'valid':True,'data_hash':sha256(PROCESSED/'parcels.parquet'),'metrics':{k:m.metric(frame[TARGET],frame[k]) for k in preds},'by_state':by_state,'by_area':by_area,'folds':records,'interval':{'nominal':.9,**interval_report(frame),'by_state':{s:interval_report(d) for s,d in frame.groupby('Estado')}}}
    write_json(ARTIFACTS/f'validation-{name}.json',report);pd.DataFrame(features).to_csv(ARTIFACTS/f'selected-features-{name}.csv',index=False);diagnostics(frame,name)
    paired=frame[[ID,'Estado','spatial_group',TARGET,'selected','official','regional_mean']].copy()
    for k in ['selected','official']:paired[f'{k}_squared_error_delta']=(paired[k]-paired[TARGET])**2-(paired.regional_mean-paired[TARGET])**2
    paired.to_csv(ARTIFACTS/f'paired-{name}.csv',index=False)
    return report

def stress(master,tables,external,location,groups,indices):
    y=master[TARGET].to_numpy();states=master.Estado.to_numpy();results=[]
    pts=master.to_crs(32614).geometry.representative_point();xy=np.column_stack([pts.x,pts.y])
    scenarios=[]
    for state in sorted(np.unique(states[indices])):
        tr=indices[states[indices]!=state];va=indices[states[indices]==state];assert not (states[tr]==state).any()
        scenarios.append(('leave-one-state-out',state,tr,va,None))
    for group in np.unique(groups[indices]):
        tr=indices[groups[indices]!=group];va=indices[groups[indices]==group]
        # Minimum polygon-to-polygon distance in meters, not centroid proxy.
        projected=master.to_crs(32614);union=projected.iloc[va].geometry.union_all();distance=projected.iloc[tr].geometry.distance(union).to_numpy()
        kept=tr[distance>=1000];minimum=float(distance[distance>=1000].min()) if len(kept) else None
        scenarios.append(('buffer_1000m',int(group),kept,va,minimum))
    for kind,key,tr,va,min_distance in scenarios:
        print('Sensibilidad',kind,key,len(tr),flush=True)
        row={'kind':kind,'held_out':key,'train_n':len(tr),'validation_n':len(va),'train_ids':master.iloc[tr][ID].tolist(),'validation_ids':master.iloc[va][ID].tolist(),'minimum_polygon_distance_m':min_distance}
        if len(tr)<80 or len(np.unique(groups[tr]))<2:
            row.update(status='no viable',reason='train <80 o menos de dos grupos disponibles')
        else:
            s=m.select(tr,y,groups,states,tables,external,location,False);model=m.fit_selection(s,tr,y,tables,external,location);p=m.predict_selection(model,s,va,tables,external,location)
            row.update(status='evaluado',metrics=m.metric(y[va],p),selection=serial(s),route='official congelada')
        results.append(row)
    write_json(ARTIFACTS/'stress.json',results);return results

def save_bundle(name,selection,model,interval,tables,external,location,receipt):
    required=selection['candidates']+(interval['selection']['candidates'] if interval else [])
    tables_contract={}
    for j,c in enumerate(required):
        key=f'{c.features}__component_{j}'
        tables_contract[key]={'base_key':c.features,'columns':list(m.table_for(c,tables,external,location).columns),'hash':sha256(PROCESSED/f'features_{c.features}.parquet'),'sources':list(c.sources),'geo':c.geo,'family':c.family,'kind':c.kind,'alpha':c.alpha,'state_field':'Estado'}
    sources=sorted({s for c in required for s in c.sources})
    contract={'dataset_hash':sha256(PROCESSED/'source-manifest.json'),'parcels_hash':sha256(PROCESSED/'parcels.parquet'),'code_hash':code_hash(),'dependencies':dependencies(),'cutoff':CUTOFF,'seed':SEED,
        'selection':serial(selection),'tables':tables_contract,'sources':sources,'prediction_sources':sorted({s for c in selection['candidates'] for s in c.sources}),
        'external_hashes':{s:sha256(PROCESSED/f'external_{s}.parquet') for s in sources},'run_id':WORKSPACE['run_id'],'policy_hash':receipt['policy_hash'],'scheme_hash':receipt['scheme_hash'],'scheme':'principal-5','component_statistics':[m.component_statistics(component) for component in model.models]}
    joblib.dump({'model':model,'selection':selection,'contract':contract,'interval':interval},ARTIFACTS/f'model_{name}.joblib')
    contract['model_hash']=sha256(ARTIFACTS/f'model_{name}.joblib');write_json(ARTIFACTS/f'contract_{name}.json',contract)

def run(official_only=False):
    started=time.perf_counter();receipt=freeze();master=gpd.read_parquet(PROCESSED/'parcels.parquet');validate_population(master)
    if not all(v['valid'] for v in receipt['validity'].values()):
        write_json(ARTIFACTS/'promotion.json',promotion({},False));raise ValueError('Esquema no viable: promoción bloqueada')
    historic=pd.read_csv(Path(WORKSPACE['snapshot'])/'artifacts/oof.csv');audit_originals(diagnostics(historic,'historic'))
    tables,external,location=m.load_tables(master);tables={k:tables[k] for k in ['monthly_20_10','whittaker_20_10']}
    if official_only:external={}
    y=master[TARGET].to_numpy();states=master.Estado.to_numpy();indices=np.flatnonzero(master[TARGET].notna());hidden=np.flatnonzero(master[TARGET].isna());assignments=pd.read_csv(ARTIFACTS/'schemes.csv');reports={};group_sets={}
    with threadpool_limits(limits=2):
        for name in SCHEMES:
            groups=np.full(len(master),-1);groups[indices]=assignments[assignments.scheme.eq(name)].set_index(ID).reindex(master.iloc[indices][ID]).fold.to_numpy();group_sets[name]=groups
            reports[name]=evaluate(name,master,tables,external,location,groups,indices)
        decision=promotion(reports,False);write_json(ARTIFACTS/'promotion.json',decision)
        stress_results=stress(master,tables,external,location,group_sets[SCHEMES[0]],indices)
        groups=group_sets[SCHEMES[0]];official=m.select(indices,y,groups,states,tables,external,location,False)
        selected=m.select(indices,y,groups,states,tables,external,location,True,base_scores=official['_raw_scores']) if external else official
        cal=m.calibrate(indices,y,groups,states,tables,external,location)
        primary=reports[SCHEMES[0]];interval=primary['interval'];ok=bool(interval['valid_n']==138 and interval['coverage']>=.85 and cal and cal['calibration_n']>=25)
        interval.update(available=ok,calibration_min=25,limitation='Cobertura empírica de desarrollo; sin garantía por estado ni campaña futura')
        for name,s in [('selected',selected),('official',official)]:
            model=m.fit_selection(s,indices,y,tables,external,location);save_bundle(name,s,model,cal if name=='selected' and ok else None,tables,external,location,receipt)
            prediction=m.predict_selection(model,s,hidden,tables,external,location)
            if not np.isfinite(prediction).all() or (prediction<0).any():raise ValueError('Exportación bloqueada: predicción inválida, sin cotas artificiales')
            export=pd.DataFrame({ID:master.iloc[hidden][ID].to_numpy(),TARGET:prediction}).sort_values(ID);assert len(export)==59 and export[ID].is_unique
            export.to_csv(ARTIFACTS/('predictions_59.csv' if name=='selected' else 'predictions_official_only_59.csv'),index=False)
        compatibility={**primary,'by_state':{s:v['selected'] for s,v in primary['by_state'].items()},'final_selection':serial(selected),'interval':interval,'regional_stress':[{'held_out_state':r['held_out'],'n':r['validation_n'],**r['metrics']} for r in stress_results if r['kind']=='leave-one-state-out' and r['status']=='evaluado'],'buffer_sensitivity':[r for r in stress_results if r['kind']=='buffer_1000m'],'seconds':time.perf_counter()-started}
        write_json(ARTIFACTS/'validation.json',compatibility)
    pd.read_csv(ARTIFACTS/f'oof-{SCHEMES[0]}.csv').to_csv(ARTIFACTS/'oof.csv',index=False)
    pd.read_csv(ARTIFACTS/f'selected-features-{SCHEMES[0]}.csv').to_csv(ARTIFACTS/'selected-features.csv',index=False)
    history=historic.set_index(ID);current=pd.read_csv(ARTIFACTS/'oof.csv').set_index(ID);assert current.index.equals(history.index)
    assert np.array_equal(current.spatial_group,history.spatial_group) and np.array_equal(current[TARGET],history[TARGET])
    current['previous_selected']=history.selected;current['previous_squared_error_delta']=(current.selected-current[TARGET])**2-(history.selected-history[TARGET])**2;current.to_csv(ARTIFACTS/'historical-paired-primary.csv')
    frequencies=Counter();source_frequency=Counter()
    for scheme,report in reports.items():
        for fold in report['folds']:
            for c in fold['selection']['candidates']:frequencies[(scheme,c['family'],c['kind'],c['alpha'])]+=1
            for d in fold['selection']['decisions']:
                if 'source' in d:source_frequency[(scheme,d['source'],d['family'],d['admitted'])]+=1
    pd.DataFrame([dict(zip(['scheme','family','kind','alpha'],k),count=v) for k,v in frequencies.items()]).to_csv(ARTIFACTS/'selection-frequencies.csv',index=False)
    pd.DataFrame([dict(zip(['scheme','source','family','admitted'],k),count=v) for k,v in source_frequency.items()]).to_csv(ARTIFACTS/'source-frequencies.csv',index=False)
    write_json(ARTIFACTS/'phase-comparison.json',{'previous_primary':m.metric(history[TARGET],history.selected),'schemes':{k:v['metrics'] for k,v in reports.items()},'decision':decision,'data_hash':receipt['data_hash'],'policy_hash':receipt['policy_hash'],'seconds':time.perf_counter()-started,'limitation':policy()['limitation']})
    active_intact();print('Fase evaluada:',decision,flush=True)
