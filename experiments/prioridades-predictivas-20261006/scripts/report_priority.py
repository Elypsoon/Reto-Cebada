"""Cierre y cobertura a partir de artefactos reales; nunca activa un modelo."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from agrocebada.common import ROOT,ID,TARGET,sha256
from agrocebada.tracking import atomic_json,check_manifest,compare_frames
from agrocebada.priority_registry import PriorityRegistry,TERMINAL
from agrocebada.priority_run import diagnostics
from agrocebada.priority_validation import evaluate_eligibility,SCHEMES

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def report(final=False):
    registry=PriorityRegistry();registry.publish();states=read(ROOT/'registry/priority-summary.json')
    frozen=read(ROOT/'registry/frozen-priority.json')
    source=read(ROOT/'registry/source-integrity.json')
    intact={name:Path(record['source']).is_file() and sha256(record['source'])==record['sha256'] for name,record in source.items()}
    atomic_json(ROOT/'registry/closing-integrity.json',{'protected_files':len(intact),'all_intact':all(intact.values()),
        'checks':intact,'frozen_snapshot_intact':check_manifest(ROOT/'versions'/frozen['version'],read(ROOT/'versions'/frozen['version']/'manifest.json'))})
    byid={s['run_id']:s for s in states};active=byid.get('P00-C-activa',{})
    controls_ok=all(byid.get('P00-'+name,{}).get('predictively_tested') for name in ['C-activa','C-soporte'])
    frames={};actives={}
    if byid.get('P06',{}).get('predictively_tested'):
        frames={s:pd.read_csv(ROOT/'runs/P06/artifacts'/f'oof-{s}.csv',float_precision='round_trip') for s in SCHEMES}
    if active.get('predictively_tested'):
        actives={s:pd.read_csv(ROOT/'runs/P00-C-activa/artifacts'/f'oof-{s}.csv',float_precision='round_trip') for s in SCHEMES}
    decision=evaluate_eligibility('P06',frames,actives,byid.get('P06',{}).get('verified',False),controls_ok)
    atomic_json(ROOT/'registry/P06-eligibility.json',decision)
    lines=['# Evaluación de prioridades predictivas','',
           'Evidencia de desarrollo sobre las mismas 138 etiquetas de abril–octubre de 2025. No es una validación de otra campaña.',
           '',f"Versión congelada: `{frozen['version']}`.",'',
           '| Ejecución | Estado | Predicción externa verificada | Motivo |','| --- | --- | --- | --- |']
    lines += [f"| {s['run_id']} | {s['status']} | {s['predictively_tested']} | {s.get('reason') or '—'} |" for s in states]
    lines+=['','| Ejecución | Ruta | Esquema | RMSE (t/ha) | MAE | Sesgo | Δ RMSE activa oficial |',
            '| --- | --- | --- | --- | --- | --- | --- |']
    detailed={}
    for state in states:
        if not state['predictively_tested']:continue
        run_id=state['run_id'];art=ROOT/'runs'/run_id/'artifacts';detailed[run_id]={}
        for path in sorted(art.glob('oof-*.csv')):
            scheme=path.stem.removeprefix('oof-');frame=pd.read_csv(path,float_precision='round_trip')
            routes=['official','selected'] if run_id.startswith('P00') else ['official']
            detailed[run_id][scheme]={}
            for route in routes:
                d=diagnostics(frame.set_index(ID),route);detailed[run_id][scheme][route]=d
                delta=None
                if scheme in actives:
                    a=actives[scheme].copy();c=frame.copy();c['official']=c[route]
                    compare_frames(c,a,'official').to_csv(ROOT/'docs'/f'paired-active-{run_id}-{route}-{scheme}.csv',index=False,float_format='%.17g')
                    delta=d['metrics']['rmse']-diagnostics(a.set_index(ID))['metrics']['rmse']
                if controls_ok and scheme in SCHEMES:
                    control=pd.read_csv(ROOT/'runs/P00-C-soporte/artifacts'/f'oof-{scheme}.csv',float_precision='round_trip')
                    candidate=frame.copy();candidate['official']=candidate[route]
                    compare_frames(candidate,control,'official').to_csv(ROOT/'docs'/f'paired-support-{run_id}-{route}-{scheme}.csv',index=False,float_format='%.17g')
                z=d['metrics'];lines.append(f"| {run_id} | {route} | {scheme} | {z['rmse']:.6f} | {z['mae']:.6f} | {z['bias']:.6f} | {f'{delta:+.6f}' if delta is not None else '—'} |")
    atomic_json(ROOT/'docs/detailed-results.json',detailed)
    lines+=['','Elegibilidad P06: '+str(decision['eligible'])+'. Activación, despliegue y envío: false.','',
            'Comprobaciones: '+str(decision['checks']), '','Fallos de protección estatal: '+str(decision['state_failures']),
            '', 'Las configuraciones individuales conservan OOF y resultados en cada ejecución; ninguna sustituye retrospectivamente la selección interna.',
            '', 'Las referencias agronómicas y la bibliografía motivan hipótesis, sin demostrar ganancias locales. Véase la matriz de evidencia y cobertura.','',
            'BART, TabM, NGBoost, radar, ERA5, SoilGrids, AlphaEarth y simulación completa de cultivo siguen diferidos. No se afirma haber probado todas las posibilidades.',
            '', 'Un fallo, interrupción u omisión cierra su incidencia, pero no certifica evaluación predictiva completa.']
    (ROOT/'docs/priority-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    mandatory=[s for s in states if s['block'] not in ['P07','P08']]
    closure={'administratively_closed':all(s['status'] in TERMINAL for s in states),
             'mandatory_predictive_coverage_complete':all(s['predictively_tested'] for s in mandatory),
             'optional_verified':sum(s['predictively_tested'] for s in states if s['block'] in ['P07','P08']),
             'eligible_P06':decision['eligible'],'activated':False,'deployed':False,'sent':False,
             'all_protected_sources_intact':all(intact.values()),'final_requested':final}
    atomic_json(ROOT/'registry/closure.json',closure)
    if final and (not closure['administratively_closed'] or not all(intact.values())):
        raise ValueError('Cierre incompleto o integridad fallida; no se flexibiliza')
    print(closure,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');args=parser.parse_args();report(args.final)
