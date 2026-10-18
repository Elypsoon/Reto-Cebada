"""Relaciona estados reales con evidencia congelada; análisis sin entrenamiento."""
import json
import re
from pathlib import Path
import pandas as pd
from agrocebada.common import ROOT,ID,TARGET,sha256
from agrocebada.tracking import atomic_json,compare_frames
from agrocebada.priority_validation import SCHEMES
from agrocebada.priority_run import diagnostics

evidence=json.loads((ROOT/'registry/evidence.json').read_text(encoding='utf-8'))
states=json.loads((ROOT/'registry/priority-summary.json').read_text(encoding='utf-8'))
records=[]
for hypothesis in evidence['hypotheses']:
    runs=[s for s in states if s['block']==hypothesis['id']]
    records.append({**hypothesis,'status':'completed' if runs and all(s['predictively_tested'] for s in runs) else 'closed_incomplete' if runs and all(s['administratively_closed'] for s in runs) else 'pending_or_running',
                    'run_ids':[s['run_id'] for s in runs],'metrics':{s['run_id']:s['metrics'] for s in runs},
                    'verified_runs':sum(s['predictively_tested'] for s in runs),'registered_runs':len(runs),
                    'runs':[{'id':s['run_id'],'status':s['status'],'reason':s.get('reason'),'metrics':s['metrics'],
                             'protocol_hash':s['protocol_hash'],'predictively_tested':s['predictively_tested']} for s in runs]})
atomic_json(ROOT/'registry/coverage-final.json',{'hypotheses':records,'sources':evidence['sources'],'deferred':evidence['deferred'],
            'frozen_evidence_hash':sha256(ROOT/'registry/evidence.json'),'development_evidence_only':True})
lines=['# Evidencia y cobertura prioritaria','',
       'Los estados y métricas proceden de ejecuciones registradas y verificadas; un fallo u omisión no cuenta como prueba completada.',
       '', 'Las 138 etiquetas siguen siendo evidencia de desarrollo de una única campaña.','',
       '| Comparación | Estado | Ejecuciones verificadas | Evidencia | Hipótesis y control |',
       '| --- | --- | --- | --- | --- |']
lines += [f"| {r['id']} | {r['status']} | {r['verified_runs']}/{r['registered_runs']} | {', '.join(r['evidence_ids'])} | {r['hypothesis_and_control']} |" for r in records]
lines += ['','Las métricas completas, decisiones y motivos están en priority-results.md y coverage-final.json. Los contrastes de mecanismos permanecen descriptivos.','',
          '## Fuentes','']
for source in evidence['sources']:
    title=source['title_and_source']
    for entry in source['sources']:
        if 'path' in entry:
            pattern=r'\['+re.escape(entry['title'])+r'\]\([^)]+\)'
            title=re.sub(pattern,lambda match:f"[{entry['title']}](<{Path(entry['path']).as_posix()}>)",title)
    lines.append('- '+source['id']+': '+title+'. '+source['reading_scope_and_limitation'])
lines += ['','La lectura bibliográfica se registró antes de la preparación. Los checkpoints y dependencias fundacionales se verificaron después en optional/*/preflight.json; sus hashes y pruebas están incluidos en la versión congelada.','',
          '## Alternativas diferidas','']
lines += [f"- {r['name']}: {r['reason']} No evaluada en esta fase." for r in evidence['deferred']]
(ROOT/'docs/evidence-and-coverage.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
support=ROOT.parents[1]/'experiments/soporte-regional-20261003'
optional_comparison={}
for state in states:
    if state['block'] not in ['P07','P08'] or not state['predictively_tested']:continue
    protocol=json.loads((ROOT/'runs'/state['run_id']/'protocol.json').read_text(encoding='utf-8'))
    key=protocol['table'];art=ROOT/'runs'/state['run_id']/'artifacts';optional_comparison[state['run_id']]={}
    for scheme in SCHEMES:
        frame=pd.read_csv(art/f'oof-{scheme}.csv',float_precision='round_trip')
        previous=pd.read_csv(support/'runs'/('E07-v3-'+key)/'artifacts'/f'oof-{scheme}.csv',float_precision='round_trip')
        paired=compare_frames(frame,previous,'official')
        paired.to_csv(ROOT/'docs'/f'paired-TabPFN25-{state["run_id"]}-{scheme}.csv',index=False,float_format='%.17g')
        a,b=diagnostics(frame.set_index(ID)),diagnostics(previous.set_index(ID))
        optional_comparison[state['run_id']][scheme]={'candidate':a,'TabPFN25_historical':b,
                'delta_rmse':a['metrics']['rmse']-b['metrics']['rmse'],'historical_oof_hash':sha256(support/'runs'/('E07-v3-'+key)/'artifacts'/f'oof-{scheme}.csv'),
                'interpretation':'Comparación exploratoria, sin selección externa ni entrada a P06'}
atomic_json(ROOT/'docs/optional-vs-TabPFN25.json',optional_comparison)
print('Cobertura y evidencia actualizadas',len(records),flush=True)
