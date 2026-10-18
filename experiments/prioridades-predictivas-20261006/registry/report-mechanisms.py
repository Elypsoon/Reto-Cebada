"""Comparaciones descriptivas de configuraciones ya congeladas, sin seleccionar modelos."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from agrocebada.common import ROOT,ID,TARGET
from agrocebada.modeling import metric
from agrocebada.tracking import atomic_json
from agrocebada.priority_catalog import candidates
from agrocebada.priority_validation import SCHEMES


def comparisons(block):
    grid=[c for c in candidates(block) if not c.family.endswith('_mean')]
    pairs=[]
    def same(a,b,excluded):
        x,y=a.__dict__,b.__dict__
        return all(x[k]==y[k] for k in x if k not in excluded)
    for a in grid:
        for b in grid:
            label=None
            if block=='P01' and a.selector=='rank' and b.selector in ['agronomic','all'] and same(a,b,{'selector'}):
                label='Selector '+b.selector+' frente a rank'
            if block=='P02' and a.representation=='calendar_nasa' and b.representation=='thermal' and same(a,b,{'representation'}):
                label='Tiempo térmico frente a calendario; contexto NASA idéntico'
            if block=='P03' and same(a,b,{'state_setting'}):
                if a.family=='hierarchical_ridge' and a.state_setting=='infinite' and b.state_setting!='infinite':label='Ridge con efecto estatal frente a sin efecto estatal'
                if a.family=='hierarchical_gpr' and a.state_setting==0 and b.state_setting!=0:label='GPR con covarianza estatal frente a tau²=0'
            if block=='P04':
                if a.family=='ebm' and a.interactions=='none' and b.interactions=='fixed_pairs' and same(a,b,{'interactions'}):label='EBM con dos interacciones frente a aditivo'
                if a.family=='gam' and a.knots==3 and b.knots==4 and same(a,b,{'knots'}):label='GAM con cuatro nudos frente a tres'
            if block=='P05' and a.representation=='calendar' and b.representation=='functional' and same(a,b,{'representation','components'}):
                label='Proyección funcional frente a resúmenes calendarizados'
            if block=='P06' and a.representation=='compact' and b.representation=='functional' and same(a,b,{'representation','components'}):
                label='Representación funcional frente a compacta; diagnóstico fijo de P06'
            if label:pairs.append((label,a,b))
    return pairs


rows=[];paired_rows=[];individual_best={}
for block in ['P01','P02','P03','P04','P05','P06']:
    folder=ROOT/'runs'/block/'artifacts'
    if not (folder/'fresh-process-check.json').exists():continue
    individual_best[block]={}
    for scheme in SCHEMES:
        frame=pd.read_csv(folder/f'oof-{scheme}.csv',float_precision='round_trip').set_index(ID)
        values=pd.read_csv(folder/f'individual-oof-{scheme}.csv',float_precision='round_trip').set_index(ID)
        info=json.loads((folder/f'individual-{scheme}.json').read_text(encoding='utf-8'))
        complete=[(key,record) for key,record in info['candidates'].items() if record['complete']]
        key,record=min(complete,key=lambda pair:pair[1]['metrics']['rmse'])
        individual_best[block][scheme]={'id':key,**record,'interpretation':'Mínimo descriptivo observado; no sustituye selección ni receta P06'}
        for label,a,b in comparisons(block):
            p,q=values[a.id],values[b.id]
            complete=bool(np.isfinite(p).all() and np.isfinite(q).all())
            row={'block':block,'scheme':scheme,'comparison':label,'control_id':a.id,'candidate_id':b.id,
                 'complete':complete,'control':a.__dict__,'candidate':b.__dict__,'n':138}
            if complete:
                x,y=metric(frame[TARGET],p),metric(frame[TARGET],q)
                row.update(control_rmse=x['rmse'],candidate_rmse=y['rmse'],delta_rmse=y['rmse']-x['rmse'],
                           delta_mae=y['mae']-x['mae'],by_state={s:{'control':metric(part[TARGET],p.loc[part.index]),
                            'candidate':metric(part[TARGET],q.loc[part.index])} for s,part in frame.groupby('Estado')})
                for pid in frame.index:
                    paired_rows.append({'block':block,'scheme':scheme,'control_id':a.id,'candidate_id':b.id,ID:pid,
                            'state':frame.loc[pid,'Estado'],'target':frame.loc[pid,TARGET],
                            'control':p.loc[pid],'candidate':q.loc[pid],
                            'squared_error_delta':(q.loc[pid]-frame.loc[pid,TARGET])**2-(p.loc[pid]-frame.loc[pid,TARGET])**2})
            else:row['reason']='Algún fold inviable; no se promedia omitiéndolo'
            rows.append(row)
atomic_json(ROOT/'docs/mechanism-comparisons.json',{'comparisons':rows,'individual_minimums':individual_best,
            'selection_changed':False,'P06_changed':False,'development_evidence_only':True})
pd.DataFrame(paired_rows).to_csv(ROOT/'docs/paired-mechanisms.csv',index=False,float_format='%.17g')
lines=['# Contrastes de mecanismos','',
       'Cada par utiliza las mismas 138 etiquetas y configuración, variando únicamente el mecanismo indicado. Los resultados son descriptivos y no eligen ni sustituyen modelos.',
       '', '| Bloque | Esquema | Contraste | Pares completos | Pares con menor RMSE | Mediana Δ RMSE (t/ha) |',
       '| --- | --- | --- | --- | --- | --- |']
df=pd.DataFrame(rows)
if len(df):
    for (block,scheme,label),part in df.groupby(['block','scheme','comparison']):
        usable=part.loc[part.complete]
        lines.append(f"| {block} | {scheme} | {label} | {len(usable)}/{len(part)} | {int(usable.delta_rmse.lt(0).sum())} | {usable.delta_rmse.median():+.6f} |")
lines+=['','Los mínimos individuales observados se publican en mechanism-comparisons.json como diagnósticos. No se ajustan pesos ni se usa OOF externa para reconfigurar P06.',
        '', 'Las diferencias por parcela y por estado están en paired-mechanisms.csv y mechanism-comparisons.json. Una mejora en un par no demuestra estabilidad entre campañas.']
(ROOT/'docs/mechanism-comparisons.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Contrastes descriptivos publicados',len(rows),flush=True)
