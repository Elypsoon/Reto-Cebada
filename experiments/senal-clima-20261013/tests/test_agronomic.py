import pandas as pd
import pytest
from signalclima.agronomic import import_records


def test_optional_conflicts_units_and_foreign_id(tmp_path,monkeypatch):
    import signalclima.common as common
    monkeypatch.setattr(common,'ROOT',tmp_path)
    assert import_records(None,['a'],tmp_path/'absent')['status']=='absent'
    rows=pd.DataFrame([
        ['a','2025','riego','2','cm','2025-06-01','bitácora'],
        ['a','2025','variedad','Esmeralda','','2025-06-01','bitácora'],
        ['a','2025','variedad','Adabella','','2025-06-01','otra bitácora']],
        columns=['ID_POLIGONO','campana','campo','valor','unidad','fecha_evento','procedencia'])
    path=tmp_path/'input.csv';rows.to_csv(path,index=False)
    result=import_records(path,['a'],tmp_path/'records')
    assert result['conflicts']==2 and result['predictive_use'] is False
    assert pd.read_csv(tmp_path/'records/records.csv').iloc[0].valor=='20.0'
    rows.loc[0,'ID_POLIGONO']='other';rows.to_csv(path,index=False)
    with pytest.raises(ValueError,match='ajeno'):import_records(path,['a'],tmp_path/'bad')


def test_descriptive_import_does_not_change_frozen_model_inputs(tmp_path,monkeypatch):
    import signalclima.common as common
    monkeypatch.setattr(common,'ROOT',tmp_path)
    frozen=tmp_path/'frozen-protocol.json';frozen.write_bytes(b'original protocol')
    predictions=tmp_path/'predictions.csv';predictions.write_bytes(b'original predictions')
    import_records(None,['a'],tmp_path/'data/descriptive/agronomic')
    assert frozen.read_bytes()==b'original protocol' and predictions.read_bytes()==b'original predictions'
