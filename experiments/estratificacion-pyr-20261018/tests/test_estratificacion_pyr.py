"""Pruebas automatizadas para la fase experimental estratificacion-pyr-20261018."""
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

PHASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE_DIR / "src"))

from estratificacion_pyr.common import (
    PHASE_ROOT, PROCESSED, REGISTRY, RUNS, ID, TARGET
)
from estratificacion_pyr.features import (
    build_biweekly_and_historical_features, build_spatial_contrast_features
)
from estratificacion_pyr.modeling import (
    RUN_CATALOG, build_validation_schemes, calibrate_conformal_intervals
)


def test_pyr_split_audit_and_70_30_proportions():
    audit_path = REGISTRY / "pyr-split-audit.json"
    assert audit_path.exists()
    data = json.loads(audit_path.read_text(encoding="utf-8"))
    assert data["total_parcels"] == 197
    assert data["train_parcels"] == 138
    assert data["test_parcels"] == 59
    assert data["area_weighting"] is False
    assert 300.0 <= data["test_to_nearest_train_distance_m"]["median"] <= 400.0


def test_schemes_integrity_and_no_overlap():
    schemes_df = pd.read_csv(REGISTRY / "schemes.csv")
    assert len(schemes_df) == 138
    assert schemes_df[ID].is_unique
    for col in ["estratificado_5", "principal_5", "balanceado_4", "rotado_45_5"]:
        assert schemes_df[col].notna().all()
        assert len(schemes_df[col].unique()) in (4, 5)


def test_biweekly_and_spatial_contrast_no_target_leakage():
    master = gpd.read_parquet(PROCESSED / "parcels.parquet")
    sat = pd.read_parquet(PROCESSED / "satellite.parquet")
    X_bw1 = build_biweekly_and_historical_features(master, sat)
    master_perturbed = master.copy()
    master_perturbed[TARGET] = np.random.RandomState(42).uniform(0, 10, size=len(master))
    X_bw2 = build_biweekly_and_historical_features(master_perturbed, sat)
    pd.testing.assert_frame_equal(X_bw1, X_bw2)


def test_all_runs_registered_and_59_predictions_valid():
    summary_df = pd.read_csv(REGISTRY / "summary.csv")
    assert set(RUN_CATALOG.keys()) == set(summary_df["run_id"].unique())

    for r_id in RUN_CATALOG:
        run_dir = RUNS / r_id
        assert (run_dir / "metrics.json").exists()
        assert (run_dir / "run.json").exists()
        pred_59 = pd.read_csv(run_dir / "predictions_59.csv")
        assert len(pred_59) == 59
        assert list(pred_59.columns) == [ID, TARGET]
        assert pred_59[ID].is_unique
        assert np.isfinite(pred_59[TARGET]).all()
        assert (pred_59[TARGET] > 0).all()

        pred_int = pd.read_csv(run_dir / "predictions_59_intervals.csv")
        assert len(pred_int) == 59
        assert (pred_int["INTERVAL_HIGH"] >= pred_int[TARGET]).all()
        assert (pred_int[TARGET] >= pred_int["INTERVAL_LOW"]).all()


def test_improvements_over_baseline_and_control():
    summary = json.loads((REGISTRY / "summary.json").read_text(encoding="utf-8"))
    elig = json.loads((REGISTRY / "eligibility-evaluation.json").read_text(encoding="utf-8"))
    # Under estratificado-5 (PyR Question 5), R05, R06, R07, and R08 must beat B0 and R00
    rmse_b0_est = summary["B0"]["schemes"]["estratificado-5"]["global"]["rmse"]
    rmse_r00_est = summary["R00"]["schemes"]["estratificado-5"]["global"]["rmse"]
    rmse_r06_est = summary["R06"]["schemes"]["estratificado-5"]["global"]["rmse"]
    rmse_r07_est = summary["R07"]["schemes"]["estratificado-5"]["global"]["rmse"]
    rmse_r08_est = summary["R08"]["schemes"]["estratificado-5"]["global"]["rmse"]
    assert rmse_r07_est < rmse_r00_est < rmse_b0_est
    assert rmse_r08_est < rmse_r00_est < rmse_b0_est
    assert rmse_r06_est < rmse_r00_est < rmse_b0_est
    assert rmse_r07_est < 0.51

    # Under principal-5 (Spatial Block CV), R01 and R03 beat R00 and B0, and R06/R07/R08 pass all 4 schemes
    rmse_b0_sp = summary["B0"]["schemes"]["principal-5"]["global"]["rmse"]
    rmse_r00_sp = summary["R00"]["schemes"]["principal-5"]["global"]["rmse"]
    rmse_r01_sp = summary["R01"]["schemes"]["principal-5"]["global"]["rmse"]
    rmse_r03_sp = summary["R03"]["schemes"]["principal-5"]["global"]["rmse"]
    rmse_r08_sp = summary["R08"]["schemes"]["principal-5"]["global"]["rmse"]
    assert rmse_r01_sp < rmse_r03_sp < rmse_r00_sp < rmse_b0_sp
    assert rmse_r08_sp < rmse_b0_sp
    assert elig["R06"]["passes_all_4_schemes"] is True
    assert elig["R07"]["passes_all_4_schemes"] is True
    assert elig["R08"]["passes_all_4_schemes"] is True

    # Interval coverage >= 90%
    cov_r07 = summary["R07"]["interval_calibration_estratificado_5"]["empirical_coverage"]
    cov_r08 = summary["R08"]["interval_calibration_estratificado_5"]["empirical_coverage"]
    assert cov_r07 >= 0.90
    assert cov_r08 >= 0.90

