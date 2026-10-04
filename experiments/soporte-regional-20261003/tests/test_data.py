import pandas as pd
import pytest
from agrocebada.data import verify_master
from agrocebada.common import ID, TARGET


def valid_pair():
    t = pd.DataFrame({ID:["A","B"],"AREA_HA":[1.,2.],TARGET:[3.,None],"CONJUNTO":["ENTRENAMIENTO","PREDICCION"]})
    g = pd.DataFrame({ID:["A","B"],"área_ha":[1.,2.],"CONJUNTO":t.CONJUNTO})
    return t,g


def test_rejects_hidden_label():
    t,g=valid_pair(); t.loc[1,TARGET]=4
    with pytest.raises(ValueError,match="Etiqueta inesperada"):
        verify_master(t,g,expected=False)


def test_rejects_multiplied_join():
    t,g=valid_pair(); g=pd.concat([g,g.iloc[:1]])
    with pytest.raises(ValueError,match="duplicados"):
        verify_master(t,g,expected=False)


def test_rejects_area_discrepancy():
    t,g=valid_pair(); g.loc[0,"área_ha"]=10
    with pytest.raises(ValueError,match="discrepantes"):
        verify_master(t,g,expected=False)
