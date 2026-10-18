import json
import pytest
import numpy as np
import pandas as pd
from dataclasses import asdict
from hydric import registry,run
from hydric.common import ID,TARGET,SCHEMES
from hydric.modeling import candidate_grid

def test_protocol_modification_is_rejected(monkeypatch):
    monkeypatch.setattr(registry,'read',lambda p:{'hashes':{'input':'original'}})
    monkeypatch.setattr(registry,'input_hashes',lambda:{'input':'changed'})
    with pytest.raises(ValueError,match='alterados'):registry.protocol()

def test_second_freeze_cannot_overwrite(tmp_path,monkeypatch):
    (tmp_path/'registry').mkdir()
    frozen=tmp_path/'registry/frozen-protocol.json';frozen.write_text('{}')
    monkeypatch.setattr(registry,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='ya congelado'):registry.freeze()
    assert frozen.read_text()=='{}'

def test_corrupted_model_is_rejected_before_deserialization(tmp_path,monkeypatch):
    folder=tmp_path/'runs/bad';folder.mkdir(parents=True)
    (folder/'model.joblib').write_bytes(b'not a fitted object')
    (folder/'contract.json').write_text(json.dumps({'model_hash':'original'}))
    monkeypatch.setattr(run,'ROOT',tmp_path)
    monkeypatch.setattr(run,'protocol',lambda:{})
    monkeypatch.setattr(run,'load',lambda:(None,None,None,None,None))
    with pytest.raises(AssertionError):run.verify('bad')

def test_synthetic_training_and_recovery_end_to_end(tmp_path,monkeypatch):
    n=197;ids=[f'synthetic-{i}' for i in range(n)]
    x=np.linspace(0,1,n);target=4+np.sin(x*5);target[138:]=np.nan
    master=pd.DataFrame({ID:ids,TARGET:target,'Estado':['a']*n,'Municipio':['fake']*n,'AREA_HA':1+x})
    X=pd.DataFrame({'x':x,'Estado':['a']*n},index=ids)
    base={'official':X.copy(),'enriched':X.copy()}
    schemes=pd.DataFrame([{ID:ids[i],'scheme':s,'fold':i%5} for s in SCHEMES for i in range(138)])
    inputs=(master,base,{},None,schemes)
    folder=tmp_path/'runs/W01-E';folder.mkdir(parents=True)
    (tmp_path/'registry').mkdir();(tmp_path/'registry/frozen-protocol.json').write_text('{}')
    record={'catalog':{'variants':{'W01-E':[asdict(r) for r in candidate_grid()]},'available_blocks':[]},'hashes':{}}
    monkeypatch.setattr(run,'ROOT',tmp_path)
    monkeypatch.setattr(run,'protocol',lambda:record)
    monkeypatch.setattr(run,'load',lambda:inputs)
    # Restrict test outputs to pytest's owned directory, without changing real phase receipts.
    def save_local(p,obj):p.write_text(json.dumps(obj,allow_nan=False,default=lambda v:v.item()),encoding='utf-8')
    monkeypatch.setattr(run,'save',save_local)
    run.train('W01-E');run.verify('W01-E')
    assert json.loads((folder/'fresh-process-check.json').read_text())['passed']
    assert len(pd.read_csv(folder/'predictions_59.csv'))==59
