"""Preflight sintético supervisado; nunca consulta etiquetas de las parcelas."""
import json
import os
from pathlib import Path
import subprocess
import sys
from agrocebada.common import ROOT
from agrocebada.priority_resources import supervise
from agrocebada.tracking import atomic_json

for name in ['tabicl-v2','tabpfn-3']:
    folder=ROOT/'optional'/name
    python=folder/'env/Scripts/python.exe'
    frozen=subprocess.run(['uv','pip','freeze','--python',str(python),'--cache-dir',str(ROOT/'tmp/uv-cache')],capture_output=True,text=True,check=True)
    (folder/'requirements.lock').write_text(frozen.stdout,encoding='utf-8')
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'TABPFN_DISABLE_TELEMETRY':'1','DO_NOT_TRACK':'1'}
    okay=True
    for action in ['smoke','verify-smoke']:
        receipt=supervise([str(python),'-m','agrocebada.priority_optional',action,name],ROOT,env,
                folder/f'resources-{action}.json',seconds=1800,log=folder/f'{action}.log')
        if receipt['exit_code']!=0:
            atomic_json(folder/'preflight.json',{'available':False,'synthetic_only':True,
                        'reason':receipt['reason'] or 'Error en prueba sintética; véase '+action+'.log','resources':receipt})
            okay=False
            break
    if okay:
        info=json.loads((folder/'preflight.json').read_text(encoding='utf-8'))
        info.update(fresh_process_verified=True,license_context='Uso profesional experimental no comercial confirmado por el usuario' if name=='tabpfn-3' else 'BSD-3-Clause',
                    limits_enforced=True,offline_recovery_verified=True)
        atomic_json(folder/'preflight.json',info)
    print(name,'disponible',okay,flush=True)
