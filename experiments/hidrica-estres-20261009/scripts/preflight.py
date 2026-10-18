import sys
from pathlib import Path
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.common import ROOT,PROJECT,save
from hydric.resources import supervised
python=str(PROJECT/'.venv/Scripts/python.exe');offline=str(ROOT/'scripts/offline_worker.py')
(ROOT/'registry/synthetic').mkdir(parents=True,exist_ok=True)
results={}
for mode in ['fit','verify']:
    result=supervised([python,offline,'module','hydric.synthetic',mode],ROOT/f'registry/synthetic/{mode}-resources-v2.json',ROOT/f'registry/synthetic/{mode}-v2.log',seconds=60)
    if result['exit_code']!=0:raise ValueError('Preflight falló: '+mode)
    results[mode]=result
interrupted=supervised([python,offline,'module','hydric.synthetic','wait'],ROOT/'registry/synthetic/timeout-resources-v2.json',ROOT/'registry/synthetic/timeout-v2.log',seconds=.5)
assert interrupted['reason']=='time_limit' and interrupted['exit_code']!=0
results['timeout']=interrupted
memory=supervised([python,offline,'module','hydric.synthetic','wait'],ROOT/'registry/synthetic/memory-resources.json',ROOT/'registry/synthetic/memory.log',seconds=20,memory_mb=1)
assert memory['reason']=='memory_limit' and memory['includes_children']
results['memory']=memory
save(ROOT/'registry/resource-preflight.json',{'passed':True,'results':results,'original_environments_modified':False})
print('Preflight: recuperación sin red y límite de tiempo verificados')
