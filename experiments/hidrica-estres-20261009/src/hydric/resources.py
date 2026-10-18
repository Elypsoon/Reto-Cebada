import os,time,subprocess
from pathlib import Path
import psutil
from .common import ROOT,save,now

def supervised(command,receipt,log,seconds=7200,memory_mb=4096):
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8',
      'PROJ_NETWORK':'OFF','PYTHONHASHSEED':'2026','MKL_CBWR':'COMPATIBLE',
      **{k:'2' for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']}}
    started=time.perf_counter();peak=0.;reason=None
    Path(log).parent.mkdir(parents=True,exist_ok=True)
    with Path(log).open('x',encoding='utf-8') as out:
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
        parent=psutil.Process(process.pid)
        try:
            while process.poll() is None:
                try:
                    tree=[parent]+parent.children(recursive=True)
                    rss=sum(p.memory_info().rss for p in tree if p.is_running())/1024**2
                    peak=max(peak,rss)
                except psutil.NoSuchProcess: tree=[]
                if peak>memory_mb or time.perf_counter()-started>seconds:
                    reason='memory_limit' if peak>memory_mb else 'time_limit'
                    for p in reversed(tree):
                        try: p.kill()
                        except psutil.NoSuchProcess: pass
                    process.wait();break
                time.sleep(.25)
        finally:
            if process.poll() is None:
                for p in reversed([parent]+parent.children(recursive=True)):
                    try:p.kill()
                    except psutil.NoSuchProcess:pass
            result={'at':now(),'exit_code':process.wait(),'seconds':time.perf_counter()-started,
              'peak_tree_rss_mb':peak,'reason':reason,'memory_mb':memory_mb,'time_limit_seconds':seconds,
              'threads':2,'includes_children':True,'offline':str(ROOT/'scripts/offline_worker.py') in command}
            save(receipt,result)
    return result
