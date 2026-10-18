"""Supervisor local con límites medidos del árbol de procesos."""
import os
import time
import subprocess
from pathlib import Path
import psutil
from .common import ROOT,safe,save,now


def supervised(command,receipt,log,seconds=21600,memory_bytes=6*1024**3):
    log=safe(log);receipt=safe(receipt);log.parent.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8',
         'PROJ_NETWORK':'OFF','PYTHONHASHSEED':'2026','MKL_CBWR':'COMPATIBLE',
         **{key:'2' for key in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']}}
    started=time.perf_counter();peak=0;reason=None
    with log.open('x',encoding='utf-8') as out:
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
        parent=psutil.Process(process.pid)
        try:
            while process.poll() is None:
                children=[parent]+parent.children(recursive=True)
                rss=0
                for p in children:
                    try:rss+=p.memory_info().rss
                    except psutil.NoSuchProcess:pass
                peak=max(peak,rss)
                if peak>memory_bytes or time.perf_counter()-started>seconds:
                    reason='memory_limit' if peak>memory_bytes else 'time_limit'
                    break
                time.sleep(.25)
        except KeyboardInterrupt:reason='interrupted'
        except psutil.NoSuchProcess:pass
        finally:
            if reason and process.poll() is None:
                for p in reversed([parent]+parent.children(recursive=True)):
                    try:p.kill()
                    except psutil.NoSuchProcess:pass
                process.wait()
        result={'at':now(),'exit_code':process.wait(),'seconds':time.perf_counter()-started,'peak_tree_rss_bytes':peak,
                'reason':reason,'memory_limit_bytes':memory_bytes,'time_limit_seconds':seconds,'includes_children':True,'threads':2}
        save(receipt,result)
    return result
