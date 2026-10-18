"""Congela todos los bloques antes del primer resultado externo, sin sobrescribir."""
from pathlib import Path
import json
import shutil
import hashlib
from datetime import datetime,timezone
from agrocebada.common import ROOT,sha256
from agrocebada.tracking import atomic_json,manifest,check_manifest
from agrocebada.priority_catalog import serial_catalog
from agrocebada.priority_data import load
from agrocebada.priority_registry import PriorityRegistry

if (ROOT/'registry/frozen-priority.json').exists():
    raise ValueError('Congelación existente; no se amplía después de resultados')
master,tables,groups=load()
catalog=serial_catalog()
evidence=json.loads((ROOT/'registry/evidence.json').read_text(encoding='utf-8'))
optional={name:json.loads((ROOT/'optional'/name/'preflight.json').read_text(encoding='utf-8'))
          for name in ['tabicl-v2','tabpfn-3']}
controls={name:json.loads((ROOT/'controls'/name/'provenance/procedure.json').read_text(encoding='utf-8'))
          for name in ['C-activa','C-soporte']}
inputs={}
for folder in ['src','scripts','tests','data/processed','data/external']:
    for name,digest in manifest(ROOT/folder).items():inputs[folder+'/'+name]=digest
for name in ['requirements.lock','pyproject.toml','workspace.json','registry/schemes.csv','registry/evidence.json','registry/implementation-tests.xml','registry/resource-preflight.json']:
    inputs[name]=sha256(ROOT/name)
for control in controls:
    for folder in ['src','data/processed','data/external','provenance']:
        for name,digest in manifest(ROOT/'controls'/control/folder).items():inputs[f'controls/{control}/{folder}/{name}']=digest
    for name in ['requirements.lock','pyproject.toml']:
        inputs[f'controls/{control}/{name}']=sha256(ROOT/'controls'/control/name)
    if (ROOT/'controls'/control/'workspace.json').exists():inputs[f'controls/{control}/workspace.json']=sha256(ROOT/'controls'/control/'workspace.json')
for model in optional:
    folder=ROOT/'optional'/model
    for p in folder.glob('*'):
        if p.is_file() and p.suffix not in ['.log']:
            inputs[p.relative_to(ROOT).as_posix()]=sha256(p)
version=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
snapshot=ROOT/'versions'/version;snapshot.mkdir(exist_ok=False)
for name in inputs:
    target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
atomic_json(snapshot/'manifest.json',inputs)
if not check_manifest(snapshot,inputs):raise ValueError('Versión congelada incompatible')
policy={'seed':2026,'cpu_threads':2,'sequential':True,'rss_limit_mb':4096,'mandatory_seconds':7200,
        'optional_seconds_per_configuration':1800,'inner':'Un grupo espacial existente por inner-fold; todos los folds obligatorios',
        'admission':{'rmse_ratio_max':.98,'better_folds_min':2,'state_mae_ratio_max':1.1,'state_min_n':10},
        'tie_atol':1e-10,'priority':['references','simpler','candidate_id'],'no_outer_reconfiguration':True,
        'outer_schemes':['principal-5','balanceado-4','rotado-45-5'],'diagnostic_scheme':'intraestado-3',
        'eligibility':'P06 exclusivamente; activa oficial y regional, protección estatal; activación falsa',
        'interval':{'nominal':.9,'calibration_min_n':25,'principal_coverage_min':.85},
        'population':197,'labeled':138,'hidden':59,'cutoff':'2025-10-31','units':'t/ha',
        'individual_diagnostics':'OOF de cada candidato fijo; ninguna selección con resultados externos',
        'sensitivity':{'leave_one_state_out':True,'buffer_m':1000,'polygon_distance':True,'train_min':80},
        'recovery_atol':1e-10,'recovery_rtol':0,'activated':False,'deployed':False,'sent':False}
registry=PriorityRegistry()
common={'version':version,'input_manifest':inputs,'policy':policy,'evidence_registry_hash':inputs['registry/evidence.json'],
        'evidence':evidence}
for block,entry in catalog.items():
    if block=='P00':
        for name,procedure in controls.items():
            registry.create('P00-'+name,{**common,'block':block,'control':name,'procedure':procedure,'catalog':entry})
    elif block in ['P07','P08']:
        for key in entry['configurations']:
            registry.create(block+'-'+key,{**common,'block':block,'table':key,'catalog':entry,'preflight':optional[entry['model']]})
    else:
        registry.create(block,{**common,'block':block,'catalog':entry})
atomic_json(ROOT/'registry/frozen-priority.json',{'at':datetime.now(timezone.utc).isoformat(),'version':version,
            'snapshot_manifest_hash':sha256(snapshot/'manifest.json'),'catalog':catalog,'controls':controls,'policy':policy,
            'preflight_only':True,'new_external_result_before_freeze':False,
            'protocol_hashes':{p.parent.name:sha256(p) for p in (ROOT/'runs').glob('*/protocol.json')}})
registry.publish()
print('Protocolos congelados:',version,len(list((ROOT/'runs').glob('*/protocol.json'))),flush=True)
