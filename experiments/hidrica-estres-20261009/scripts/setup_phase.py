"""Copias verificadas; no ajusta modelos ni transforma etiquetas."""
import sys
from pathlib import Path
import shutil
import json
PHASE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.common import ROOT,PROJECT,save,digest,now

receipt = ROOT/'registry/copy-origins.json'
if receipt.exists():
    raise ValueError('Preparación ya registrada; no sobrescribir')
for directory in ['data/processed','data/external','data/soil','registry','runs','docs','tests']:
    (ROOT/directory).mkdir(parents=True,exist_ok=True)
copies=[]
def copy(src,dst):
    src,dst = Path(src),Path(dst).resolve()
    assert dst.is_relative_to(ROOT) and src.resolve()!=dst
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
    assert digest(src)==digest(dst)
    copies.append({'source':str(src.resolve()),'target':str(dst),'sha256':digest(dst)})

prior=PROJECT/'experiments/prioridades-predictivas-20261006'
control=prior/'controls/C-activa'
for p in (control/'src').rglob('*.py'):
    if '__pycache__' not in p.parts: copy(p,ROOT/'controls/C-activa'/p.relative_to(control))
for p in (control/'data/processed').glob('*'):
    if p.is_file(): copy(p,ROOT/'controls/C-activa/data/processed'/p.name)
for p in (control/'artifacts').glob('*'):
    if p.is_file() and p.suffix in ['.json','.joblib','.csv']:
        copy(p,ROOT/'controls/C-activa/artifacts'/p.name)
for p in (control/'provenance').glob('*.json'):
    copy(p,ROOT/'controls/C-activa/provenance'/p.name)
copy(control/'requirements.lock',ROOT/'controls/C-activa/requirements.lock')
for p in (prior/'runs/P00-C-activa/artifacts').glob('*'):
    if p.is_file() and p.name.startswith(('oof-','metrics-','model_','predictions_')):
        copy(p,ROOT/'controls/W00-artifacts'/p.name)
for name in ['parcels.parquet','features_monthly_20_10.parquet','external_nasa.parquet','nasa-cells.csv','nasa-quality.json','satellite.parquet','source-manifest.json']:
    copy(PROJECT/'data/processed'/name,ROOT/'data/processed'/name)
for p in (PROJECT/'data/external').glob('nasa*.json'): copy(p,ROOT/'data/external'/p.name)
for name in ['schemes.csv','scheme-validation.json']:
    copy(prior/'registry'/name,ROOT/'registry'/name)
for name in ['offline_worker.py']:
    copy(PROJECT/'experiments/ampliacion-cimmyt-20261008/scripts'/name,ROOT/'scripts'/name)
copy(PROJECT/'requirements.lock',ROOT/'requirements.lock')
save(ROOT/'workspace.json',{'project_root':str(PROJECT),'phase_root':str(ROOT),'data_root':str(ROOT/'data'),'created':now()})
save(receipt,{'at':now(),'copies':copies,'all_verified':True,'isolated_destinations':True})
print('Copias verificadas:',len(copies))
