"""Supervisor de recuperación que conserva el entorno numérico histórico."""
import os
import subprocess
import time
from pathlib import Path
import psutil
from agrocebada.common import ROOT
from agrocebada.tracking import atomic_json


def supervise(command, cwd, env, receipt, seconds=1800, memory_mb=4096, log=None):
    # El supervisor nuevo impone MKL_CBWR=COMPATIBLE. No pertenecía a E07-v3.
    # Se recupera su entorno original, sin cambiar fuente, pesos ni tolerancia.
    environment = dict(env, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                       PYTHONDONTWRITEBYTECODE='1')
    command = [command[0], str(ROOT/'scripts/offline_worker.py'), 'module', *command[2:]]
    started = time.perf_counter()
    peak = 0.
    reason = None
    with Path(log).open('w', encoding='utf-8') as output:
        process = subprocess.Popen(command, cwd=cwd, env=environment, stdout=output, stderr=subprocess.STDOUT)
        parent = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                tree = [parent] + parent.children(recursive=True)
                peak = max(peak, sum(p.memory_info().rss for p in tree if p.is_running())/1024**2)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                tree = [parent]
            if peak > memory_mb or time.perf_counter()-started > seconds:
                reason = 'Límite de memoria agregado' if peak > memory_mb else 'Límite de tiempo'
                for child in reversed(tree):
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass
                break
            time.sleep(.5)
        result = {'exit_code': process.wait(), 'seconds': time.perf_counter()-started,
                  'peak_tree_rss_mb': peak, 'reason': reason, 'offline': True,
                  'ip_socket_connections_blocked': True, 'includes_children': True,
                  'limits': {'seconds': seconds, 'rss_mb': memory_mb},
                  'numeric_environment': 'original E07-v3; torch threads=2, preprocessing jobs=1',
                  'environment_overrides': {k: environment.get(k) for k in
                      ['MKL_CBWR', 'PYTHONHASHSEED', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS']}}
    atomic_json(receipt, result)
    return result
