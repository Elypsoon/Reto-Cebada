import os
import subprocess
from cimmyt.common import ROOT,PROJECT,read,save,digest,now
from agrocebada.priority_resources import supervise

python=PROJECT/'.venv/Scripts/python.exe'
env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PROJ_NETWORK':'OFF','PYTHONIOENCODING':'utf-8'}
folder=ROOT/'registry/synthetic';folder.mkdir(exist_ok=True)
receipts=[]
for mode in ['fit','verify']:
    receipt=supervise([str(python),str(ROOT/'scripts/synthetic_worker.py'),mode],ROOT,env,
        folder/f'resources-{mode}.json',seconds=120,memory_mb=4096,log=folder/f'{mode}.log')
    if receipt['exit_code']!=0:raise ValueError('Preflight sintético falló; revisar registro '+mode)
    receipts.append(receipt)
optional=PROJECT/'experiments/prioridades-predictivas-20261006/optional/tabpfn-3'
manifest=read(optional/'manifest.json')
assert manifest['sha256']=='311ce18d97e9533d8585eaadafe040fbdd8070533209ed8696641dadc97a7301'
assert digest(optional/manifest['checkpoint'])==manifest['sha256']
assert digest(optional/'LICENSE')==manifest['license_sha256']
assert (optional/manifest['checkpoint']).stat().st_size==manifest['bytes']==233289807
version=subprocess.run([str(optional/'env/Scripts/python.exe'),'-c',
    "from importlib.metadata import version;print(version('tabpfn'))"],capture_output=True,text=True,check=True).stdout.strip()
assert version==manifest['package_version']=='9.1.0'
audit=read(ROOT/'registry/label-audit-v2.json');upper=audit['before_spatial']['C-local']['rows']
assert upper==29 and upper<30
save(ROOT/'registry/preflight-v2.json',{'at':now(),'passed':True,'synthetic_resources':receipts,
    'synthetic_recovery':read(folder/'synthetic-recovery.json'),'one_worker':True,'threads':2,
    'max_context':394,'features':14,'optional':{'status':'omitted_before_model_preflight_for_insufficient_local_support',
        'reason':'29 local candidates < 30 required; no TabPFN synthetic or official fit performed',
        'checkpoint_hash':manifest['sha256'],'license_hash':manifest['license_sha256'],'package_version':version,
        'environment_lock_sha256':digest(optional/'requirements.lock'),'identity_verified':True,
        'noncommercial_professional_experimental_purpose_previously_authorized':True},
    'implementation_tests_sha256':digest(ROOT/'registry/implementation-tests-v2.xml')})
print('Preflight y recuperación sintéticos verificados; A04 omitido por soporte, identidad TabPFN-3 verificada')
