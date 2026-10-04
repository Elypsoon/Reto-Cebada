"""La suite usa una copia de artefactos; nunca modifica un run cerrado."""
from pathlib import Path
import sys,os,shutil,subprocess,re,uuid,json
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
from agrocebada.tracking import read,check_manifest,atomic_json
catalog=read(root/'registry/catalog.json');rid=next(z['run_id'] for z in catalog['experiments'] if z['experiment']=='E08')
source=root/'runs'/rid;assert read(source/'run.json')['status']=='completed' and check_manifest(source/'artifacts',read(source/'artifact-manifest.json'))
destination=root/'tmp'/('integration-'+uuid.uuid4().hex);shutil.copytree(source/'artifacts',destination)
legacy=Path(read(root/'workspace.json')['legacy_root'])/'artifacts'
for path in legacy.glob('diagnostic-historic*'):shutil.copy2(path,destination/path.name)
for name in ['hidalgo-original-review.json','originals-check.json','corrections-v1.json']:shutil.copy2(legacy/name,destination/name)
env=dict(os.environ,PYTHONPATH=str(root/'src'),AGROCEBADA_ARTIFACTS=str(destination),PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
previous=root/'registry/test-results.json'
if previous.exists():
    history=root/'registry/test-attempts';history.mkdir(exist_ok=True)
    token=uuid.uuid4().hex
    shutil.copy2(previous,history/f'{token}-results.json');shutil.copy2(root/'registry/test-suite.log',history/f'{token}-suite.log')
result=subprocess.run([sys.executable,'-m','pytest',str(root/'tests'),'-q','-p','no:cacheprovider'],cwd=root,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
log=root/'registry/test-suite.log';log.write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
counts={name:int(re.search(r'(\d+) '+name,result.stdout).group(1)) if re.search(r'(\d+) '+name,result.stdout) else 0 for name in ['passed','failed','skipped','errors']}
atomic_json(root/'registry/test-results.json',{'passed':result.returncode==0,'counts':counts,'run_id':rid,'immutable_training_artifacts':check_manifest(source/'artifacts',read(source/'artifact-manifest.json')),'test_artifact_copy':str(destination),'log':str(log)})
print(result.stdout[-6500:],flush=True);print(result.stderr[-2000:],flush=True);raise SystemExit(result.returncode)
