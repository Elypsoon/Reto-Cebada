"""Recupera exclusivamente los dos contextos E07-v3 originales en copias nuevas."""
import argparse
import json
import os
import shutil
from pathlib import Path
from agrocebada.common import ROOT,sha256
from original_environment import supervise
from agrocebada.tracking import atomic_json,manifest,check_manifest

AUDIT=ROOT/'registry/historic-recovery'
SUPPORT=ROOT.parents[1]/'experiments/soporte-regional-20261003'

def prepare():
    source=SUPPORT/'optional/adapter-v3';target=AUDIT/'optional-copy'
    target.mkdir(exist_ok=False)
    hashes={}
    for folder in ['src','data/processed','optional/tabpfn-2.5','registry']:
        for name,digest in manifest(source/folder).items():
            path=folder+'/'+name;dest=target/path;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source/path,dest)
            hashes[path]={'source':str(source/path),'sha256':digest}
    contexts=[]
    for case in json.loads((AUDIT/'plan.json').read_text(encoding='utf-8'))['optional_contexts']:
        src=Path(case['context']);dest=target/'runs'/case['run_id']/'artifacts';dest.mkdir(parents=True)
        for name in ['training-context.npz','context-contract.json','predictions_official_only_59.csv']:
            shutil.copy2(src/name,dest/name)
            hashes[(dest/name).relative_to(target).as_posix()]={'source':str(src/name),'sha256':sha256(src/name)}
        key=json.loads(Path(case['protocol']).read_text(encoding='utf-8'))['optional_config']
        contexts.append({'run_id':case['run_id'],'key':key,'destination':str(dest)})
    atomic_json(AUDIT/'optional-plan.json',{'root':str(target),'contexts':contexts,'input_manifest':hashes,
                'python':str(SUPPORT/'optional/tabpfn-2.5/env/Scripts/python.exe')})
    print('Contextos opcionales históricos preparados',len(contexts),flush=True)

def run():
    plan=json.loads((AUDIT/'optional-plan.json').read_text(encoding='utf-8'));root=Path(plan['root'])
    if any(sha256(root/n)!=r['sha256'] or sha256(r['source'])!=r['sha256'] for n,r in plan['input_manifest'].items()):
        raise ValueError('Contexto/código/pesos históricos alterados')
    results=[]
    for context in plan['contexts']:
        env={**os.environ,'PYTHONPATH':str(root/'src'),'AGROCEBADA_ARTIFACTS':context['destination'],
             'TABPFN_DISABLE_TELEMETRY':'1','TABPFN_MODEL_CACHE_DIR':str(root/'optional/tabpfn-2.5')}
        receipt=supervise([plan['python'],'-m','agrocebada.optional','verify',context['key'],context['destination']],root,env,
                         AUDIT/f'resources-original-env-{context["run_id"]}.json',seconds=1800,log=AUDIT/f'original-env-{context["run_id"]}.log')
        if receipt['exit_code']!=0:raise ValueError('Recuperación opcional histórica fallida: '+context['run_id'])
        result=json.loads((Path(context['destination'])/'fresh-process-check.json').read_text(encoding='utf-8'))
        results.append({'run_id':context['run_id'],**result})
        atomic_json(AUDIT/'optional-summary.json',{'passed':True,'contexts':results,'new_external_fits':False})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);args=parser.parse_args()
    if args.action=='prepare':prepare()
    else:run()
