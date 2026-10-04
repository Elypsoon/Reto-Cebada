"""Cierre con evidencias reales; conserva la versión activa si falla el gate."""
import json
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from agrocebada.common import ROOT,ARTIFACTS,WORKSPACE,ID,TARGET,write_json,sha256
from agrocebada import robust as r
from agrocebada.inference import verify_artifacts

p=argparse.ArgumentParser();p.add_argument('--close',action='store_true');args=p.parse_args()
reports={name:json.loads((ARTIFACTS/f'validation-{name}.json').read_text(encoding='utf-8')) for name in r.SCHEMES}
r.active_intact();integration=verify_artifacts()
snapshot=Path(WORKSPACE['snapshot']);manifest=json.loads((snapshot/'version-manifest.json').read_text(encoding='utf-8'))
restore_checks={name:sha256(snapshot/name)==digest for name,digest in manifest.items()}
assert all(restore_checks.values()),'Snapshot no coincide íntegramente con la versión conservada'
prior=json.loads((snapshot/'artifacts/integration-check.json').read_text(encoding='utf-8'))
assert prior['same_predictions'] and prior['metrics_reproduced'] and prior['predictions']==59
tests=json.loads((ARTIFACTS/'test-results.json').read_text(encoding='utf-8'));assert tests['experimental']['failed']==0 and tests['snapshot']['failed']==0
decision=r.promotion(reports,True);write_json(ARTIFACTS/'promotion.json',decision)
comparison=json.loads((ARTIFACTS/'phase-comparison.json').read_text(encoding='utf-8'));comparison.update(decision=decision,tests=tests,active_preserved=True,restore_verified=True,snapshot=str(snapshot))
write_json(ARTIFACTS/'phase-comparison.json',comparison)
write_json(ARTIFACTS/'restoration-check.json',{'verified_files':len(restore_checks),'all_hashes_match':True,'fresh_process_predictions':prior,'snapshot':str(snapshot),'active_intact':True})
if args.close:
    report_check=json.loads((ARTIFACTS/'technical-report-check.json').read_text(encoding='utf-8'))
    assert report_check['annex_predictions']==59 and report_check['annex_pages']==2 and report_check['visual_verified']
    if decision['promote']:raise ValueError('Este cierre requiere promover una versión completa; preparar esa migración antes de cerrar')
    version={'active_version':'selection-current-20261003','experiment':WORKSPACE['run_id'],'action':'keep_active','reason':decision,'active_model_hash':prior['model_hash'],'experimental_model_hash':integration['model_hash'],'restorable_snapshot':str(snapshot),'all_active_hashes_intact':True,'scope':'Desarrollo local; sin despliegue, validación temporal ni envío al organizador'}
    write_json(ARTIFACTS/'version-decision.json',version)
    # Describes exact files needed to recover this finished experimental version.
    paths=[]
    for folder in ['src','data/processed','data/external','docs','output/pdf','scripts','tests','.streamlit','openspec']:
        paths.extend(path for path in (ROOT/folder).rglob('*') if path.is_file() and '__pycache__' not in path.parts)
    paths.extend(path for path in ARTIFACTS.glob('*') if path.is_file())
    paths.extend(ROOT/path for path in ['app.py','requirements.lock','pyproject.toml','workspace.json','README.md','run.ps1'])
    write_json(ROOT/'experimental-version-manifest.json',{path.relative_to(ROOT).as_posix():sha256(path) for path in sorted(paths)})
    r.active_intact();print(version)
else:print(decision)
