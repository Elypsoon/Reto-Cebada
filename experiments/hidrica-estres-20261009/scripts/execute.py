import sys,os
from pathlib import Path
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.common import ROOT,PROJECT,read,save,now
from hydric.registry import protocol,transition,state
from hydric.resources import supervised

p=protocol();lock=ROOT/'registry/training.lock'
fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
os.write(fd,str(os.getpid()).encode());os.close(fd)
try:
    for run in sys.argv[1:]:
        if run in p['catalog']['omitted']:
            transition(run,'not_viable',reason=p['catalog']['omitted'][run],verified=True,metrics=None)
            print(run,'no viable:',p['catalog']['omitted'][run],flush=True);continue
        if run!='W00' and run not in p['catalog']['variants']:raise ValueError('Ejecución no registrada')
        if run!='W00' and state('W00')['status']!='completed':raise ValueError('Control histórico no verificado')
        transition(run,'running');folder=ROOT/f'runs/{run}';failure='failed';start=now()
        python=str(PROJECT/'.venv/Scripts/python.exe');offline=str(ROOT/'scripts/offline_worker.py')
        try:
            command=[python,offline,'script',str(ROOT/'scripts/recover_control.py')] if run=='W00' else [python,offline,'module','hydric.run','train',run]
            result=supervised(command,folder/'resources-run.json',folder/'training.log')
            if result['exit_code']!=0:
                failure='interrupted' if result['reason'] else 'failed'
                raise ValueError('Proceso no completado; revisar training.log')
            if run!='W00':
                recovery=supervised([python,offline,'module','hydric.run','verify',run],folder/'resources-verify.json',folder/'verification.log',seconds=max(0,7200-result['seconds']))
                if recovery['exit_code']!=0:raise ValueError('Recuperación no completada')
            transition(run,'completed',verified=True,metrics=read(folder/'metrics.json'),started=start)
            print(run,'completado y verificado',flush=True)
        except BaseException as error:
            save(folder/'failure.json',{'error':repr(error),'at':now()})
            transition(run,failure,reason=repr(error));raise
finally:
    lock.unlink()
