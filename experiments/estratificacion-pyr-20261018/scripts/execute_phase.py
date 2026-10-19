"""Ejecutor reproducible de la fase experimental estratificacion-pyr-20261018."""
import sys
import time
import shutil
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.model_selection import StratifiedShuffleSplit

PHASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE_DIR / "src"))

from agrocebada.modeling import load_tables, metric
from estratificacion_pyr.common import (
    PHASE_ROOT, ROOT, PROCESSED, ARTIFACTS, DATASET, DOCS, REGISTRY, RUNS,
    ID, TARGET, SEED, START, CUTOFF, sha256, write_json, dependencies, phase_code_hash
)
from estratificacion_pyr.features import (
    build_biweekly_and_historical_features, build_spatial_contrast_features
)
from estratificacion_pyr.modeling import (
    RUN_CATALOG, build_validation_schemes, fit_and_predict_all_runs, calibrate_conformal_intervals
)

warnings.filterwarnings("ignore")


def main():
    t0 = time.perf_counter()
    REGISTRY.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    # Copy requirements.lock for phase traceability
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

    # 1. Audit of PyR.pdf Question 5 (70/30 Stratified Split & Spatial Proximity)
    u = master.to_crs(32614)
    tr_pts = u.iloc[train_indices].geometry.centroid
    te_pts = u.iloc[hidden_indices].geometry.centroid
    min_dists_te_to_tr = np.array([float(tr_pts.distance(p).min()) for p in te_pts])

    ct_state = pd.crosstab(master["Estado"], master["CONJUNTO"])
    ct_mun = pd.crosstab([master["Estado"], master["Municipio"]], master["CONJUNTO"])

    pyr_audit = {
        "document_path": "DataSet/PyR.pdf",
        "document_sha256": sha256(DATASET / "PyR.pdf") if (DATASET / "PyR.pdf").exists() else None,
        "total_parcels": int(len(master)),
        "train_parcels": int(len(train_indices)),
        "test_parcels": int(len(hidden_indices)),
        "split_mechanism": "Muestreo aleatorio estratificado 70/30 (Pregunta 5 PyR.pdf)",
        "official_metrics": ["RMSE", "MAE", "R2"],
        "area_weighting": False,
        "target_origin": "Comercializadora (pesaje en báscula sin ajuste por humedad/impurezas/mermas) + Productores (redondeado en Tlaxcala a 2.5, 3.0, 3.5 t/ha)",
        "state_distribution": {
            st: {
                "train": int(ct_state.loc[st, "ENTRENAMIENTO"]),
                "test": int(ct_state.loc[st, "PREDICCION"]),
                "test_ratio": float(ct_state.loc[st, "PREDICCION"] / (ct_state.loc[st, "ENTRENAMIENTO"] + ct_state.loc[st, "PREDICCION"]))
            }
            for st in ct_state.index
        },
        "test_to_nearest_train_distance_m": {
            "min": float(np.min(min_dists_te_to_tr)),
            "p25": float(np.percentile(min_dists_te_to_tr, 25)),
            "median": float(np.median(min_dists_te_to_tr)),
            "mean": float(np.mean(min_dists_te_to_tr)),
            "p75": float(np.percentile(min_dists_te_to_tr, 75)),
            "max": float(np.max(min_dists_te_to_tr)),
            "pct_within_600m": float(np.mean(min_dists_te_to_tr <= 600.0)),
            "pct_within_1000m": float(np.mean(min_dists_te_to_tr <= 1000.0)),
        }
    }
    write_json(REGISTRY / "pyr-split-audit.json", pyr_audit)

    # 2. Build validation schemes & save schemes.csv
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
        "phase_id": "estratificacion-pyr-20261018",
        "seed": SEED,
        "cutoff": CUTOFF,
        "code_hash": phase_code_hash(),
        "dependencies": dependencies(),
        "schemes": list(schemes.keys()) + ["holdout-70-30-30x"],
        "runs": RUN_CATALOG,
    })

    write_json(PHASE_ROOT / "workspace.json", {
        "phase": "estratificacion-pyr-20261018",
        "created_at": "2026-10-18",
        "status": "completed",
        "parcels_total": 197,
        "parcels_train": 138,
        "parcels_test": 59,
        "dependencies": dependencies()
    })

    # 3. Build Feature Bundle
    print("1/4 Construyendo matriz de características (Whittaker, Quincenal 14d, Histórico 2022-2024 y Contraste 1 km)...", flush=True)
    X_w40 = tables["whittaker_40_10"].join(external["nasa"]).copy()
    X_w40_geo = X_w40.join(location[["location_x", "location_y"]])
    X_bw = build_biweekly_and_historical_features(master, sat, cloud_max=30)
    X_spatial_contrast = build_spatial_contrast_features(X_w40, location, bandwidth_m=1000.0)
    X_r03 = pd.concat([X_w40_geo, X_bw, X_spatial_contrast], axis=1)
    X_r03 = X_r03.loc[:, ~X_r03.columns.duplicated()]

    feature_bundle = {
        "X_w40": X_w40,
        "X_w40_geo": X_w40_geo,
        "X_r03": X_r03,
        "states_all": states_all,
        "mun_all": mun_all,
        "coords_all": coords_all,
    }

    # 4. Run Cross-Validation across all 4 schemes
    print("2/4 Evaluando B0 y R00..R08 en los 4 esquemas de validación (estratificado-5, principal-5, balanceado-4, rotado-45-5)...", flush=True)
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
    print("3/4 Ejecutando simulación de 30 sorteos estratificados 70/30 (59 test / 138 train)...", flush=True)
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
    print("4/4 Ajustando modelos finales sobre las 138 parcelas y exportando predicciones + intervalos para las 59 parcelas...", flush=True)
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

        # Calibrate 90% conformal intervals using estratificado-5 OOF residuals
        cal_info = calibrate_conformal_intervals(y_train, oof_by_scheme["estratificado-5"][r_id], s_train, nominal=0.90)
        run_metrics["interval_calibration_estratificado_5"] = cal_info
        interval_summary[r_id] = cal_info

        # Save 59 predictions (official 2-column format + extended interval format)
        p59 = final_preds_59[r_id]
        s_59 = states_all[hidden_indices]
        radii_59 = np.array([cal_info["state_radii_t_ha"][st] for st in s_59])

        df_pred59 = pd.DataFrame({
            ID: master.iloc[hidden_indices][ID].to_numpy(),
            TARGET: p59
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

    # Paired comparisons against B0 (regional_mean) and active production selected (0.7641 in principal-5, 0.6010 in estratificado-5)
    active_ref = {"estratificado-5": 0.6010, "principal-5": 0.7641, "balanceado-4": 0.7510, "rotado-45-5": 0.7609}
    paired = {}
    for r_id in RUN_CATALOG:
        paired[r_id] = {}
        for sc_name in schemes:
            m_r = summary_dict[r_id]["schemes"][sc_name]["global"]
            m_b0 = summary_dict["B0"]["schemes"][sc_name]["global"]
            paired[r_id][sc_name] = {
                "rmse": m_r["rmse"],
                "delta_rmse_vs_B0": float(m_r["rmse"] - m_b0["rmse"]),
                "pct_improvement_vs_B0": float((m_b0["rmse"] - m_r["rmse"]) / m_b0["rmse"] * 100.0),
                "delta_rmse_vs_active_selected": float(m_r["rmse"] - active_ref[sc_name]),
                "pct_improvement_vs_active_selected": float((active_ref[sc_name] - m_r["rmse"]) / active_ref[sc_name] * 100.0),
            }
    write_json(REGISTRY / "paired-comparisons.json", paired)

    # Eligibility evaluation for R07 (best stratified) and R08 (best unified adaptive)
    eligibility = {}
    for candidate_id in ["R01", "R03", "R05", "R06", "R07", "R08"]:
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

    print(f"Fase estratificacion-pyr-20261018 ejecutada con éxito en {time.perf_counter()-t0:.1f}s.", flush=True)


if __name__ == "__main__":
    main()

