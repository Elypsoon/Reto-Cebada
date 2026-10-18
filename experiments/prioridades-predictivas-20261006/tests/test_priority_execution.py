import json
import os
import sys
import numpy as np
import pandas as pd
from agrocebada.priority_catalog import PriorityCandidate,serial_catalog
from agrocebada.priority_resources import supervise
from agrocebada import priority_run as runner
from agrocebada.priority_selection import select
from agrocebada.common import ID,TARGET


def test_all_blocks_and_optional_generation_independent():
    catalog=serial_catalog()
    assert set(catalog)=={f'P{i:02d}' for i in range(9)}
    assert catalog['P07']['model']=='tabicl-v2' and catalog['P08']['model']=='tabpfn-3'
    assert all(catalog[k]['total']==2 and not catalog[k]['enters_P06'] for k in ['P07','P08'])


def test_supervisor_interrupts_and_records_partial_resources(tmp_path):
    receipt=supervise([sys.executable,'-c','import time; time.sleep(4)'],tmp_path,dict(os.environ),tmp_path/'receipt.json',seconds=.1)
    assert receipt['exit_code']!=0 and receipt['reason']=='Límite de tiempo'
    assert receipt['includes_children'] and receipt['peak_tree_rss_mb']>0


def test_offline_worker_blocks_connection_before_network(tmp_path):
    script=tmp_path/'network_attempt.py'
    script.write_text('import socket\nsocket.create_connection(("127.0.0.1",9))\n',encoding='utf-8')
    log=tmp_path/'attempt.log'
    receipt=supervise([sys.executable,str(script)],tmp_path,dict(os.environ),tmp_path/'receipt.json',log=log)
    assert receipt['exit_code']!=0 and receipt['ip_socket_connections_blocked']
    assert 'conexión IP bloqueada' in log.read_text(encoding='utf-8',errors='replace') or 'IP bloqueada' in log.read_text(encoding='utf-8',errors='replace')


def test_full_worker_oof_and_fresh_recovery_without_refit(tmp_path,monkeypatch):
    ids=pd.Index([f'ID{i}' for i in range(197)],name=ID)
    rng=np.random.default_rng(2026)
    master=pd.DataFrame({'Estado':['A']*197,'Municipio':['M']*197,'AREA_HA':np.arange(197)+1,
                         TARGET:np.r_[rng.uniform(2,4,138),np.full(59,np.nan)]},index=ids)
    table=pd.DataFrame({'x':rng.normal(size=197),'region__A':np.ones(197)},index=ids)
    groups={s:pd.Series(np.arange(138)%3,index=ids[:138]) for s in runner.SCHEMES}
    grid=[PriorityCandidate('x',f) for f in ['global_mean','regional_mean']]
    monkeypatch.setattr(runner,'load',lambda:(master,{'x':table},groups))
    monkeypatch.setattr(runner,'candidates',lambda block:grid)
    monkeypatch.setattr(runner,'select',lambda block,tr,y,g,s,t:select(block,tr,y,g,s,t,grid=grid))
    art=tmp_path/'artifacts';(tmp_path/'protocol.json').write_text('{}',encoding='utf-8')
    runner.run('P02',art)
    runner.verify(art)
    check=json.loads((art/'fresh-process-check.json').read_text(encoding='utf-8'))
    assert check['n']==59 and check['metrics_recalculated'] and check['no_transform_refit']
    for scheme in runner.SCHEMES:
        oof=pd.read_csv(art/f'oof-{scheme}.csv')
        assert len(oof)==138 and oof[ID].is_unique and np.isfinite(oof.official).all()
