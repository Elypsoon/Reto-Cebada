"""Ejecutor reproducible de la fase experimental fisiologia-siniestros-20261018."""
from __future__ import annotations

import shutil
import sys
import time
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

PHASE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = PHASE_DIR.parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(PHASE_DIR / "src"))

from agrocebada.modeling import load_tables
from fisiologia_siniestros.common import (
    PHASE_ROOT,
    ROOT,
    PROCESSED,
    DOCS,
    REGISTRY,
    RUNS,
    ID,
    TARGET,
    SEED,
    CUTOFF,
    sha256,
    write_json,
    dependencies,
    phase_code_hash,
    metric,
    paired_comparison,
)
from fisiologia_siniestros.features import (
    build_biweekly_and_historical_features,
    build_spatial_contrast_features,
    build_agronomic_physiology_features,
    compute_forensic_outlier_audit,
    compute_feature_importance_registry,
)
from fisiologia_siniestros.modeling import (
    RUN_CATALOG,
    build_validation_schemes,
    fit_and_predict_all_runs,
    calibrate_conformal_intervals,
)

warnings.filterwarnings("ignore")


def main() -> None:
    t0 = time.perf_counter()
    REGISTRY.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    if (ROOT / "requirements.lock").exists():
        shutil.copyfile(ROOT / "requirements.lock", PHASE_ROOT / "requirements.lock")

    master = gpd.read_parquet(PROCESSED / "parcels.parquet")
    sat = pd.read_parquet(PROCESSED / "satellite.parquet")
    tables, external, location = load_tables(master)

    train_indices = np.flatnonzero(master[TARGET].notna())
    hidden_indices = np.flatnonzero(master[TARGET].isna())
    y_train = master[TARGET].to_numpy()[train_indices]
    states_all = master.Estado.to_numpy()
    mun_all = master.Municipio.to_numpy()
    s_train = states_all[train_indices]
    m_train = mun_all[train_indices]
    coords_all = location[["location_x", "location_y"]].to_numpy()

    # 1. Build validation schemes & save schemes.csv
    schemes, strata_train = build_validation_schemes(master, train_indices)
    df_schemes = pd.DataFrame({
        ID: master.iloc[train_indices][ID].to_numpy(),
        "Estado": s_train,
        "Municipio": m_train,
        "stratum": strata_train,
        "estratificado_5": schemes["estratificado-5"],
        "principal_5": schemes["principal-5"],
        "balanceado_4": schemes["balanceado-4"],
        "rotado_45_5": schemes["rotado-45-5"],
    })
    df_schemes.to_csv(REGISTRY / "schemes.csv", index=False)

    write_json(REGISTRY / "frozen-protocol.json", {
        "phase_id": "fisiologia-siniestros-20261018",
        "seed": SEED,
        "cutoff": CUTOFF,
        "code_hash": phase_code_hash(),
        "dependencies": dependencies(),
        "schemes": list(schemes.keys()) + ["holdout-70-30-30x"],
        "runs": RUN_CATALOG,
    })

    write_json(PHASE_ROOT / "workspace.json", {
        "phase": "fisiologia-siniestros-20261018",
        "created_at": "2026-10-18",
        "status": "completed",
        "parcels_total": 197,
        "parcels_train": 138,
        "parcels_test": 59,
        "cycles_multiannual_self_supervised": 788,
        "dependencies": dependencies(),
    })

    # 2. Build Feature Bundle (Base + F1..F5 Agronomic Physiology)
    print("1/5 Construyendo matriz fisiológica, daño intra-parcela, labranza y latentes 788 ciclos (F1..F5)...", flush=True)
    X_w40 = tables["whittaker_40_10"].join(external["nasa"]).copy()
    X_w40_geo = X_w40.join(location[["location_x", "location_y"]])
    X_bw = build_biweekly_and_historical_features(master, sat, cloud_max=30)
    X_spatial_contrast = build_spatial_contrast_features(X_w40, location, bandwidth_m=1000.0)
    X_r03 = pd.concat([X_w40_geo, X_bw, X_spatial_contrast], axis=1)
    X_r03 = X_r03.loc[:, ~X_r03.columns.duplicated()]

    X_agro = build_agronomic_physiology_features(master, sat, X_r03, cloud_max=30)

    f1_f2_cols = [c for c in X_agro.columns if c.startswith(("f1_", "f2_"))]
    f3_f4_cols = [c for c in X_agro.columns if c.startswith(("f3_", "f4_"))]
    f5_cols = [c for c in X_agro.columns if c.startswith("f5_")]

    X_e01 = pd.concat([X_r03, X_agro[f1_f2_cols]], axis=1)
    X_e02 = pd.concat([X_r03, X_agro[f3_f4_cols]], axis=1)
    X_e03 = pd.concat([X_r03, X_agro[f5_cols]], axis=1)
    X_full_agro = pd.concat([X_r03, X_agro], axis=1)
    X_full_agro = X_full_agro.loc[:, ~X_full_agro.columns.duplicated()]

    agro_sim_cols = [c for c in ["log_area", "slope", "s2_evi_early", "f2_fapar_early", "f4_tillage_ndti_std_early"] if c in X_full_agro.columns]
    puebla_res_cols = [c for c in ["f2_fapar_early", "slope", "f4_tillage_ndti_std_early", "log_area", "f5_ndwi_q90_hist", "f3_fapar_min_early"] if c in X_full_agro.columns]
    tlax_res_cols = [c for c in ["s2_senescence", "f3_damage_floor_early", "f3_srndi_min_sepoct", "landsat_vi6t_middle_diff_local1km"] if c in X_full_agro.columns]

    feature_bundle = {
        "X_w40": X_w40,
        "X_w40_geo": X_w40_geo,
        "X_r03": X_r03,
        "X_e01": X_e01,
        "X_e02": X_e02,
        "X_e03": X_e03,
        "X_full_agro": X_full_agro,
        "agro_sim_cols": agro_sim_cols,
        "puebla_res_cols": puebla_res_cols,
        "tlax_res_cols": tlax_res_cols,
        "states_all": states_all,
        "mun_all": mun_all,
        "coords_all": coords_all,
    }

    # 3. Forensic Outlier Audit & Feature Importance Registry
    print("2/5 Ejecutando auditoría forense de parcelas atípicas y registro de importancia por estado...", flush=True)
    outlier_audit = compute_forensic_outlier_audit(master, X_full_agro)
    write_json(REGISTRY / "forensic-outlier-audit.json", outlier_audit)

    df_imp, imp_summary = compute_feature_importance_registry(master, X_full_agro, train_indices)
    df_imp.to_csv(REGISTRY / "feature-importance.csv", index=False)
    write_json(REGISTRY / "feature-importance.json", imp_summary)

    # 4. Run Cross-Validation across all 4 schemes
    print("3/5 Evaluando B0, R08 y E01..E08 en los 4 esquemas de validación (estratificado-5, principal-5, balanceado-4, rotado-45-5)...", flush=True)
    oof_by_scheme = {sc: {r: np.zeros(len(train_indices)) for r in RUN_CATALOG} for sc in schemes}

    for sc_name, sc_folds in schemes.items():
        for f in np.unique(sc_folds):
            tr_local = np.flatnonzero(sc_folds != f)
            va_local = np.flatnonzero(sc_folds == f)
            tr_global = train_indices[tr_local]
            va_global = train_indices[va_local]
            fold_preds = fit_and_predict_all_runs(tr_global, va_global, y_train[tr_local], feature_bundle)
            for r_id, p in fold_preds.items():
                oof_by_scheme[sc_name][r_id][va_local] = p

    # 5. Run 30x Repeated 70/30 Stratified Holdout Simulation
    print("4/5 Ejecutando simulación de 30 sorteos estratificados 70/30 (59 test / 138 train)...", flush=True)
    sss = StratifiedShuffleSplit(n_splits=30, test_size=59 / 197, random_state=SEED)
    holdout_records = {r: [] for r in RUN_CATALOG}
    for split_idx, (tr_local, va_local) in enumerate(sss.split(train_indices, strata_train)):
        tr_global = train_indices[tr_local]
        va_global = train_indices[va_local]
        fold_preds = fit_and_predict_all_runs(tr_global, va_global, y_train[tr_local], feature_bundle)
        for r_id, p in fold_preds.items():
            m = metric(y_train[va_local], p)
            holdout_records[r_id].append({"split": split_idx, **m})

    holdout_summary = {}
    for r_id, recs in holdout_records.items():
        df_r = pd.DataFrame(recs)
        holdout_summary[r_id] = {
            "rmse_mean": float(df_r.rmse.mean()),
            "rmse_std": float(df_r.rmse.std()),
            "rmse_median": float(df_r.rmse.median()),
            "mae_mean": float(df_r.mae.mean()),
            "mae_std": float(df_r.mae.std()),
            "r2_mean": float(df_r.r2.mean()),
            "r2_std": float(df_r.r2.std()),
        }
    write_json(REGISTRY / "holdout-70-30-simulation.json", holdout_summary)

    # 6. Fit Final Models on all 138 training parcels and predict the 59 test parcels
    print("5/5 Ajustando modelos finales sobre las 138 parcelas y exportando predicciones + intervalos para las 59 parcelas...", flush=True)
    final_preds_59 = fit_and_predict_all_runs(train_indices, hidden_indices, y_train, feature_bundle)

    summary_rows = []
    summary_dict = {}
    interval_summary = {}

    for r_id, meta in RUN_CATALOG.items():
        run_dir = RUNS / r_id
        run_dir.mkdir(parents=True, exist_ok=True)

        run_metrics = {"run_id": r_id, **meta, "schemes": {}, "holdout_70_30_30x": holdout_summary[r_id]}

        for sc_name, sc_folds in schemes.items():
            p_oof = oof_by_scheme[sc_name][r_id]
            m_global = metric(y_train, p_oof)
            by_state = {
                st: metric(y_train[s_train == st], p_oof[s_train == st])
                for st in ["Puebla", "Hidalgo", "Tlaxcala"]
            }
            run_metrics["schemes"][sc_name] = {"global": m_global, "by_state": by_state}

            df_oof = pd.DataFrame({
                ID: master.iloc[train_indices][ID].to_numpy(),
                "Estado": s_train,
                "Municipio": m_train,
                "AREA_HA": master.iloc[train_indices]["AREA_HA"].to_numpy(),
                "fold": sc_folds,
                TARGET: y_train,
                "prediction": p_oof,
                "residual": y_train - p_oof,
            })
            df_oof.to_csv(run_dir / f"oof-{sc_name}.csv", index=False)

            summary_rows.append({
                "run_id": r_id,
                "name": meta["name"],
                "scheme": sc_name,
                "rmse": m_global["rmse"],
                "mae": m_global["mae"],
                "r2": m_global["r2"],
                "rmse_Puebla": by_state["Puebla"]["rmse"],
                "mae_Puebla": by_state["Puebla"]["mae"],
                "r2_Puebla": by_state["Puebla"]["r2"],
                "rmse_Hidalgo": by_state["Hidalgo"]["rmse"],
                "mae_Hidalgo": by_state["Hidalgo"]["mae"],
                "r2_Hidalgo": by_state["Hidalgo"]["r2"],
                "rmse_Tlaxcala": by_state["Tlaxcala"]["rmse"],
                "mae_Tlaxcala": by_state["Tlaxcala"]["mae"],
                "r2_Tlaxcala": by_state["Tlaxcala"]["r2"],
            })

        cal_info = calibrate_conformal_intervals(y_train, oof_by_scheme["estratificado-5"][r_id], s_train, nominal=0.90)
        run_metrics["interval_calibration_estratificado_5"] = cal_info
        interval_summary[r_id] = cal_info

        p59 = final_preds_59[r_id]
        s_59 = states_all[hidden_indices]
        radii_59 = np.array([cal_info["state_radii_t_ha"][st] for st in s_59])

        df_pred59 = pd.DataFrame({
            ID: master.iloc[hidden_indices][ID].to_numpy(),
            TARGET: p59,
        }).sort_values(ID)
        df_pred59.to_csv(run_dir / "predictions_59.csv", index=False)

        df_pred59_ext = pd.DataFrame({
            ID: master.iloc[hidden_indices][ID].to_numpy(),
            "Estado": s_59,
            "Municipio": mun_all[hidden_indices],
            "AREA_HA": master.iloc[hidden_indices]["AREA_HA"].to_numpy(),
            TARGET: p59,
            "PRODUCCION_T": p59 * master.iloc[hidden_indices]["AREA_HA"].to_numpy(),
            "INTERVAL_LOW": np.maximum(0.0, p59 - radii_59),
            "INTERVAL_HIGH": p59 + radii_59,
            "INTERVAL_WIDTH": 2.0 * radii_59,
        }).sort_values(ID)
        df_pred59_ext.to_csv(run_dir / "predictions_59_intervals.csv", index=False)

        write_json(run_dir / "metrics.json", run_metrics)
        write_json(run_dir / "run.json", {
            "run_id": r_id,
            **meta,
            "predictions_59_sha256": sha256(run_dir / "predictions_59.csv"),
            "mean_pred_59_t_ha": float(np.mean(p59)),
            "std_pred_59_t_ha": float(np.std(p59)),
            "min_pred_59_t_ha": float(np.min(p59)),
            "max_pred_59_t_ha": float(np.max(p59)),
        })
        summary_dict[r_id] = run_metrics

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(REGISTRY / "summary.csv", index=False)
    write_json(REGISTRY / "summary.json", summary_dict)
    write_json(REGISTRY / "interval-calibration.json", interval_summary)

    # Paired comparisons against B0 and R08
    paired = {}
    for r_id in RUN_CATALOG:
        paired[r_id] = {}
        for sc_name, sc_folds in schemes.items():
            m_r = summary_dict[r_id]["schemes"][sc_name]["global"]
            m_b0 = summary_dict["B0"]["schemes"][sc_name]["global"]
            m_r08 = summary_dict["R08"]["schemes"][sc_name]["global"]
            stat_vs_r08 = paired_comparison(
                y_train,
                oof_by_scheme[sc_name][r_id],
                oof_by_scheme[sc_name]["R08"],
                sc_folds,
                seed=SEED,
                n_boot=1000,
            )
            paired[r_id][sc_name] = {
                "rmse": m_r["rmse"],
                "mae": m_r["mae"],
                "r2": m_r["r2"],
                "delta_rmse_vs_B0": float(m_r["rmse"] - m_b0["rmse"]),
                "pct_improvement_vs_B0": float((m_b0["rmse"] - m_r["rmse"]) / m_b0["rmse"] * 100.0),
                "delta_rmse_vs_R08": float(m_r["rmse"] - m_r08["rmse"]),
                "pct_improvement_vs_R08": float((m_r08["rmse"] - m_r["rmse"]) / m_r08["rmse"] * 100.0),
                "paired_test_vs_R08": stat_vs_r08,
            }
    write_json(REGISTRY / "paired-comparisons.json", paired)

    eligibility = {}
    for candidate_id in ["R08", "E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08"]:
        sc_eval = {}
        for sc_name in schemes:
            m_c = summary_dict[candidate_id]["schemes"][sc_name]["global"]
            m_b0 = summary_dict["B0"]["schemes"][sc_name]["global"]
            st_c = summary_dict[candidate_id]["schemes"][sc_name]["by_state"]
            st_b0 = summary_dict["B0"]["schemes"][sc_name]["by_state"]
            beats_b0_by_2pct = m_c["rmse"] <= 0.98 * m_b0["rmse"]
            state_mae_ok = all(
                st_c[st]["mae"] <= 1.10 * st_b0[st]["mae"] + 1e-12
                for st in ["Puebla", "Hidalgo", "Tlaxcala"]
            )
            sc_eval[sc_name] = {
                "rmse": m_c["rmse"],
                "mae": m_c["mae"],
                "r2": m_c["r2"],
                "beats_B0_by_2pct": bool(beats_b0_by_2pct),
                "passes_regional_mae_gate_110pct": bool(state_mae_ok),
                "eligible_in_scheme": bool(beats_b0_by_2pct and state_mae_ok),
            }
        eligibility[candidate_id] = {
            "schemes": sc_eval,
            "passes_all_4_schemes": all(v["eligible_in_scheme"] for v in sc_eval.values()),
            "passes_stratified_and_principal": bool(
                sc_eval["estratificado-5"]["eligible_in_scheme"] and sc_eval["principal-5"]["eligible_in_scheme"]
            ),
            "interval_coverage_90": interval_summary[candidate_id]["empirical_coverage"],
            "interval_width_t_ha": interval_summary[candidate_id]["mean_adaptive_width_t_ha"],
        }
    write_json(REGISTRY / "eligibility-evaluation.json", eligibility)

    print(f"Fase fisiologia-siniestros-20261018 ejecutada con éxito en {time.perf_counter()-t0:.1f}s.", flush=True)


if __name__ == "__main__":
    main()

