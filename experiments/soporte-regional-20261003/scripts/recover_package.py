"""Ensambla una versión completa desde un run cerrado y hashes verificados."""
from pathlib import Path
import os,sys,shutil,subprocess,json
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from agrocebada.tracking import read,check_manifest,manifest,atomic_json
from agrocebada.common import sha256
rid=sys.argv[1];source=root/'runs'/rid;state=read(source/'run.json')
assert state['status']=='completed' and check_manifest(source/'artifacts',read(source/'artifact-manifest.json'))
candidate='--candidate' in sys.argv
routes=[route for route,z in state['decision'].get('by_route',{}).items() if z['eligible']] if candidate else ['selected','official']
assert routes and (not candidate or state['experiment_id']=='E08')
destination=root/'packages'/(('candidate-' if candidate else '')+rid)
if destination.exists():raise FileExistsError('Un paquete existente no se sobrescribe')
code=root/'versions'/state['code_hash'];assert check_manifest(code,read(code/'manifest.json'))
shutil.copytree(code/'src',destination/'src')
shutil.copytree(root/'data/processed',destination/'data/processed')
shutil.copytree(root/'data/external',destination/'data/external')
shutil.copytree(source/'artifacts',destination/'artifacts')
if candidate:
    for route in set(['selected','official'])-set(routes):
        for name in [f'model_{route}.joblib',f'contract_{route}.json','predictions_59.csv' if route=='selected' else 'predictions_official_only_59.csv']:
            (destination/'artifacts'/name).unlink()
    atomic_json(destination/'candidate.json',{'eligible_routes':routes,'activated':False,'run_id':rid,'purpose':'Paquete candidato para revisión; no despliegue'})
for name in ['requirements.lock','pyproject.toml']:shutil.copy2(code/name,destination/name)
shutil.copy2(root/'workspace.json',destination/'workspace.json');shutil.copy2(source/'changes.json',destination/'changes.json')
atomic_json(destination/'manifest.json',manifest(destination))
env=dict(os.environ,PYTHONPATH=str(destination/'src'),PYTHONDONTWRITEBYTECODE='1',AGROCEBADA_ARTIFACTS=str(destination/'artifacts'),REPRO_ROUTES=json.dumps(routes))
subprocess.run([sys.executable,'-c',"from agrocebada.inference import Predictor,official_export; import pandas as pd,numpy as np,json,os; from agrocebada.common import ARTIFACTS,ID,TARGET;\nfor route in json.loads(os.environ['REPRO_ROUTES']):\n file='predictions_59.csv' if route=='selected' else 'predictions_official_only_59.csv'; a=official_export(Predictor(route)); b=pd.read_csv(ARTIFACTS/file); assert a[ID].equals(b[ID]) and np.allclose(a[TARGET],b[TARGET],rtol=0,atol=1e-10)\nprint('Paquete: 59 predicciones reproducidas por ruta')"],env=env,cwd=destination,check=True)
assert check_manifest(destination,read(destination/'manifest.json'))
print(destination,flush=True)
