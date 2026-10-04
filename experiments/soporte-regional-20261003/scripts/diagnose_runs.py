"""Diagnósticos externos descriptivos; no modifican selección ni elegibilidad."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from agrocebada.tracking import read,atomic_json,check_manifest
from agrocebada import robust as r
catalog=read(root/'registry/catalog.json')
rows={}
for entry in catalog['experiments']:
    folder=root/'runs'/entry['run_id'];state=read(folder/'run.json')
    if state['status']!='completed' or entry['experiment'] in ['E00','E07']:continue
    assert check_manifest(folder/'artifacts',read(folder/'artifact-manifest.json'))
    reports={s:read(folder/f'artifacts/validation-{s}.json') for s in r.SCHEMES};result={}
    for route in read(folder/'protocol.json')['routes']:
        routed={s:{**z,'metrics':{**z['metrics'],'selected':z['metrics'][route]},'by_state':{state:{**stats,'selected':stats[route]} for state,stats in z['by_state'].items()}} for s,z in reports.items()}
        diagnosed=r.promotion(routed,True)
        result[route]={'threshold_diagnostics':diagnosed,'interpretation':'Diagnóstico descriptivo de umbrales sobre las mismas etiquetas; solo E08 recibe elegibilidad y ninguna ejecución se activa','scope':'E08' if entry['experiment']=='E08' else 'exploratorio','activated':False}
    atomic_json(folder/'diagnostic-criteria.json',result);rows[entry['run_id']]=result
atomic_json(root/'registry/diagnostic-criteria.json',rows)
print('Diagnósticos descriptivos publicados:',len(rows),flush=True)
