import socket
import json
import numpy as np
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest
from agrocebada.common import ROOT,ARTIFACTS,ID,TARGET
from agrocebada.inference import Predictor,official_export

pytestmark=pytest.mark.skipif(not (ARTIFACTS/"model_selected.joblib").exists(),reason="Requiere entrenamiento completo")


def test_app_offline_filters_real_inference_and_full_download(monkeypatch):
    st.cache_resource.clear();st.cache_data.clear()
    connect=socket.socket.connect
    def blocked(sock,address):
        if isinstance(address,tuple) and address[0] in ["127.0.0.1","::1"]:return connect(sock,address)
        raise OSError("Sin conexión externa para esta prueba")
    monkeypatch.setattr(socket.socket,"connect",blocked)
    calls=[];original=Predictor.predict
    def recorded(self,ids):
        calls.append(list(ids));return original(self,ids)
    monkeypatch.setattr(Predictor,"predict",recorded)
    at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=30).run()
    assert not at.exception and not at.error
    assert len(at.selectbox(key="parcel").options)==197
    at.selectbox(key="state").select("Tlaxcala").run()
    assert not at.exception and len(at.selectbox(key="parcel").options)==46
    pid=at.selectbox(key="parcel").value
    at.button(key="calculate").click().run()
    assert not at.exception and [pid] in calls
    result=at.session_state["result"]["row"]
    assert np.isclose(result["PRODUCCION_T"],result[TARGET]*result["AREA_HA"])
    assert len(official_export(Predictor()))==59
    assert "Descargar las 59 predicciones" in at.get_by_key("official_download").label
    interval=json.loads((ARTIFACTS/"validation.json").read_text(encoding="utf-8"))["interval"]["available"]
    if not interval:assert "INTERVAL_LOW" not in result
    at.text_input(key="search").set_value("identificador inexistente").run()
    assert not at.exception and any("No hay parcelas" in x.value for x in at.info)


def test_app_incompatible_artifact_has_clear_error(monkeypatch):
    import agrocebada.inference as inference
    st.cache_resource.clear()
    def incompatible(*args,**kwargs):raise ValueError("Las columnas son incompatibles con el modelo.")
    monkeypatch.setattr(inference,"Predictor",incompatible)
    at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=30).run()
    assert not at.exception
    assert at.error and "incompatibles" in at.error[0].value
