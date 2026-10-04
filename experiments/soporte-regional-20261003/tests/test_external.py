import json
import numpy as np
import pandas as pd
import pytest
from agrocebada import external as e
from agrocebada.common import PROCESSED


def test_nasa_units_dates_fill_and_physical_rejection(tmp_path,monkeypatch):
    original=e.EXTERNAL
    paths=list(original.glob("nasa*.json"))
    assert len(paths)==4
    for p in paths:(tmp_path/p.name).write_bytes(p.read_bytes())
    monkeypatch.setattr(e,"EXTERNAL",tmp_path)
    frames,_=e.read_nasa()
    assert len(frames)==4 and all(len(d)==214 for d in frames.values())
    p=tmp_path/paths[0].name;d=json.loads(p.read_text(encoding="utf-8"))
    d["properties"]["parameter"]["T2M"]["20250401"]=500.
    p.write_text(json.dumps(d),encoding="utf-8")
    with pytest.raises(ValueError,match="física"):e.read_nasa()
    d["properties"]["parameter"]["T2M"]["20250401"]=d["header"]["fill_value"]
    p.write_text(json.dumps(d),encoding="utf-8")
    with pytest.raises(ValueError,match="física"):e.read_nasa()


def test_siap_composite_keys_years_and_weighted_yield():
    d=pd.read_csv(PROCESSED/"siap-history.csv")
    assert len(d)==63 and d.Anio.between(2018,2024).all()
    assert len(d[["Nomestado","Nommunicipio"]].drop_duplicates())==9
    assert not ((d.Nomestado=="Tlaxcala")&(d.Nommunicipio=="Emiliano Zapata")).any()
    np.testing.assert_allclose(d["yield"],d.production/d.area)
