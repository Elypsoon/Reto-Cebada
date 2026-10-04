"""Recuperación independiente de cada contexto TabPFN; no paquete de promoción."""
from pathlib import Path
import sys,shutil,os,subprocess
import pandas as pd
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from agrocebada.tracking import read,check_manifest,manifest,atomic_json
from agrocebada.common import ID,TARGET
adapter=root/'optional/adapter-v3'
assert check_manifest(adapter,read(adapter/'manifest.json'))
for key in ['monthly_20_10','whittaker_20_10']:
    rid='E07-v3-'+key;folder=root/'runs'/rid;state=read(folder/'run.json')
    assert state['status']=='completed' and check_manifest(folder/'artifacts',read(folder/'artifact-manifest.json'))
    destination=root/'packages'/('recovery-'+rid)
    assert not destination.exists()
    shutil.copytree(adapter,destination)
    (destination/'manifest.json').unlink()
    shutil.copytree(folder/'artifacts',destination/'artifacts')
    shutil.copy2(folder/'changes.json',destination/'changes.json')
    atomic_json(destination/'recovery.json',{'run_id':rid,'activated':False,'eligible':False,'purpose':'Recuperación experimental; sin promoción ni despliegue','interpreter_environment':str(root/'optional/tabpfn-2.5/env'),'dependency_lock':'optional/tabpfn-2.5/requirements.lock'})
    env=dict(os.environ,PYTHONPATH=str(destination/'src'),AGROCEBADA_ARTIFACTS=str(destination/'artifacts'),PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TABPFN_DISABLE_TELEMETRY='1')
    with (destination/'verification.log').open('w',encoding='utf-8') as log:subprocess.run([str(root/'optional/tabpfn-2.5/env/Scripts/python.exe'),'-m','agrocebada.optional','verify',key,str(destination/'artifacts')],cwd=destination,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    assert read(destination/'artifacts/fresh-process-check.json')['passed']
    atomic_json(destination/'manifest.json',manifest(destination))
    assert check_manifest(destination,read(destination/'manifest.json'))
    lines=[f'# {rid}: TabPFN-2.5 ({key})','','Configuración fija, referencia E00-v2; mismas 138 etiquetas. Sin activación ni incorporación a E08.','','| esquema | RMSE | MAE | sesgo | cambio RMSE |','| --- | --- | --- | --- | --- |']
    for scheme,z in state['metrics']['official'].items():lines.append(f'| {scheme} | {z["rmse"]:.6f} | {z["mae"]:.6f} | {z["bias"]:.6f} | {z["control_delta_rmse"]:+.6f} |')
    lines+=['','59 consultas reproducidas en un proceso nuevo desde el contexto y desde un paquete independiente, tolerancia absoluta 1e-10.','', '[Cambios y contexto](changes.json). [Recursos](artifacts/resources.json). [Paquete recuperable](../../packages/recovery-'+rid+'/manifest.json).','','## Resultados por estado','','| esquema | estado | n | MAE | sesgo | MAE media regional |','| --- | --- | --- | --- | --- | --- |']
    for scheme in state['metrics']['official']:
        frame=pd.read_csv(folder/f'artifacts/oof-{scheme}.csv').set_index(ID);control=pd.read_csv(root/f'runs/E00-v2/artifacts/oof-{scheme}.csv').set_index(ID).reindex(frame.index)
        for state_name,part in frame.groupby('Estado'):
            err=part.official-part[TARGET];regional=control.loc[part.index]
            lines.append(f'| {scheme} | {state_name} | {len(part)} | {err.abs().mean():.6f} | {err.mean():.6f} | {(regional.regional_mean-regional[TARGET]).abs().mean():.6f} |')
    (folder/'result.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(rid,'paquete y 59 consultas verificados',flush=True)
