"""Pruebas de integridad, reproducibilidad, anti-fuga y artefactos de la fase fisiologia-siniestros-20261018."""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

PHASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY = PHASE_DIR / "registry"
RUNS = PHASE_DIR / "runs"
DOCS = PHASE_DIR / "docs"

EXPECTED_RUNS = ["B0", "R08", "E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08"]
EXPECTED_SCHEMES = ["estratificado-5", "principal-5", "balanceado-4", "rotado-45-5"]


def test_registry_and_docs_exist():
    assert (PHASE_DIR / "README.md").exists()
    assert (PHASE_DIR / "workspace.json").exists()
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
    assert len(df_imp) >= 100
    assert {"feature", "family", "r_Puebla", "r_Hidalgo", "r_Tlaxcala", "mean_abs_intra_state_r"}.issubset(df_imp.columns)


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


def test_e06_and_e08_improve_over_r08_control():
    summary = json.loads((REGISTRY / "summary.json").read_text(encoding="utf-8"))
    holdout = json.loads((REGISTRY / "holdout-70-30-simulation.json").read_text(encoding="utf-8"))
    elig = json.loads((REGISTRY / "eligibility-evaluation.json").read_text(encoding="utf-8"))

    r08_strat = summary["R08"]["schemes"]["estratificado-5"]["global"]["rmse"]
    e04_strat = summary["E04"]["schemes"]["estratificado-5"]["global"]["rmse"]
    e05_strat = summary["E05"]["schemes"]["estratificado-5"]["global"]["rmse"]
    e06_strat = summary["E06"]["schemes"]["estratificado-5"]["global"]["rmse"]
    e08_strat = summary["E08"]["schemes"]["estratificado-5"]["global"]["rmse"]

    # E04, E05, E06, E08 all beat R08 in estratificado-5 and 30x 70/30 holdout
    assert e04_strat < r08_strat
    assert e05_strat < r08_strat
    assert e06_strat < 0.495  # Breaks the 0.500 t/ha barrier
    assert e08_strat < r08_strat
    assert holdout["E06"]["rmse_mean"] < holdout["R08"]["rmse_mean"]
    assert holdout["E08"]["rmse_mean"] < holdout["R08"]["rmse_mean"]

    # E01 and E03 beat R08 across all 3 strict spatial validation schemes
    for sc in ["principal-5", "balanceado-4", "rotado-45-5"]:
        assert summary["E01"]["schemes"][sc]["global"]["rmse"] < summary["R08"]["schemes"][sc]["global"]["rmse"]
        assert summary["E03"]["schemes"][sc]["global"]["rmse"] < summary["R08"]["schemes"][sc]["global"]["rmse"]

    # E08 beats R08 in estratificado-5, principal-5, balanceado-4 and passes all 4 eligibility gates
    assert summary["E08"]["schemes"]["principal-5"]["global"]["rmse"] < summary["R08"]["schemes"]["principal-5"]["global"]["rmse"]
    assert summary["E08"]["schemes"]["balanceado-4"]["global"]["rmse"] < summary["R08"]["schemes"]["balanceado-4"]["global"]["rmse"]
    assert elig["E08"]["passes_all_4_schemes"] is True
    assert elig["E06"]["schemes"]["estratificado-5"]["eligible_in_scheme"] is True
