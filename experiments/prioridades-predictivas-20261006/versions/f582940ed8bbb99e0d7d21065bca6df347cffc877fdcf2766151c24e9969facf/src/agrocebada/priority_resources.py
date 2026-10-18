"""Supervisor de un único proceso de entrenamiento y todos sus descendientes."""
import os
import subprocess
import time
from pathlib import Path
import psutil
from .tracking import atomic_json


def supervise(command, cwd, env, receipt, seconds=7200, memory_mb=4096, log=None):
    from .common import ROOT
    command=list(command)
    if len(command)>2 and command[1]=='-m':
        command=[command[0],str(ROOT/'scripts/offline_worker.py'),'module',*command[2:]]
    elif len(command)>1 and str(command[1]).endswith('.py'):
        command=[command[0],str(ROOT/'scripts/offline_worker.py'),'script',*command[1:]]
    started, peak, reason = time.perf_counter(), 0., None
    env = {**env, **{k: '2' for k in ['OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS']},
           'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'PYTHONDONTWRITEBYTECODE': '1',
           'PYTHONHASHSEED':'2026','MKL_CBWR':'COMPATIBLE','SKB_DATA_DIRECTORY':str(Path(cwd)/'tmp/skrub-data')}
    output = Path(log).open('a', encoding='utf-8') if log else None
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT if output else None)
    parent = psutil.Process(process.pid)
    try:
        while process.poll() is None:
            try:
                tree = [parent]+parent.children(recursive=True)
                rss = sum(p.memory_info().rss for p in tree if p.is_running())/1024**2
                peak = max(peak, rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                tree = [parent]
            elapsed = time.perf_counter()-started
            if peak > memory_mb or elapsed > seconds:
                reason = 'Límite de memoria agregado' if peak > memory_mb else 'Límite de tiempo'
                for p in reversed(tree):
                    try:
                        p.kill()
                    except psutil.NoSuchProcess:
                        pass
                process.wait()
                break
            time.sleep(.5)
    finally:
        if output:
            output.close()
        result = {'exit_code':process.wait(), 'seconds':time.perf_counter()-started,
                  'peak_tree_rss_mb':peak, 'reason':reason, 'limits':{'seconds':seconds,'rss_mb':memory_mb,'threads':2},
                  'includes_children':True, 'offline':True,'ip_socket_connections_blocked':len(command)>1 and command[1].endswith('offline_worker.py')}
        atomic_json(receipt,result)
    return result
