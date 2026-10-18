"""Auditoría de solo inferencia de versiones históricas; no cambia sus protocolos."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PHASE=Path(__file__).resolve().parents[2]
PROJECT=PHASE.parents[1]
AUDIT=PHASE/'registry/historic-recovery'


def prepare():
    from agrocebada.common import sha256
    from agrocebada.tracking import atomic_json
    cases=[('activa',PROJECT,PROJECT,PROJECT/'artifacts'),
           ('regional',PROJECT/'experiments/regional-20261003',PROJECT/'experiments/regional-20261003',PROJECT/'experiments/regional-20261003/artifacts')]
    support=PROJECT/'experiments/soporte-regional-20261003'
    optional=[]
    for folder in sorted((support/'runs').iterdir()):
        state_path=folder/'run.json'
        if not state_path.exists():continue
        state=json.loads(state_path.read_text(encoding='utf-8'))
        if state['status']!='completed':continue
        if (folder/'artifacts/model_official.joblib').exists():
            protocol=json.loads((folder/'protocol.json').read_text(encoding='utf-8'))
            cases.append((folder.name,support/'versions'/protocol['code_hash'],support,folder/'artifacts'))
        elif (folder/'artifacts/training-context.npz').exists():
            optional.append({'run_id':folder.name,'context':str(folder/'artifacts'),
                             'protocol':str(folder/'protocol.json'),'needs_context_recovery':True})
    records=[]
    for name,code_source,data_source,art_source in cases:
        target=AUDIT/'copies'/name
        if target.exists():raise ValueError('Copia histórica ya preparada')
        target.mkdir(parents=True)
        hashes={}
        paths=list((code_source/'src/agrocebada').glob('*.py'))
        paths += [p for p in (data_source/'data/processed').glob('*') if p.is_file()]
        paths += [p for p in (data_source/'data/external').glob('*') if p.is_file()]
        for source in paths:
            relative=source.relative_to(code_source) if source.is_relative_to(code_source/'src') else source.relative_to(data_source)
            dest=target/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
            hashes[relative.as_posix()]={'source':str(source),'sha256':sha256(source)}
        for source in art_source.iterdir():
            if source.is_file() and (source.name.startswith(('model_','contract_','predictions')) or source.name in ['selection-policy.json','schemes.csv']):
                dest=target/'artifacts'/source.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(source,dest)
                hashes['artifacts/'+source.name]={'source':str(source),'sha256':sha256(source)}
        if (data_source/'workspace.json').exists():shutil.copy2(data_source/'workspace.json',target/'workspace.json')
        records.append({'case':name,'root':str(target),'input_manifest':hashes,'artifact_source':str(art_source)})
    atomic_json(AUDIT/'plan.json',{'inference_cases':records,'optional_contexts':optional,'new_training':False})
    print('Copias históricas preparadas:',len(records),'contextos:',len(optional),flush=True)


def worker(case):
    import numpy as np
    import pandas as pd
    from agrocebada.inference import Predictor,official_export
    from agrocebada.common import ARTIFACTS,ROOT,ID,TARGET,code_hash,sha256
    output={}
    for route in ['official','selected']:
        model=Predictor(route);generated=official_export(model)
        filename='predictions_59.csv' if route=='selected' else 'predictions_official_only_59.csv'
        saved=pd.read_csv(ARTIFACTS/filename,float_precision='round_trip')
        if not generated[ID].equals(saved[ID]):raise ValueError('IDs históricos no recuperados')
        np.testing.assert_allclose(generated[TARGET],saved[TARGET],atol=1e-10,rtol=0)
        output[route]={'n':59,'passed':True,'model_hash':sha256(ARTIFACTS/f'model_{route}.joblib'),'no_refit':True}
    (AUDIT/f'result-{case}.json').write_text(json.dumps({'case':case,'passed':True,'routes':output,'code_hash':code_hash(),'offline':True}),encoding='utf-8')
    print(case,'59 consultas históricas por ruta reproducidas',flush=True)


def run():
    from agrocebada.priority_resources import supervise
    from agrocebada.common import sha256
    from agrocebada.tracking import atomic_json
    plan=json.loads((AUDIT/'plan.json').read_text(encoding='utf-8'))
    results=[]
    for case in plan['inference_cases']:
        root=Path(case['root'])
        if any(sha256(root/name)!=r['sha256'] or sha256(r['source'])!=r['sha256'] for name,r in case['input_manifest'].items()):
            raise ValueError('Copia o fuente histórica alterada')
        env={**os.environ,'PYTHONPATH':str(root/'src'),'AGROCEBADA_ARTIFACTS':str(root/'artifacts')}
        receipt=supervise([sys.executable,str(Path(__file__).resolve()),'worker',case['case']],root,env,
                         AUDIT/f'resources-{case["case"]}.json',seconds=300,log=AUDIT/f'{case["case"]}.log')
        if receipt['exit_code']!=0:raise ValueError('Recuperación histórica fallida: '+case['case'])
        results.append(json.loads((AUDIT/f'result-{case["case"]}.json').read_text(encoding='utf-8')))
        atomic_json(AUDIT/'summary.json',{'passed':True,'cases':results,'optional_contexts_pending':plan['optional_contexts']})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','worker','run']);parser.add_argument('case',nargs='?');args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='worker':worker(args.case)
    else:run()
