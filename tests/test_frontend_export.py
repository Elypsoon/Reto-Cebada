"""The public dashboard must show the same science as the saved predictor."""
import json

import numpy as np
import pandas as pd
import pytest

from agrocebada.common import ROOT, ARTIFACTS, ID, TARGET, sha256
from agrocebada.inference import Predictor
from agrocebada.modeling import metric

PUBLIC = ROOT / "frontend/public"
pytestmark = pytest.mark.skipif(not (PUBLIC / "data/model.json").exists(), reason="Frontend export not included")


def test_frontend_identity_metrics_and_provenance_match_active_model():
    exported = json.loads((PUBLIC / "data/model.json").read_text(encoding="utf-8"))
    contract = json.loads((ARTIFACTS / "contract_selected.json").read_text(encoding="utf-8"))
    report = json.loads((ARTIFACTS / "validation.json").read_text(encoding="utf-8"))
    assert exported["id"] == contract["presentation"]["id"] == "E12"
    assert exported["name"] == contract["presentation"]["name"]
    assert exported["sourceCommit"] == "32a6d2116e480c9388b9024faa300d1a48ee075d"
    assert exported["cutoff"] == "2025-12-31"
    assert exported["artifactCutoff"] == contract["cutoff"]
    assert exported["metrics"] == report["metrics"]["selected"]
    assert exported["byState"] == report["by_state"]
    assert exported["interval"] == report["interval"]
    for key, path in {
        "model": ARTIFACTS / "model_selected.joblib",
        "contract": ARTIFACTS / "contract_selected.json",
        "parcels": ROOT / "data/processed/parcels.parquet",
        "validation": ARTIFACTS / "validation.json", "oof": ARTIFACTS / "oof.csv",
    }.items():
        assert exported["sourceHashes"][key] == sha256(path)
    points = pd.DataFrame(exported["oof"]).set_index("id")
    original = pd.read_csv(ARTIFACTS / "oof.csv").set_index(ID).loc[points.index]
    assert len(points) == 138 and points.index.is_unique
    np.testing.assert_allclose(points.estimated, original.selected, atol=5e-7, rtol=0)
    np.testing.assert_allclose(points.observed, original[TARGET], atol=5e-7, rtol=0)
    assert points.state.tolist() == original.Estado.tolist()
    for key, value in metric(points.observed, points.estimated).items():
        assert np.isclose(value, exported["metrics"][key], atol=1e-6, rtol=0)


def test_frontend_parcels_intervals_and_downloads_reproduce_saved_predictor():
    parcels = pd.DataFrame(json.loads((PUBLIC / "data/parcels.json").read_text(encoding="utf-8")))
    assert len(parcels) == 197 and parcels.id.is_unique
    predictor = Predictor("selected")
    expected = predictor.predict(parcels.id)
    for field, column in {
        "estimate": TARGET, "production": "PRODUCCION_T", "low": "INTERVAL_LOW", "high": "INTERVAL_HIGH",
    }.items():
        np.testing.assert_allclose(parcels[field], expected[column], atol=5e-7, rtol=0)
    assert parcels.low.ge(0).all()
    assert (parcels.low <= parcels.estimate).all() and (parcels.estimate <= parcels.high).all()
    for filename in ["predictions_59.csv", "predictions_59_intervals.csv"]:
        assert sha256(PUBLIC / "downloads" / filename) == sha256(ARTIFACTS / filename)
    downloaded = pd.read_csv(PUBLIC / "downloads/predictions_59.csv")
    research = pd.read_csv(ROOT / "experiments/fisiologia-siniestros-20261018/runs/E12/predictions_59.csv")
    pd.testing.assert_frame_equal(downloaded, research, check_exact=True)
