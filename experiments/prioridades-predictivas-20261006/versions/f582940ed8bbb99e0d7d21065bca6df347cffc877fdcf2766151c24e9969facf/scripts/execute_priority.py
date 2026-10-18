"""Orquestación secuencial con límites compartidos por bloque y verificación."""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path
from agrocebada.common import ROOT,sha256
from agrocebada.priority_registry import PriorityRegistry
from agrocebada.priority_resources import supervise
from agrocebada.tracking import atomic_json,manifest,check_manifest


def execute(run_id):
    registry=PriorityRegistry();protocol=registry.validate(run_id);folder=ROOT/'runs'/run_id;art=folder/'artifacts'
    if registry.state(run_id)['status']!='frozen':raise ValueError('No se reutiliza ID ejecutado')
    snapshot=ROOT/'versions'/protocol['version']
    if not check_manifest(snapshot,protocol['input_manifest']):raise ValueError('Paquete congelado alterado')
    block=protocol['block'];env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'DO_NOT_TRACK':'1','TABPFN_DISABLE_TELEMETRY':'1','PROJ_NETWORK':'OFF'}
    cwd=ROOT;python=ROOT/'.venv/Scripts/python.exe';limit=7200
    if block=='P00':
        name=protocol['control'];cwd=ROOT/'controls'/name;env['PYTHONPATH']=str(cwd/'src')
        command=[str(python),str(ROOT/'scripts/control_worker.py'),'run']
        recovery=[str(python),str(ROOT/'scripts/control_worker.py'),'verify']
        previous=[p for p in (ROOT/'runs').glob('P00-*/artifacts/resources-run.json') if p.parent.parent.name!=run_id]
        limit-=sum(json.loads(p.read_text(encoding='utf-8'))['seconds'] for p in previous)
    elif block in ['P07','P08']:
        if not protocol['preflight'].get('available'):
            registry.transition(run_id,'skipped',protocol['preflight']['reason']);return
        name=protocol['catalog']['model'];python=ROOT/'optional'/name/'env/Scripts/python.exe';limit=1800
        command=[str(python),'-m','agrocebada.priority_optional','run',name,protocol['table'],str(art)]
        recovery=[str(python),'-m','agrocebada.priority_optional','verify',name,str(art)]
    else:
        command=[str(python),'-m','agrocebada.priority_run','run',block,str(art)]
        recovery=[str(python),'-m','agrocebada.priority_run','verify',str(art)]
    registry.transition(run_id,'running')
    print('INICIO',run_id,flush=True)
    try:
        receipt=supervise(command,cwd,env,art/'resources-run.json',seconds=max(0,limit),log=art/'training.log')
        if block=='P00':
            for path in (cwd/'artifacts').iterdir():
                if path.is_file():shutil.copy2(path,art/path.name)
        if receipt['exit_code']!=0:
            registry.transition(run_id,'interrupted' if receipt['reason'] else 'failed',receipt['reason'] or 'Error del proceso; véase training.log')
            print('FALLO',run_id,receipt,flush=True);return
        verified=supervise(recovery,cwd,env,art/'resources-verify.json',seconds=max(0,limit-receipt['seconds']),log=art/'verification.log')
        if block=='P00' and (cwd/'artifacts/fresh-process-check.json').exists():shutil.copy2(cwd/'artifacts/fresh-process-check.json',art/'fresh-process-check.json')
        if verified['exit_code']!=0:
            registry.transition(run_id,'failed','No se reprodujo la inferencia/métricas; véase verification.log');return
        check=json.loads((art/'fresh-process-check.json').read_text(encoding='utf-8'))
        if not check['passed']:raise ValueError('Recuperación negativa')
        metrics=({s:json.loads(p.read_text(encoding='utf-8')) for p in art.glob('metrics-*.json') for s in [p.stem.removeprefix('metrics-')]}
                 if block=='P00' else json.loads((art/'metrics.json').read_text(encoding='utf-8')))
        atomic_json(art/'recovery-package.json',{'snapshot':str(snapshot),'snapshot_manifest_hash':sha256(snapshot/'manifest.json'),
                    'protocol_hash':sha256(folder/'protocol.json'),'shared_immutable_inputs':True,
                    'fitted_objects_or_context':True,'offline_verified':True,'atol':1e-10,'rtol':0})
        registry.transition(run_id,'completed',metrics=metrics,verified=True)
        print('COMPLETADO',run_id,metrics,flush=True)
    except BaseException as error:
        atomic_json(art/'failure.json',{'error':repr(error)})
        if registry.state(run_id)['status']=='running':registry.transition(run_id,'failed',repr(error))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('run_ids',nargs='+');args=parser.parse_args()
    lock=ROOT/'registry/priority-writer.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(fd,str(os.getpid()).encode());os.close(fd)
        for run_id in args.run_ids:
            execute(run_id)
            if run_id.startswith('P00') and PriorityRegistry().state(run_id)['status']!='completed':
                raise ValueError('Control no reproducido; investigar antes de comparaciones nuevas')
    finally:
        lock.unlink()
