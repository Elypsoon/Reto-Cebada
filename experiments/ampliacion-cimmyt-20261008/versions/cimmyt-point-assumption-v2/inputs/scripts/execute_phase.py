import os
import sys
from cimmyt.common import ROOT,PROJECT,read,save
from cimmyt.registry import Registry
from agrocebada.priority_resources import supervise

lock=ROOT/'registry/training-v2.lock'
fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
try:
    os.write(fd,str(os.getpid()).encode());os.close(fd)
    registry=Registry();registry.protocol()
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PROJ_NETWORK':'OFF','PYTHONIOENCODING':'utf-8'}
    for run in sys.argv[1:]:
        if run not in ['A01','A02','A03']:raise ValueError('Ejecución fuera del protocolo')
        folder=ROOT/f'runs/{run}/artifacts'
        registry.transition(run,'running');print('Inicio',run,flush=True)
        failure_status='failed'
        try:
            run_receipt=supervise([str(PROJECT/'.venv/Scripts/python.exe'),'-m','cimmyt.run','run',run],
                ROOT,env,folder/'resources-run.json',seconds=7200,memory_mb=4096,log=folder/'training.log')
            if run_receipt['exit_code']!=0:
                failure_status='interrupted' if run_receipt['reason'] else 'failed'
                raise ValueError('La comparación falló: '+run)
            if run=='A03' and read(folder/'curve-status.json')['applicable_outer_fits']==0:
                registry.transition(run,'skipped',reason='A02 no seleccionó donantes en ningún ajuste externo; curva no aplicable')
                print('A03 no aplicable; conserva estados y conteos',flush=True);continue
            verify_receipt=supervise([str(PROJECT/'.venv/Scripts/python.exe'),'-m','cimmyt.run','verify',run],
                ROOT,env,folder/'resources-verify.json',seconds=max(0,7200-run_receipt['seconds']),memory_mb=4096,
                log=folder/'verification.log')
            if verify_receipt['exit_code']!=0:
                raise ValueError('Recuperación negativa: '+run)
            registry.transition(run,'completed',metrics=read(folder/'metrics.json'))
            print('Completado y recuperado',run,flush=True)
        except BaseException as error:
            save(folder/'failure.json',{'error':repr(error)})
            if registry.state(run)['status']=='running':registry.transition(run,failure_status,reason=repr(error))
            raise
finally:
    lock.unlink()
