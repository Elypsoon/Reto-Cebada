import sys
from pathlib import Path
PHASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PHASE/'src'))
from signalclima.common import ROOT,read,save
from signalclima.registry import protocol,transition,begin_attempt
from signalclima.resources import supervised
p=protocol();run=sys.argv[1]
if run not in p['variants']:raise ValueError('Ejecución no viable/no registrada')
remaining=begin_attempt(run)
folder=ROOT/'runs'/run
result=supervised([sys.executable,str(ROOT/'scripts/offline_worker.py'),'module','signalclima.run','train',run],folder/'resources-run.json',folder/'training.log',seconds=remaining)
if result['exit_code']!=0:
    transition(run,'incomplete' if result['reason'] else 'failed',reason=result['reason'] or 'Proceso de entrenamiento falló')
    raise SystemExit(1)
transition(run,'fitted')
remaining-=result['seconds']
result=supervised([sys.executable,str(ROOT/'scripts/offline_worker.py'),'module','signalclima.run','verify',run],folder/'resources-verify.json',folder/'verify.log',seconds=max(0,remaining))
if result['exit_code']!=0:
    transition(run,'failed',reason='Recuperación no completada');raise SystemExit(1)
transition(run,'completed',verified=True,metrics=read(folder/'metrics.json'))
print(run,'completado y verificado',flush=True)
