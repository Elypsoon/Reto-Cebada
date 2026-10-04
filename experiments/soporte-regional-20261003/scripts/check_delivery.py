"""Comprueba enlaces, cierres, versiones y salidas de la entrega acumulada."""
from pathlib import Path
import sys,re
import pandas as pd,numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from agrocebada.tracking import read,check_manifest,atomic_json
from agrocebada.common import ID,TARGET,sha256
closure=read(root/'registry/phase-closure.json');report=root/'docs/phase-results.md'
assert closure['report_hash']==sha256(report)
links=[]
for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
    if target.startswith(('http:','https:','#')):continue
    path=(report.parent/target.split('#')[0]).resolve();assert path.exists(),str(path);links.append(target)
catalog=read(root/'registry/catalog.json');mandatory=[]
for entry in catalog['experiments']:
    state=read(root/'runs'/entry['run_id']/'run.json')
    if not entry['optional']:assert state['status']=='completed';mandatory.append(entry['run_id'])
versions=[]
for version in (root/'versions').iterdir():assert check_manifest(version,read(version/'manifest.json'));versions.append(version.name)
verified=[];statuses={}
for folder in (root/'runs').iterdir():
    state=read(folder/'run.json');statuses[state['status']]=statuses.get(state['status'],0)+1
    assert state['status'] in ['completed','failed','skipped']
    if state.get('origin')=='historical':continue
    assert check_manifest(folder/'artifacts',read(folder/'artifact-manifest.json'))
    if state['status']!='completed':continue
    for path in (folder/'artifacts').glob('predictions*59.csv'):
        frame=pd.read_csv(path);assert len(frame)==59 and frame[ID].is_unique and np.isfinite(frame[TARGET]).all() and (frame[TARGET]>=0).all();verified.append(str(path.relative_to(root)))
assert closure['tests']['passed'] and closure['tests']['counts']['passed']==68
assert not closure['eligible_routes'] and not closure['activated']
primary=read(root/'runs/E08-v2/artifacts/validation.json')
assert all(not primary['interval_by_route'][route]['available'] for route in ['official','selected'])
atomic_json(root/'registry/delivery-check.json',{'passed':True,'report_hash':sha256(report),'local_links':links,'mandatory_completed':mandatory,'statuses':statuses,'verified_versions':versions,'exports_59_checked':verified,'intervals_disabled':True,'eligible_routes':[],'activated':False})
print({'passed':True,'local_links':len(links),'mandatory_completed':len(mandatory),'statuses':statuses,'exports_59_checked':len(verified)},flush=True)
