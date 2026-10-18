import pytest
from agrocebada.priority_registry import PriorityRegistry


def test_omission_is_closed_but_not_predictively_tested(tmp_path):
    registry = PriorityRegistry(tmp_path)
    registry.create('P08-x', {'block':'P08', 'input_manifest':{}})
    registry.transition('P08-x', 'skipped', 'Sin checkpoint verificado')
    state = registry.state('P08-x')
    assert state['administratively_closed'] and not state['predictively_tested']
    with pytest.raises(ValueError):
        registry.transition('P08-x', 'completed', verified=True)
    with pytest.raises(FileExistsError):
        registry.create('P08-x', {'block':'P08', 'changed':True})


def test_altered_protocol_and_partial_result_cannot_complete(tmp_path):
    registry = PriorityRegistry(tmp_path)
    folder = registry.create('P06', {'block':'P06','input_manifest':{}})
    registry.transition('P06','running')
    with pytest.raises(ValueError):
        registry.transition('P06','completed', verified=False)
    (folder/'protocol.json').write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError):
        registry.validate('P06')
