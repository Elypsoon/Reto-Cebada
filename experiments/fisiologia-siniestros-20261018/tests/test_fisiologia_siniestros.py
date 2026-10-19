"""Pruebas de integridad, reproducibilidad, anti-fuga y artefactos de la fase fisiologia-siniestros-20261018."""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

PHASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY = PHASE_DIR / "registry"
RUNS = PHASE_DIR / "runs"
DOCS = PHASE_DIR / "docs"

EXPECTED_RUNS = ["B0", "R08", "E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12"]
EXPECTED_SCHEMES = ["estratificado-5", "principal-5", "balanceado-4", "rotado-45-5"]


def test_registry_and_docs_exist():
    assert (PHASE_DIR / "README.md").exists()
    assert (PHASE_DIR / "workspace.json").exists()
    assert (PHASE_DIR.parents[1] / "data" / "external" / "open_meteo_daily_2025_nodes.json").exists()
    assert (PHASE_DIR.parents[1] / "data" / "external" / "micro_topography_197.json").exists()
    assert (REGISTRY / "frozen-protocol.json").exists()
    assert (REGISTRY / "forensic-outlier-audit.json").exists()
    assert (REGISTRY / "feature-importance.csv").exists()
    assert (REGISTRY / "feature-importance.json").exists()
    assert (REGISTRY / "schemes.csv").exists()
    assert (REGISTRY / "summary.csv").exists()
    assert (REGISTRY / "summary.json").exists()
    assert (REGISTRY / "holdout-70-30-simulation.json").exists()
    assert (REGISTRY / "paired-comparisons.json").exists()
    assert (REGISTRY / "interval-calibration.json").exists()
    assert (REGISTRY / "eligibility-evaluation.json").exists()
    assert (DOCS / "forensic-outliers-and-features.md").exists()
    assert (DOCS / "results.md").exists()
    assert (DOCS / "conclusions.md").exists()


def test_forensic_audit_and_feature_importance():
    audit = json.loads((REGISTRY / "forensic-outlier-audit.json").read_text(encoding="utf-8"))
    assert len(audit["outlier_parcels"]) == 5
    assert 290.0 <= audit["western_chignahuapan_cluster"]["distance_m"] <= 305.0

    df_imp = pd.read_csv(REGISTRY / "feature-importance.csv")
    assert len(df_imp) >= 130
    assert {"feature", "family", "r_Puebla", "r_Hidalgo", "r_Tlaxcala", "mean_abs_intra_state_r"}.issubset(df_imp.columns)
    assert "F6_full_year_2025_pyr_q6" in set(df_imp["family"])
    assert "F7_openmeteo_daily_and_microtopo" in set(df_imp["family"])


def test_all_runs_and_predictions_valid():
    summary = json.loads((REGISTRY / "summary.json").read_text(encoding="utf-8"))
    for r_id in EXPECTED_RUNS:
        assert r_id in summary
        run_dir = RUNS / r_id
        assert (run_dir / "metrics.json").exists()
        assert (run_dir / "run.json").exists()
        p59 = pd.read_csv(run_dir / "predictions_59.csv")
        assert len(p59) == 59
        assert list(p59.columns) == ["ID_POLIGONO", "RENDIMIENTO_T_HA"]
        assert p59["RENDIMIENTO_T_HA"].notna().all()
        assert (p59["RENDIMIENTO_T_HA"] >= 0.5).all() and (p59["RENDIMIENTO_T_HA"] <= 6.5).all()

        for sc in EXPECTED_SCHEMES:
            oof = pd.read_csv(run_dir / f"oof-{sc}.csv")
            assert len(oof) == 138
            assert oof["prediction"].notna().all()


def test_e06_e08_and_e09_to_e12_improve_over_r08_control():
    summary = json.loads((REGISTRY / "summary.json").read_text(encoding="utf-8"))
    holdout = json.loads((REGISTRY / "holdout-70-30-simulation.json").read_text(encoding="utf-8"))
    elig = json.loads((REGISTRY / "eligibility-evaluation.json").read_text(encoding="utf-8"))

    r08_strat = summary["R08"]["schemes"]["estratificado-5"]["global"]["rmse"]
    e06_strat = summary["E06"]["schemes"]["estratificado-5"]["global"]["rmse"]
    e08_strat = summary["E08"]["schemes"]["estratificado-5"]["global"]["rmse"]
    e09_strat = summary["E09"]["schemes"]["estratificado-5"]["global"]["rmse"]
    e10_strat = summary["E10"]["schemes"]["estratificado-5"]["global"]["rmse"]
    e11_strat = summary["E11"]["schemes"]["estratificado-5"]["global"]["rmse"]
    e12_strat = summary["E12"]["schemes"]["estratificado-5"]["global"]["rmse"]

    # Monotonic progression: R08 (0.5056) > E08 (0.5026) > E06 (0.4935) > E09 (0.4915) > E10 (0.4899) > E11 (0.4821) > E12 (0.4809)
    assert e08_strat < r08_strat
    assert e06_strat < 0.495
    assert e09_strat < e06_strat
    assert e10_strat < e09_strat
    assert e11_strat < e10_strat
    assert e12_strat < e11_strat
    assert e12_strat < 0.482

    # E09..E12 beat R08 and E08 across ALL 4 validation schemes and 30x 70/30 holdout
    for r_id in ["E09", "E10", "E11", "E12"]:
        assert holdout[r_id]["rmse_mean"] < holdout["R08"]["rmse_mean"]
        assert holdout[r_id]["rmse_mean"] < holdout["E08"]["rmse_mean"]
        for sc in EXPECTED_SCHEMES:
            assert summary[r_id]["schemes"][sc]["global"]["rmse"] < summary["R08"]["schemes"][sc]["global"]["rmse"]
            assert summary[r_id]["schemes"][sc]["global"]["rmse"] < summary["E08"]["schemes"][sc]["global"]["rmse"]
    for r_id in ["E09", "E10", "E12"]:
        assert elig[r_id]["passes_all_4_schemes"] is True
    assert elig["E11"]["passes_stratified_and_principal"] is True

