import json
import numpy as np
import pandas as pd
import pytest
from agrocebada.common import ARTIFACTS,ID,TARGET
from agrocebada.inference import Predictor,official_export,verify_artifacts

pytestmark=pytest.mark.skipif(not (ARTIFACTS/"model_selected.joblib").exists(),reason="Requiere entrenamiento completo")


def test_export_reproduction_and_both_models():
    result=verify_artifacts()
    assert result["same_predictions"] and result["metrics_reproduced"]
    for name in ["selected","official"]:
        p=Predictor(name);d=official_export(p)
        expected=p.master.loc[p.master.CONJUNTO.eq("PREDICCION"),ID]
        assert set(d[ID])==set(expected) and d[ID].is_unique and list(d[ID])==sorted(expected)
        assert len(d)==59 and np.isfinite(d[TARGET]).all() and d[TARGET].ge(0).all()
        with pytest.raises(ValueError,match="identificadores"):p.predict(["no existe"])


def test_explanation_matches_exact_models_and_area_arithmetic():
    p=Predictor();ids=p.master.groupby("Estado")[ID].first().tolist()
    d=p.predict(ids)
    np.testing.assert_allclose(d.PRODUCCION_T,d[TARGET]*d.AREA_HA)
    for pid in ids:
        effects,info=p.explain(pid)
        if info["exact_additive"]:assert np.isclose(info["baseline"]+effects.contribution_t_ha.sum(),info["prediction"])
    report=json.loads((ARTIFACTS/"validation.json").read_text(encoding="utf-8"))
    if not report["interval"]["available"]:assert "INTERVAL_LOW" not in d
