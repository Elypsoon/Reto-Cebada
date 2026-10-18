import sys
import pytest
from signalclima.common import save,read


def test_interruption_resume_preserves_partials_and_budget(tmp_path,monkeypatch):
    import signalclima.common as common
    import signalclima.registry as registry
    import signalclima.resources as resources
    for module in [common,registry,resources]:monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(registry,'protocol',lambda:{})
    remaining=registry.begin_attempt('F00');assert remaining==21600
    folder=tmp_path/'runs/F00'
    result=resources.supervised([sys.executable,'-c','import time; time.sleep(2)'],folder/'resources-run.json',folder/'training.log',seconds=.1)
    assert result['reason']=='time_limit' and result['exit_code']!=0
    registry.transition('F00','incomplete',reason=result['reason'])
    (folder/'partial.csv').write_text('conservar')
    remaining=registry.begin_attempt('F00')
    assert remaining==pytest.approx(21600-result['seconds'])
    assert (folder/'partials/attempt-1/partial.csv').read_text()=='conservar'
    assert not (folder/'partial.csv').exists()
    registry.transition('F00','fitted');registry.transition('F00','completed')
    with pytest.raises(ValueError,match='sobrescritura'):registry.begin_attempt('F00')


def test_protocol_detects_added_and_modified_inputs(tmp_path,monkeypatch):
    import signalclima.common as common
    import signalclima.registry as registry
    for module in [common,registry]:monkeypatch.setattr(module,'ROOT',tmp_path)
    for name in ['requirements.lock','registry/schemes.csv','registry/viability.json','registry/spectral-audit.json','registry/nasa-audit.json','registry/preflight.json']:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}')
    source=tmp_path/'src/example.py';source.parent.mkdir();source.write_text('a')
    save(tmp_path/'registry/frozen-protocol.json',{'hashes':registry.input_hashes(),'dependencies':registry.runtime()})
    registry.protocol()
    source.write_text('b')
    with pytest.raises(ValueError,match='alterados'):registry.protocol()
    source.write_text('a');(tmp_path/'src/added.py').write_text('c')
    with pytest.raises(ValueError,match='alterados'):registry.protocol()


def test_contract_rejected_before_loading_model(tmp_path,monkeypatch):
    import signalclima.run as run
    import signalclima.common as common
    for module in [common,run]:monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(run,'protocol',lambda:{'hashes':{}})
    monkeypatch.setattr(run,'load',lambda:(None,None,None))
    folder=tmp_path/'runs/F00';folder.mkdir(parents=True)
    (folder/'model.joblib').write_bytes(b'tampered')
    (tmp_path/'registry').mkdir();(tmp_path/'registry/frozen-protocol.json').write_text('{}')
    save(folder/'contract.json',{'model_hash':'incompatible','protocol_hash':'incompatible'})
    with pytest.raises(ValueError,match='incompatible'):run.verify('F00')
