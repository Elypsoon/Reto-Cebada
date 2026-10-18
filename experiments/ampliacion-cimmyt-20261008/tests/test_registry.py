import pytest
from cimmyt.common import save,digest
from cimmyt.registry import Registry,semantic_hash


def registry(tmp_path):
    (tmp_path/'registry').mkdir()
    (tmp_path/'runs/A01/artifacts').mkdir(parents=True)
    input_file=tmp_path/'input.txt';input_file.write_text('immutable')
    task=tmp_path/'task.md';task.write_text('- [ ] 1.1 Same behavior\n')
    snapshot=tmp_path/'snapshot.md';snapshot.write_bytes(task.read_bytes())
    protocol={'inputs':{'input.txt':digest(input_file)},'planning':[{'current_path':str(task),
        'semantic_sha256':semantic_hash(task),'snapshot':'snapshot.md','sha256':digest(snapshot)}]}
    save(tmp_path/'registry/protocol-v2.json',protocol)
    (tmp_path/'registry/protocol-v2.sha256').write_text(digest(tmp_path/'registry/protocol-v2.json'))
    save(tmp_path/'runs/A01/run.json',{'status':'frozen'})
    return Registry(tmp_path)


def test_incomplete_results_cannot_close(tmp_path):
    r=registry(tmp_path);r.transition('A01','running')
    with pytest.raises(ValueError,match='Recuperación'):r.transition('A01','completed',metrics={'rmse':1.})
    save(tmp_path/'runs/A01/artifacts/fresh-process-check.json',{'passed':True,'offline':True})
    r.transition('A01','completed',metrics={'rmse':1.})
    assert r.check_closed('A01')
    with pytest.raises(ValueError,match='cerrado'):r.transition('A01','running')
    (tmp_path/'runs/A01/artifacts/new.txt').write_text('changed')
    assert not r.check_closed('A01')


def test_semantic_changes_block_but_checkboxes_do_not(tmp_path):
    r=registry(tmp_path)
    (tmp_path/'task.md').write_text('- [x] 1.1 Same behavior\n')
    r.protocol()
    (tmp_path/'task.md').write_text('- [x] 1.1 Different behavior\n')
    with pytest.raises(ValueError,match='planificación'):r.protocol()


def test_input_and_protocol_identity_are_guarded(tmp_path):
    r=registry(tmp_path)
    (tmp_path/'input.txt').write_text('changed')
    with pytest.raises(ValueError,match='Entrada'):r.protocol()
    (tmp_path/'input.txt').write_text('immutable')
    save(tmp_path/'registry/protocol-v2.json',{'inputs':{},'planning':[]})
    with pytest.raises(ValueError,match='Protocolo alterado'):r.protocol()
