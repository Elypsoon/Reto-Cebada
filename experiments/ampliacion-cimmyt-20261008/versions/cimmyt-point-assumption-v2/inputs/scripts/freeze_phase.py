"""Congelar entradas y documentos; cambios de checkboxes no alteran semántica."""
import shutil
from dataclasses import asdict
from importlib.metadata import version
from cimmyt.common import ROOT,PROJECT,SCHEMES,read,save,digest,now
from cimmyt.spatial import PROTOCOL,GRID,POLICIES
from cimmyt.registry import semantic_hash
from cimmyt.run import load_inputs

path=ROOT/'registry/protocol-v2.json'
if path.exists():raise ValueError('Protocolo ya congelado; no sobrescribir')
assert read(ROOT/'registry/preflight-v2.json')['passed']
from xml.etree import ElementTree
tests=ElementTree.parse(ROOT/'registry/implementation-tests-final.xml').getroot().findall('testsuite')
assert sum(int(s.attrib['tests']) for s in tests)==52
assert all(int(s.attrib['failures'])==0 and int(s.attrib['errors'])==0 for s in tests)
assert all(read(ROOT/f'runs/{run}/run.json')['status']=='pending' for run in ['A01','A02','A03'])
change=PROJECT/'openspec/changes/ampliacion-entrenamiento-cebada-con-cimmyt'
files=[change/'proposal.md',change/'design.md',change/'tasks.md',*sorted((change/'specs').rglob('spec.md'))]
assert len(files)==7
snapshot=ROOT/f'versions/{PROTOCOL}'
snapshot.mkdir(parents=True,exist_ok=False)
planning=[]
for source in files:
    relative=source.relative_to(change);target=snapshot/'planning'/relative
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    planning.append({'current_path':str(source),'snapshot':str(target.relative_to(ROOT)),
        'sha256':digest(target),'semantic_sha256':semantic_hash(source)})
inputs={}
paths=[]
for directory in ['src','scripts','data','controls']:
    paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths += [ROOT/n for n in ['requirements.lock','reader-requirements.lock','workspace.json',
    'registry/schemes.csv','registry/sources.json','registry/label-audit.json','registry/label-audit-v2.json',
    'registry/cohorts.json','registry/spatial-admission.json','registry/climate-acquisition.json',
    'registry/common-features.json','registry/preflight-v2.json','registry/population-check.json',
    'registry/implementation-tests-v2.xml','registry/implementation-tests-final.xml']]
for source in sorted(set(paths)):
    relative=source.relative_to(ROOT);inputs[str(relative)]=digest(source)
    target=snapshot/'inputs'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    assert digest(target)==inputs[str(relative)]
master,engine,schemes=load_inputs()
protocol={'id':PROTOCOL,'at':now(),'before_first_real_fit':True,'inputs':inputs,'planning':planning,
    'authorization':'User: Busca esa información en la web; si no la encuentras revisa el protocolo. Then: Aplicar el protocolo revisado.',
    'antecedent':{'path':'registry/history/v1-blocker.json','sha256':digest(ROOT/'registry/history/v1-blocker.json'),
        'required_verified_polygon_vertices':True},
    'spatial_policies':[asdict(p) for p in POLICIES],'training_policy':'principal','grid':GRID,
    'source_crs':'unknown','analysis_crs':'EPSG:4326','crs_basis':'explicit_assumption',
    'catalog':[dict(asdict(c),id=c.id) for c in engine.catalog()], 'references':['global_mean','regional_mean'],
    'maximum_unique_candidates':16,'features':'common-area-nasa-v1','schemes':SCHEMES,
    'minimum_support':{'labels':30,'groups':10,'campaigns':2},'sampling_seed':2026,
    'curve_fractions':[.25,.5,1.],'optional_cap':256,
    'inner_admission':{'rmse_gain':.02,'folds_won':2,'maximum_state_mae_ratio':1.1,'minimum_state_n':10},
    'stable_gain':{'principal_rmse_gain':.02,'minimum_schemes_with_gain':2,'mean_rmse_ratio':.98,
        'maximum_scheme_rmse_ratio':1.05,'maximum_state_mae_ratio':1.1,'minimum_state_n':10},
    'resources':{'one_worker':True,'threads':2,'memory_mb':4096,'main_seconds':7200,'optional_seconds':1800},
    'runtime':{name:version(name) for name in ['numpy','pandas','scipy','scikit-learn','geopandas','shapely','pyproj','joblib','psutil']},
    'tolerance':{'absolute':1e-10,'relative':0},'activated':False,'deployed':False,'sent':False}
save(path,protocol);(ROOT/'registry/protocol-v2.sha256').write_text(digest(path)+'\n',encoding='utf-8')
for run in ['A01','A02','A03']:
    folder=ROOT/f'runs/{run}';(folder/'artifacts').mkdir(exist_ok=True)
    shutil.copy2(folder/'run.json',ROOT/f'registry/history/v1-{run}-run.json')
    save(folder/'run.json',{'run_id':run,'status':'frozen','protocol_id':PROTOCOL,'protocol_sha256':digest(path),
        'metrics':None,'verified':False,'predictively_tested':False,'administratively_closed':False,
        'activated':False,'deployed':False,'sent':False,'at':now()})
save(snapshot/'snapshot-manifest.json',{'protocol_sha256':digest(path),'inputs':inputs,'planning':planning})
print('Protocolo congelado antes de ajustar:',len(inputs),'entradas y',len(planning),'documentos')
