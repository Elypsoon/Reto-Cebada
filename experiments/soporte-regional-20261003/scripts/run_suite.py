"""Ejecutor secuencial, conserva logs y no omite fallos del control."""
from pathlib import Path
import os,subprocess,sys,json
root=Path(__file__).resolve().parents[1]
env=dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
if len(sys.argv)==2 and sys.argv[1]=='prepare':
    raise SystemExit(subprocess.run([sys.executable,'-m','agrocebada.phase','prepare'],env=env,cwd=root).returncode)
catalog=json.loads((root/'registry/catalog.json').read_text(encoding='utf-8'))
requested=sys.argv[1:]
for entry in catalog['experiments']:
    rid=entry['run_id']
    if requested and rid not in requested:continue
    state=json.loads((root/'runs'/rid/'run.json').read_text(encoding='utf-8'))
    if state['status'] in ['completed','skipped']:continue
    log=root/'runs'/rid/'execution.log'
    destination=str(root/'runs'/rid/'artifacts')
    with log.open('a',encoding='utf-8') as output:
        result=subprocess.run([sys.executable,'-m','agrocebada.phase','run','--run-id',rid],env=dict(env,AGROCEBADA_ARTIFACTS=destination),cwd=root,stdout=output,stderr=subprocess.STDOUT)
    print(rid,'cerrado' if result.returncode==0 else 'fallo',flush=True)
    print(log.read_text(encoding='utf-8',errors='replace')[-2400:],flush=True)
    if result.returncode and rid=='E00':raise SystemExit(result.returncode)
    if result.returncode:raise SystemExit(result.returncode)
