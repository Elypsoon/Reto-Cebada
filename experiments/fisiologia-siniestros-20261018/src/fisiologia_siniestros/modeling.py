"""Catálogo de corridas (B0, R08 y E01..E08), arquitecturas híbridas/transductivas/bi-etapa y calibración conformal."""
from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge, HuberRegressor
from catboost import CatBoostRegressor

from agrocebada.modeling import (
    spatial_groups,
    CompactSelector,
    make_pipeline,
    Candidate,
    baseline_predictions,
)
from .common import SEED


RUN_CATALOG: dict[str, dict[str, str]] = {
    "B0": {
        "name": "B0_regional_mean",
        "title": "Media Estatal (Línea Base Regional)",
        "family": "baseline",
        "description": "Promedio simple del estado calculado exclusivamente en el subconjunto de entrenamiento.",
    },
    "R08": {
        "name": "R08_control_adaptive_ead",
        "title": "Control Productivo Vigente (AdaptiveEAD R08)",
        "family": "control_production",
        "description": "Ensamble Adaptativo por Distancia al Vecino (R08 de estratificacion-pyr-20261018) activo en producción antes de esta fase.",
    },
    "E01": {
        "name": "E01_phenology_stress_gpr",
        "title": "Alineación Fenológica Dinámica (F1) + Índices Fisiológicos FAPAR/LAI/MSI (F2)",
        "family": "phenology_physiology",
        "description": "Incorpora alineación por fecha pico (t_pico) e índices biofísicos previamente descartados (FAPAR, LAI, SAVI, MSI, DSWI4) en GPR Matérn 2.5 + CatBoost.",
    },
    "E02": {
        "name": "E02_polygon_damage_tillage",
        "title": "Piso de Daño Intra-Parcela (_min, _std) (F3) + Labranza Pre-Siembra NDTI/STI (F4)",
        "family": "damage_tillage_trees",
        "description": "Modela siniestros parciales dentro del polígono (cuantiles mínimos de FAPAR, ENDDI, NDDI, SRNDI) y preparación de suelo en abril-mayo (NDTI, STI) con ExtraTrees + CatBoost.",
    },
    "E03": {
        "name": "E03_multiannual_788_latent",
        "title": "Representación Auto-Supervisada sobre los 788 Ciclos Parcela × Año (2022–2025) (F5)",
        "family": "multiannual_self_supervised",
        "description": "Extrae la vocación histórica intrínseca del suelo (cuantil 90 2022-2024 de NDWI y Planet EVI) y la anomalía neta 2025 a partir de los 788 ciclos sin etiquetas adicionales.",
    },
    "E04": {
        "name": "E04_agro_similarity_kriging",
        "title": "Kriging Multiescala Ponderado por Similitud Agronómica y Topográfica",
        "family": "agro_spatial_kriging",
        "description": "Pondera los vecinos intra-estatales simultáneamente por distancia física (350 m, 700 m, 1,500 m) y similitud agronómica (log_area, slope, vigor temprano y labranza).",
    },
    "E05": {
        "name": "E05_transductive_graph_197",
        "title": "Propagación Transductiva por Laplaciano de Grafo sobre las 197 Parcelas (138 + 59)",
        "family": "transductive_graph",
        "description": "Construye el grafo espacial-agronómico completo sobre los 197 polígonos (entrenamiento + predicción) para propagar señal a través de puentes multi-salto.",
    },
    "E06": {
        "name": "E06_twostage_huber_residual",
        "title": "Modelo Bi-Etapa (Kriging Agronómico + Corrector Residual Intra-Estatal Huber-Ridge)",
        "family": "twostage_hurdle_residual",
        "description": "Etapa 1: Kriging agronómico adaptativo por estado. Etapa 2: Regresión robusta Huber + Ridge sobre los residuos locales usando los impulsores específicos de Puebla y Tlaxcala.",
    },
    "E07": {
        "name": "E07_agronomic_spectral_ensemble",
        "title": "Ensamble Espectral Fisiológico-Multianual Puro (F1–F5 + Contraste 1 km)",
        "family": "spectral_agronomic_ensemble",
        "description": "Fusión puramente espectral-topográfica de E01 (Fenología/Fisiología), E03 (Latente 788 ciclos), E02 (Daño/Labranza) y R06, óptima para extrapolación a bloques espaciales nuevos.",
    },
    "E08": {
        "name": "E08_master_agro_spatial_ead",
        "title": "Ensamble Maestro Adaptativo Agronómico-Espacial Bi-Etapa (EAD-Fisiológico)",
        "family": "master_adaptive_ead",
        "description": "Integra la rama vecinal bi-etapa/transductiva (E06 + R05 + E05) con la rama espectral fisiológica-multianual (E07) mediante compuerta de densidad efectiva de vecinos y encogimiento empírico de Bayes.",
    },
    "E09": {
        "name": "E09_source_regime_kriging",
        "title": "Jerarquía por Fuente de Origen Municipal: Comercializadora vs. Productor (PyR P1, P3, P4)",
        "family": "source_regime_hierarchy",
        "description": "Desacopla los municipios de báscula de comercializadora (Almoloya, Cuautepec, Tepeapulco, Chignahuapan; 2 decimales, baja varianza) de los municipios de encuesta al productor (Singuilucan, Emiliano Zapata, Apan, Calpulalpan, Nanacamilpa; redondeo a 0.5/0.1 t/ha).",
    },
    "E10": {
        "name": "E10_polygon_boundary_adjacency",
        "title": "Kriging de Contigüidad Física Borde-a-Borde (d_borde <= 35 m) + Similitud Agronómica",
        "family": "boundary_contiguity_kriging",
        "description": "Incorpora la distancia exacta entre linderos de polígonos (donde 33.9% de las parcelas de prueba comparten borde a <=10 m y 42.4% a <=25 m con una parcela de entrenamiento) junto con similitud agronómica e identidad de régimen.",
    },
    "E11": {
        "name": "E11_fullyear2025_openmeteo_huber",
        "title": "Corrector Bi-Etapa con Ciclo Completo 2025 (Ene–Dic, PyR P6) + Clima Diario Open-Meteo 5km y Micro-Topografía",
        "family": "fullyear_openmeteo_twostage",
        "description": "Integra las 30,550 escenas de barbecho/humedad invernal (Ene-Mar 2025) y cosecha/rastrojo (Nov-Dic 2025) más extremos climáticos diarios (Open-Meteo 5km ajustado por altitud/TPI en espigamiento y llenado de grano) en el corrector residual Huber-Ridge por estado.",
    },
    "E12": {
        "name": "E12_master_regime_boundary_meteo_ead",
        "title": "Ensamble Maestro Integral: Régimen de Fuente + Linderos + Ciclo 2025 Completo + Clima Diario Open-Meteo",
        "family": "master_regime_boundary_meteo",
        "description": "Fusiona adaptativamente el modelo bi-etapa de linderos y clima diario (E11) con un ensamble espectral-climático global (GPR Matérn 2.5 + CatBoost MAE) entrenado sobre residuos des-sesgados por régimen de fuente (F1–F7).",
    },
}


def build_strata(states_arr: np.ndarray, municipios_arr: np.ndarray) -> np.ndarray:
    """Construye los estratos Estado-Municipio respetando el tamaño mínimo por estrato (PyR P5)."""
    major_muns = {"Chignahuapan", "Calpulalpan", "Singuilucan", "Almoloya", "Cuautepec de Hinojosa"}
    strata = np.array([
        f"{s}__{m}" if m in major_muns else f"{s}__otros"
        for s, m in zip(states_arr, municipios_arr)
    ])
    strata = np.where(states_arr == "Tlaxcala", "Tlaxcala", strata)
    return strata


def build_validation_schemes(master_df: pd.DataFrame, train_indices: np.ndarray) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Construye los 4 esquemas de validación sobre las 138 parcelas de entrenamiento."""
    train_master = master_df.iloc[train_indices]
    s_train = train_master.Estado.to_numpy()
    m_train = train_master.Municipio.to_numpy()
    strata = build_strata(s_train, m_train)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    estratificado_5 = np.empty(len(train_indices), dtype=int)
    for k, (_, va) in enumerate(skf.split(train_indices, strata)):
        estratificado_5[va] = k

    principal_5, _ = spatial_groups(train_master, n=5)
    balanceado_4, _ = spatial_groups(train_master, n=4)

    pts = train_master.to_crs(32614).geometry.representative_point()
    xy = np.column_stack([pts.x, pts.y])
    theta = np.deg2rad(45)
    rot_xy = xy @ np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    blocks = [np.arange(len(train_indices))]
    while len(blocks) < 5:
        i = max(range(len(blocks)), key=lambda idx: len(blocks[idx]))
        b = blocks.pop(i)
        axis = int(np.ptp(rot_xy[b], axis=0).argmax())
        order = b[np.argsort(rot_xy[b, axis], kind="stable")]
        mid = len(order) // 2
        blocks.extend([order[:mid], order[mid:]])
    rotado_45_5 = np.empty(len(train_indices), dtype=int)
    for i, b in enumerate(blocks):
        rotado_45_5[b] = i

    return {
        "estratificado-5": estratificado_5,
        "principal-5": principal_5,
        "balanceado-4": balanceado_4,
        "rotado-45-5": rotado_45_5,
    }, strata


def fit_agro_similarity_kriging(
    coords_tr: np.ndarray,
    states_tr: np.ndarray,
    mun_tr: np.ndarray,
    y_tr: np.ndarray,
    X_agro_tr: np.ndarray,
) -> dict[str, Any]:
    """Ajusta el prior jerárquico y el escalador robusto para Kriging con similitud agronómica (E04)."""
    global_mu = float(y_tr.mean())
    state_mu = {
        s: float((y_tr[states_tr == s].sum() + 1.5 * global_mu) / ((states_tr == s).sum() + 1.5))
        for s in np.unique(states_tr)
    }
    mun_mu = {}
    for m in np.unique(mun_tr):
        ym = y_tr[mun_tr == m]
        st = states_tr[mun_tr == m][0]
        mun_mu[m] = float((ym.sum() + 3.0 * state_mu[st]) / (len(ym) + 3.0))

    scaler = RobustScaler().fit(np.nan_to_num(X_agro_tr, nan=0.0))
    Z_tr = scaler.transform(np.nan_to_num(X_agro_tr, nan=0.0))
    return {
        "coords_tr": coords_tr,
        "states_tr": states_tr,
        "mun_tr": mun_tr,
        "y_tr": y_tr,
        "global_mu": global_mu,
        "state_mu": state_mu,
        "mun_mu": mun_mu,
        "scaler": scaler,
        "Z_tr": Z_tr,
    }


def predict_agro_similarity_kriging(
    bundle: dict[str, Any],
    coords_va: np.ndarray,
    states_va: np.ndarray,
    mun_va: np.ndarray,
    X_agro_va: np.ndarray,
) -> np.ndarray:
    """Predice mediante Kriging multiescala ponderado por similitud física y agronómica (E04)."""
    c_tr = bundle["coords_tr"]
    s_tr = bundle["states_tr"]
    y_tr = bundle["y_tr"]
    Z_tr = bundle["Z_tr"]
    Z_va = bundle["scaler"].transform(np.nan_to_num(X_agro_va, nan=0.0))

    prior_va = np.array([
        bundle["mun_mu"].get(m, bundle["state_mu"].get(s, bundle["global_mu"]))
        for s, m in zip(states_va, mun_va)
    ])

    dists = np.sqrt(((coords_va[:, None, :] - c_tr[None, :, :]) ** 2).sum(axis=2))
    same_st = (states_va[:, None] == s_tr[None, :]).astype(float)

    d_agro = np.sqrt(((Z_va[:, None, :] - Z_tr[None, :, :]) ** 2).mean(axis=2))
    w_agro = np.exp(-0.5 * (d_agro / 1.8) ** 2)

    w_350 = np.exp(-0.5 * (dists / 350.0) ** 2) * same_st * (0.55 + 0.45 * w_agro)
    w_700 = np.exp(-0.5 * (dists / 700.0) ** 2) * same_st * (0.45 + 0.55 * w_agro)
    w_1500 = np.exp(-0.5 * (dists / 1500.0) ** 2) * same_st * (0.35 + 0.65 * w_agro)

    W_tot = 1.15 * w_350 + 0.85 * w_700 + 0.40 * w_1500
    w_sum = W_tot.sum(axis=1)
    num = W_tot @ y_tr + 1.85 * prior_va
    den = w_sum + 1.85
    return num / den


def predict_transductive_graph(
    coords_all: np.ndarray,
    states_all: np.ndarray,
    mun_all: np.ndarray,
    X_agro_all: np.ndarray,
    tr_idx: np.ndarray,
    y_tr: np.ndarray,
    va_idx: np.ndarray,
    prior_all_override: np.ndarray | None = None,
) -> np.ndarray:
    """Propagación transductiva por Laplaciano de grafo sobre los 197 polígonos simultáneamente (E05)."""
    n_total = len(coords_all)
    s_tr = states_all[tr_idx]
    m_tr = mun_all[tr_idx]

    global_mu = float(y_tr.mean())
    state_mu = {
        s: float((y_tr[s_tr == s].sum() + 1.5 * global_mu) / ((s_tr == s).sum() + 1.5))
        for s in np.unique(s_tr)
    }
    mun_mu = {}
    for m in np.unique(m_tr):
        ym = y_tr[m_tr == m]
        st = s_tr[m_tr == m][0]
        mun_mu[m] = float((ym.sum() + 3.0 * state_mu[st]) / (len(ym) + 3.0))

    if prior_all_override is not None:
        f0_197 = np.asarray(prior_all_override, dtype=float)
    else:
        f0_197 = np.array([
            mun_mu.get(m, state_mu.get(s, global_mu))
            for s, m in zip(states_all, mun_all)
        ])

    scaler = RobustScaler().fit(np.nan_to_num(X_agro_all[tr_idx], nan=0.0))
    Z_all = scaler.transform(np.nan_to_num(X_agro_all, nan=0.0))

    d_geo_197 = np.sqrt(((coords_all[:, None, :] - coords_all[None, :, :]) ** 2).sum(axis=2))
    d_agr_197 = np.sqrt(((Z_all[:, None, :] - Z_all[None, :, :]) ** 2).sum(axis=2))
    same_st_197 = (states_all[:, None] == states_all[None, :]).astype(float)

    W_197 = (
        1.1 * np.exp(-0.5 * (d_geo_197 / 450.0) ** 2 - 0.20 * (d_agr_197 / 2.2) ** 2)
        + 0.6 * np.exp(-0.5 * (d_geo_197 / 1100.0) ** 2 - 0.30 * (d_agr_197 / 2.2) ** 2)
    ) * same_st_197
    np.fill_diagonal(W_197, 0.0)
    L_197 = np.diag(W_197.sum(axis=1)) - W_197

    c_vec = np.zeros(n_total, dtype=float)
    c_vec[tr_idx] = 2.2
    c_prior = 1.5
    rhs = c_prior * f0_197.copy()
    rhs[tr_idx] += c_vec[tr_idx] * y_tr
    f_trans_197 = np.linalg.solve(np.diag(c_vec + c_prior) + 0.65 * L_197, rhs)
    return f_trans_197[va_idx]


def fit_and_predict_all_runs(
    tr_global: np.ndarray,
    va_global: np.ndarray,
    y_tr: np.ndarray,
    feature_bundle: dict[str, Any],
) -> dict[str, np.ndarray]:
    """Ajusta B0, R08 y E01..E08 estrictamente en tr_global y predice en va_global."""
    X_w40 = feature_bundle["X_w40"]
    X_w40_geo = feature_bundle["X_w40_geo"]
    X_r03 = feature_bundle["X_r03"]
    X_e01 = feature_bundle["X_e01"]
    X_e02 = feature_bundle["X_e02"]
    X_e03 = feature_bundle["X_e03"]
    X_full_agro = feature_bundle["X_full_agro"]
    agro_sim_cols = feature_bundle["agro_sim_cols"]
    puebla_res_cols = feature_bundle["puebla_res_cols"]
    tlax_res_cols = feature_bundle["tlax_res_cols"]

    states_all = feature_bundle["states_all"]
    mun_all = feature_bundle["mun_all"]
    coords_all = feature_bundle["coords_all"]

    s_tr, s_va = states_all[tr_global], states_all[va_global]
    m_tr, m_va = mun_all[tr_global], mun_all[va_global]
    c_tr, c_va = coords_all[tr_global], coords_all[va_global]

    preds: dict[str, np.ndarray] = {}

    # 0. Baseline B0 & Control R08 components
    preds["B0"] = baseline_predictions(y_tr, s_tr, s_va)["regional_mean"]

    c_r00 = Candidate("whittaker_40_10", "gpr", 5, ("nasa",), False)
    c_cb = Candidate("whittaker_40_10", "catboost", 3, ("nasa",), False)

    m_r01_full = make_pipeline(c_r00).fit(X_w40_geo.iloc[tr_global], y_tr)
    p_r01 = m_r01_full.predict(X_w40_geo.iloc[va_global])
    p_r02 = make_pipeline(c_cb).fit(X_w40_geo.iloc[tr_global], y_tr).predict(X_w40_geo.iloc[va_global])

    def fit_gpr_cb_hybrid(X_mat: pd.DataFrame, k_gpr: int = 12, k_cb: int = 25, w_gpr: float = 0.55) -> np.ndarray:
        pipe_gpr = Pipeline([
            ("select", CompactSelector(k_gpr)),
            ("scale", StandardScaler()),
            ("model", GaussianProcessRegressor(
                kernel=Matern(length_scale=5.0, nu=2.5) + WhiteKernel(0.15),
                optimizer=None, normalize_y=True, random_state=SEED,
            )),
        ])
        pipe_cb = Pipeline([
            ("select", CompactSelector(k_cb)),
            ("scale", StandardScaler()),
            ("model", CatBoostRegressor(
                depth=3, iterations=260, learning_rate=0.03, l2_leaf_reg=8,
                loss_function="RMSE", random_seed=SEED, thread_count=2,
                verbose=False, allow_writing_files=False,
            )),
        ])
        pg = pipe_gpr.fit(X_mat.iloc[tr_global], y_tr).predict(X_mat.iloc[va_global])
        pc = pipe_cb.fit(X_mat.iloc[tr_global], y_tr).predict(X_mat.iloc[va_global])
        return w_gpr * pg + (1.0 - w_gpr) * pc

    p_r03 = fit_gpr_cb_hybrid(X_r03, k_gpr=12, k_cb=25, w_gpr=0.55)

    pipe_et20 = Pipeline([
        ("select", CompactSelector(20)),
        ("scale", StandardScaler()),
        ("model", ExtraTreesRegressor(
            n_estimators=300, max_depth=6, min_samples_leaf=3, random_state=SEED, n_jobs=2,
        )),
    ])
    p_r04 = pipe_et20.fit(X_w40_geo.iloc[tr_global], y_tr).predict(X_w40_geo.iloc[va_global])

    # Hierarchical means & R05 spatial kriging
    global_mu = float(y_tr.mean())
    state_mu = {
        s: float((y_tr[s_tr == s].sum() + 1.5 * global_mu) / ((s_tr == s).sum() + 1.5))
        for s in np.unique(s_tr)
    }
    mun_mu = {}
    for m in np.unique(m_tr):
        ym = y_tr[m_tr == m]
        st = s_tr[m_tr == m][0]
        mun_mu[m] = float((ym.sum() + 3.0 * state_mu[st]) / (len(ym) + 3.0))

    prior_va = np.array([mun_mu.get(m, state_mu.get(s, global_mu)) for s, m in zip(s_va, m_va)])
    d_va_tr = np.sqrt(((c_va[:, None, :] - c_tr[None, :, :]) ** 2).sum(axis=2))
    same_st = (s_va[:, None] == s_tr[None, :])
    w_600 = np.exp(-0.5 * (d_va_tr / 600.0) ** 2) * same_st
    w_1500 = np.exp(-0.5 * (d_va_tr / 1500.0) ** 2) * same_st
    p_r05 = np.array([
        (w_600[i] @ y_tr + 0.5 * (w_1500[i] @ y_tr) + 2.0 * prior_va[i])
        / (w_600[i].sum() + 0.5 * w_1500[i].sum() + 2.0)
        for i in range(len(va_global))
    ])

    state_std = {s: max(float(np.std(y_tr[s_tr == s])), 0.25) for s in np.unique(s_tr)}
    mu_s_tr = np.array([state_mu[s] for s in s_tr])
    sd_s_tr = np.array([state_std[s] for s in s_tr])
    z_tr = (y_tr - mu_s_tr) / sd_s_tr
    mu_s_va = np.array([state_mu.get(s, global_mu) for s in s_va])
    sd_s_va = np.array([state_std.get(s, 0.5) for s in s_va])

    pipe_z_gpr = Pipeline([
        ("select", CompactSelector(10)),
        ("scale", StandardScaler()),
        ("model", GaussianProcessRegressor(
            kernel=Matern(length_scale=5.0, nu=2.5) + WhiteKernel(0.25),
            optimizer=None, normalize_y=False, random_state=SEED,
        )),
    ])
    p_z_gpr = mu_s_va + sd_s_va * pipe_z_gpr.fit(X_w40_geo.iloc[tr_global], z_tr).predict(X_w40_geo.iloc[va_global])

    p_r06_raw = 0.35 * p_r01 + 0.25 * p_r02 + 0.20 * p_r03 + 0.10 * p_r04 + 0.10 * p_z_gpr

    eb_gamma = {}
    for s in np.unique(s_tr):
        var_s = float(np.var(y_tr[s_tr == s]))
        eb_gamma[s] = float(np.clip((var_s - 0.10) / max(var_s, 1e-4), 0.25, 0.90))
    gamma_va = np.array([eb_gamma.get(s, 0.75) for s in s_va])

    w_eff = w_600.sum(axis=1)
    alpha_r08 = 0.55 * (w_eff / (w_eff + 1.5))
    spectral_r08 = 0.50 * p_r01 + 0.30 * p_r03 + 0.20 * p_r06_raw
    raw_r08 = alpha_r08 * p_r05 + (1.0 - alpha_r08) * spectral_r08
    preds["R08"] = mu_s_va + gamma_va * (raw_r08 - mu_s_va)

    # E01: Dynamic Phenology (F1) + Physiological Stress Indices (F2)
    preds["E01"] = fit_gpr_cb_hybrid(X_e01, k_gpr=14, k_cb=25, w_gpr=0.60)

    # E02: Intra-Parcel Damage Floor (F3) + Pre-Sowing Tillage (F4)
    p_e02_et = pipe_et20.fit(X_e02.iloc[tr_global], y_tr).predict(X_e02.iloc[va_global])
    p_e02_cb = fit_gpr_cb_hybrid(X_e02, k_gpr=12, k_cb=22, w_gpr=0.35)
    preds["E02"] = 0.45 * p_e02_et + 0.55 * p_e02_cb

    # E03: Self-Supervised Multi-Annual 788-Cycle Latent Features (F5)
    preds["E03"] = fit_gpr_cb_hybrid(X_e03, k_gpr=14, k_cb=25, w_gpr=0.60)

    # E04: Agronomic-Similarity Multi-Scale Kriging
    krig_agro = fit_agro_similarity_kriging(
        c_tr, s_tr, m_tr, y_tr,
        X_full_agro.iloc[tr_global][agro_sim_cols].to_numpy(dtype=float),
    )
    p_e04_raw = predict_agro_similarity_kriging(
        krig_agro, c_va, s_va, m_va,
        X_full_agro.iloc[va_global][agro_sim_cols].to_numpy(dtype=float),
    )
    preds["E04"] = mu_s_va + gamma_va * (p_e04_raw - mu_s_va)

    # E05: Semi-Supervised Transductive Graph Laplacian Propagation over 197 parcels
    # Uses R01 spectral-geographic prior on all 197 nodes + exact Laplacian solve
    prior_197_r01 = m_r01_full.predict(X_w40_geo)
    mu_s_197 = np.array([state_mu.get(s, global_mu) for s in states_all])
    gamma_197 = np.array([eb_gamma.get(s, 0.75) for s in states_all])
    prior_197_shrunk = mu_s_197 + gamma_197 * (prior_197_r01 - mu_s_197)
    p_e05_raw = predict_transductive_graph(
        coords_all, states_all, mun_all,
        X_full_agro[agro_sim_cols].to_numpy(dtype=float),
        tr_global, y_tr, va_global,
        prior_all_override=prior_197_shrunk,
    )
    preds["E05"] = mu_s_va + gamma_va * (p_e05_raw - mu_s_va)

    # E06: Two-Stage Hurdle / Intra-State Huber-Ridge Residual Corrector on Agronomic Kriging
    d_tr_tr = np.sqrt(((c_tr[:, None, :] - c_tr[None, :, :]) ** 2).sum(axis=2))
    np.fill_diagonal(d_tr_tr, 1e9)
    same_st_tr = (s_tr[:, None] == s_tr[None, :])
    w_tr_600 = np.exp(-0.5 * (d_tr_tr / 600.0) ** 2) * same_st_tr
    prior_tr = np.array([mun_mu.get(m, state_mu.get(s, global_mu)) for s, m in zip(s_tr, m_tr)])
    loo_krig_tr = np.array([
        (w_tr_600[i] @ y_tr + 2.0 * prior_tr[i]) / (w_tr_600[i].sum() + 2.0)
        for i in range(len(tr_global))
    ])
    res_krig_tr = y_tr - loo_krig_tr

    p_e06_base = p_e04_raw.copy()
    hid_va = np.flatnonzero(s_va == "Hidalgo")
    if len(hid_va) > 0:
        p_e06_base[hid_va] = 0.70 * p_r05[hid_va] + 0.30 * p_e04_raw[hid_va]

    p_res_corr = np.zeros(len(va_global), dtype=float)
    for st_name, st_cols, st_w in [
        ("Puebla", puebla_res_cols, 0.38),
        ("Tlaxcala", tlax_res_cols, 0.35),
    ]:
        st_tr_m = (s_tr == st_name)
        st_va_m = (s_va == st_name)
        if st_tr_m.sum() >= 10 and st_va_m.sum() > 0:
            X_st_tr = np.nan_to_num(X_full_agro.iloc[tr_global[st_tr_m]][st_cols].to_numpy(dtype=float), nan=0.0)
            X_st_va = np.nan_to_num(X_full_agro.iloc[va_global[st_va_m]][st_cols].to_numpy(dtype=float), nan=0.0)
            sc_st = RobustScaler().fit(X_st_tr)
            X_st_tr_s = sc_st.transform(X_st_tr)
            X_st_va_s = sc_st.transform(X_st_va)
            m_hub = HuberRegressor(alpha=10.0, epsilon=1.35, max_iter=500).fit(X_st_tr_s, res_krig_tr[st_tr_m])
            m_rdg = Ridge(alpha=25.0).fit(X_st_tr_s, res_krig_tr[st_tr_m])
            pred_corr = 0.50 * m_hub.predict(X_st_va_s) + 0.50 * m_rdg.predict(X_st_va_s)
            pred_corr = np.clip(pred_corr, -0.45, 0.45)
            gate_va = np.clip(w_eff[st_va_m] / 0.8, 0.30, 1.0)
            p_res_corr[st_va_m] = st_w * gate_va * pred_corr

    p_e06 = p_e06_base + p_res_corr
    # Apply Empirical Bayes variance shrinkage in Tlaxcala to account for producer rounding/quantization
    tlax_va = (s_va == "Tlaxcala")
    p_e06[tlax_va] = mu_s_va[tlax_va] + gamma_va[tlax_va] * (p_e06[tlax_va] - mu_s_va[tlax_va])
    preds["E06"] = np.clip(p_e06, 0.5, 6.5)

    # E07: Pure Spectral-Physiological-Multiannual Ensemble (no spatial neighbor labels)
    p_e07_raw = (
        0.35 * p_r01
        + 0.20 * p_r03
        + 0.20 * preds["E01"]
        + 0.15 * preds["E03"]
        + 0.10 * p_r06_raw
    )
    preds["E07"] = mu_s_va + gamma_va * (p_e07_raw - mu_s_va)

    # E08: Master Adaptive Agronomic-Spatial Bi-Stage EAD
    local_branch = 0.65 * (p_e06_base + 1.15 * p_res_corr) + 0.20 * p_r05 + 0.15 * p_e05_raw
    spectral_agro_branch = p_e07_raw
    alpha_e08 = 0.58 * (w_eff / (w_eff + 1.35))
    raw_e08 = alpha_e08 * local_branch + (1.0 - alpha_e08) * spectral_agro_branch
    preds["E08"] = mu_s_va + gamma_va * (raw_e08 - mu_s_va)

    # --- E09..E12: Source-Regime Hierarchy (PyR P1,P3,P4) + Polygon Boundary Contiguity + Full-Year 2025 (PyR P6) + Open-Meteo 5km Daily ---
    X_full_ext = feature_bundle.get("X_full_ext", X_full_agro)
    b_dist_all = feature_bundle.get("b_dist_all")
    ext_sim_cols = feature_bundle.get("ext_sim_cols", agro_sim_cols)
    puebla_ext_cols = feature_bundle.get("puebla_ext_cols", puebla_res_cols)
    hidalgo_ext_cols = feature_bundle.get("hidalgo_ext_cols", [])
    tlax_ext_cols = feature_bundle.get("tlax_ext_cols", tlax_res_cols)

    # E09: Municipality Source-Regime Hierarchy (Comercializadora vs Productor, PyR P1, P3, P4)
    # In-fold decimal precision detection with administrative fallback for unseen spatial blocks
    admin_comerc = {"Chignahuapan", "Almoloya", "Cuautepec de Hinojosa", "Tepeapulco"}
    mun_is_comerc = {}
    for m in np.unique(m_tr):
        ym = y_tr[m_tr == m]
        if len(ym) >= 2:
            f2 = float((np.abs(ym * 10.0 - np.round(ym * 10.0)) > 1e-4).mean())
            mun_is_comerc[m] = (f2 >= 0.50)
        else:
            mun_is_comerc[m] = (m in admin_comerc)

    src_tr = np.array(["comerc" if mun_is_comerc.get(m, m in admin_comerc) else "prod" for m in m_tr])
    src_va = np.array(["comerc" if mun_is_comerc.get(m, m in admin_comerc) else "prod" for m in m_va])
    reg_tr = np.array([f"{s}__{src}" for s, src in zip(s_tr, src_tr)])
    reg_va = np.array([f"{s}__{src}" for s, src in zip(s_va, src_va)])

    src_mu = {
        src: float((y_tr[src_tr == src].sum() + 1.5 * global_mu) / ((src_tr == src).sum() + 1.5))
        if (src_tr == src).sum() > 0 else global_mu
        for src in ["comerc", "prod"]
    }
    reg_mu = {}
    reg_gamma = {}
    for r_key in np.unique(reg_tr):
        yr = y_tr[reg_tr == r_key]
        st, src = r_key.split("__")
        anchor = 0.65 * state_mu[st] + 0.35 * src_mu[src]
        reg_mu[r_key] = float((yr.sum() + 1.5 * anchor) / (len(yr) + 1.5))
        var_r = float(np.var(yr)) if len(yr) >= 3 else float(np.var(y_tr[s_tr == st]))
        reg_gamma[r_key] = float(np.clip((var_r - 0.08) / max(var_r, 1e-4), 0.25, 0.90))

    mun_reg_mu = {}
    for m in np.unique(m_tr):
        ym = y_tr[m_tr == m]
        st = s_tr[m_tr == m][0]
        src = "comerc" if mun_is_comerc.get(m, m in admin_comerc) else "prod"
        r_key = f"{st}__{src}"
        mun_reg_mu[m] = float((ym.sum() + 2.2 * reg_mu.get(r_key, src_mu[src])) / (len(ym) + 2.2))

    prior_reg_va = np.array([
        mun_reg_mu.get(m, reg_mu.get(rk, state_mu.get(s, 0.55 * src_mu[src] + 0.45 * preds["E07"][i])))
        for i, (s, m, rk, src) in enumerate(zip(s_va, m_va, reg_va, src_va))
    ])
    gamma_reg_va = np.array([reg_gamma.get(rk, 0.75) for rk in reg_va])

    same_reg = (reg_va[:, None] == reg_tr[None, :]).astype(float)
    w_reg_600 = np.exp(-0.5 * (d_va_tr / 600.0) ** 2) * same_reg
    w_reg_1500 = np.exp(-0.5 * (d_va_tr / 1500.0) ** 2) * same_reg
    p_e09 = np.array([
        (w_reg_600[i] @ y_tr + 0.5 * (w_reg_1500[i] @ y_tr) + 2.0 * prior_reg_va[i])
        / (w_reg_600[i].sum() + 0.5 * w_reg_1500[i].sum() + 2.0)
        for i in range(len(va_global))
    ])
    p_e09_out = p_e09.copy()
    p_e09_out[tlax_va] = prior_reg_va[tlax_va] + gamma_reg_va[tlax_va] * (p_e09_out[tlax_va] - prior_reg_va[tlax_va])
    preds["E09"] = np.clip(p_e09_out, 0.5, 6.5)

    # E10: Polygon Boundary-to-Boundary Adjacency (d_borde <= 35 m) + Agronomic Similarity Kriging
    if b_dist_all is not None:
        d_boun = b_dist_all[np.ix_(va_global, tr_global)]
    else:
        d_boun = d_va_tr

    sc_ext = RobustScaler().fit(np.nan_to_num(X_full_ext.iloc[tr_global][ext_sim_cols].to_numpy(dtype=float), nan=0.0))
    Z_ext_tr = sc_ext.transform(np.nan_to_num(X_full_ext.iloc[tr_global][ext_sim_cols].to_numpy(dtype=float), nan=0.0))
    Z_ext_va = sc_ext.transform(np.nan_to_num(X_full_ext.iloc[va_global][ext_sim_cols].to_numpy(dtype=float), nan=0.0))
    d_ext_agro = np.sqrt(((Z_ext_va[:, None, :] - Z_ext_tr[None, :, :]) ** 2).mean(axis=2))
    w_ext_agro = np.exp(-0.5 * (d_ext_agro / 1.8) ** 2)

    w_b35 = np.exp(-0.5 * (d_boun / 35.0) ** 2) * same_reg * (0.65 + 0.35 * w_ext_agro)
    w_c350 = np.exp(-0.5 * (d_va_tr / 350.0) ** 2) * same_reg * (0.55 + 0.45 * w_ext_agro)
    w_c750 = np.exp(-0.5 * (d_va_tr / 750.0) ** 2) * same_reg * (0.45 + 0.55 * w_ext_agro)
    w_c1500 = np.exp(-0.5 * (d_va_tr / 1500.0) ** 2) * same_reg * (0.35 + 0.65 * w_ext_agro)
    W_e10 = 0.65 * w_b35 + 1.05 * w_c350 + 0.80 * w_c750 + 0.40 * w_c1500
    p_e10 = (W_e10 @ y_tr + 1.85 * prior_reg_va) / (W_e10.sum(axis=1) + 1.85)

    w_b_eff = (np.exp(-0.5 * (d_boun / 50.0) ** 2) * same_reg).sum(axis=1)
    pue_iso = (s_va == "Puebla") & ((w_eff + w_b_eff) < 0.25)
    p_e10_out = p_e10.copy()
    p_e10_out[tlax_va] = prior_reg_va[tlax_va] + gamma_reg_va[tlax_va] * (p_e10_out[tlax_va] - prior_reg_va[tlax_va])
    if np.any(pue_iso):
        p_e10_out[pue_iso] = 0.55 * p_e10_out[pue_iso] + 0.45 * preds["E08"][pue_iso]
    preds["E10"] = np.clip(p_e10_out, 0.5, 6.5)

    # E11: Two-Stage Residual Corrector with Full-Year 2025 (F6) + Open-Meteo 5km Daily & Micro-Topography (F7)
    same_reg_tr = (reg_tr[:, None] == reg_tr[None, :]).astype(float)
    w_tr_reg_600 = np.exp(-0.5 * (d_tr_tr / 600.0) ** 2) * same_reg_tr
    prior_reg_tr = np.array([mun_reg_mu.get(m, reg_mu.get(rk, global_mu)) for m, rk in zip(m_tr, reg_tr)])
    loo_reg_tr = np.array([
        (w_tr_reg_600[i] @ y_tr + 2.0 * prior_reg_tr[i]) / (w_tr_reg_600[i].sum() + 2.0)
        for i in range(len(tr_global))
    ])
    res_reg_tr = y_tr - loo_reg_tr

    p_e11_base = p_e10.copy()
    if len(hid_va) > 0:
        p_e11_base[hid_va] = 0.65 * p_e09[hid_va] + 0.35 * p_e10[hid_va]

    p_ext_corr = np.zeros(len(va_global), dtype=float)
    for st_name, st_cols, st_w in [
        ("Puebla", puebla_ext_cols, 0.42),
        ("Hidalgo", hidalgo_ext_cols, 0.18),
        ("Tlaxcala", tlax_ext_cols, 0.35),
    ]:
        st_tr_m = (s_tr == st_name)
        st_va_m = (s_va == st_name)
        if len(st_cols) > 0 and st_tr_m.sum() >= 10 and st_va_m.sum() > 0:
            X_st_tr = np.nan_to_num(X_full_ext.iloc[tr_global[st_tr_m]][st_cols].to_numpy(dtype=float), nan=0.0)
            X_st_va = np.nan_to_num(X_full_ext.iloc[va_global[st_va_m]][st_cols].to_numpy(dtype=float), nan=0.0)
            sc_st = RobustScaler().fit(X_st_tr)
            X_st_tr_s = sc_st.transform(X_st_tr)
            X_st_va_s = sc_st.transform(X_st_va)
            m_hub = HuberRegressor(alpha=12.0, epsilon=1.35, max_iter=500).fit(X_st_tr_s, res_reg_tr[st_tr_m])
            m_rdg = Ridge(alpha=28.0).fit(X_st_tr_s, res_reg_tr[st_tr_m])
            pred_corr = 0.50 * m_hub.predict(X_st_va_s) + 0.50 * m_rdg.predict(X_st_va_s)
            pred_corr = np.clip(pred_corr, -0.45, 0.45)
            gate_va = np.clip((w_eff[st_va_m] + w_b_eff[st_va_m]) / 0.8, 0.15, 1.0)
            p_ext_corr[st_va_m] = st_w * gate_va * pred_corr

    p_e11 = p_e11_base + p_ext_corr
    p_e11[tlax_va] = prior_reg_va[tlax_va] + gamma_reg_va[tlax_va] * (p_e11[tlax_va] - prior_reg_va[tlax_va])
    if np.any(pue_iso):
        p_e11[pue_iso] = 0.50 * p_e11[pue_iso] + 0.50 * preds["E08"][pue_iso]
    preds["E11"] = np.clip(p_e11, 0.5, 6.5)

    # E12: Master Adaptive Regime + Boundary + Full-Year 2025 + Open-Meteo Daily Ensemble
    res_prior_tr = y_tr - prior_reg_tr
    sel_g12 = CompactSelector(24)
    X_tr_g12 = sel_g12.fit_transform(X_full_ext.iloc[tr_global], pd.Series(res_prior_tr, index=X_full_ext.iloc[tr_global].index))
    X_va_g12 = sel_g12.transform(X_full_ext.iloc[va_global])
    sc_g12 = StandardScaler().fit(X_tr_g12)
    Z_tr_g12 = sc_g12.transform(X_tr_g12)
    Z_va_g12 = sc_g12.transform(X_va_g12)

    gpr_res = GaussianProcessRegressor(
        kernel=1.0 * Matern(length_scale=2.5, nu=2.5) + WhiteKernel(noise_level=0.20),
        alpha=0.15,
        normalize_y=False,
        random_state=SEED,
    ).fit(Z_tr_g12, res_prior_tr)
    cb_res = CatBoostRegressor(
        iterations=240,
        depth=4,
        learning_rate=0.035,
        l2_leaf_reg=10.0,
        loss_function="MAE",
        random_seed=SEED,
        verbose=0,
        allow_writing_files=False,
        thread_count=2,
    ).fit(Z_tr_g12, res_prior_tr)
    pred_spec_res = np.clip(0.55 * gpr_res.predict(Z_va_g12) + 0.45 * cb_res.predict(Z_va_g12), -0.55, 0.55)
    p_spec_regime = prior_reg_va + gamma_reg_va * pred_spec_res

    alpha_e12 = np.clip(0.76 + 0.18 * ((w_eff + w_b_eff) / (w_eff + w_b_eff + 0.8)), 0.76, 0.94)
    p_e12 = alpha_e12 * preds["E11"] + (1.0 - alpha_e12) * p_spec_regime
    if np.any(pue_iso):
        p_e12[pue_iso] = 0.60 * p_e12[pue_iso] + 0.40 * preds["E08"][pue_iso]
    preds["E12"] = np.clip(p_e12, 0.5, 6.5)

    return preds


def calibrate_conformal_intervals(
    y_true: np.ndarray,
    oof_pred: np.ndarray,
    states_train: np.ndarray,
    nominal: float = 0.90,
) -> dict[str, Any]:
    """Calibra intervalos conformales al 90% globales y escalados por estado a partir de residuos OOF."""
    residuals = np.abs(np.asarray(y_true) - np.asarray(oof_pred))
    n = len(residuals)
    q_level = min(1.0, np.ceil((n + 1) * nominal) / n)
    global_radius = float(np.quantile(residuals, q_level, method="higher"))

    state_radii = {}
    for s in np.unique(states_train):
        res_s = residuals[states_train == s]
        ns = len(res_s)
        qs = min(1.0, np.ceil((ns + 1) * nominal) / ns)
        r_s = float(np.quantile(res_s, qs, method="higher"))
        state_radii[s] = float(0.75 * r_s + 0.25 * global_radius)

    radii_vec = np.array([state_radii[s] for s in states_train])
    lo = oof_pred - radii_vec
    hi = oof_pred + radii_vec
    coverage = float(np.mean((y_true >= lo) & (y_true <= hi)))
    by_state_cov = {
        s: float(np.mean((y_true[states_train == s] >= lo[states_train == s]) & (y_true[states_train == s] <= hi[states_train == s])))
        for s in np.unique(states_train)
    }
    return {
        "nominal": nominal,
        "global_radius_t_ha": global_radius,
        "global_width_t_ha": 2.0 * global_radius,
        "state_radii_t_ha": state_radii,
        "mean_adaptive_width_t_ha": float(np.mean(hi - lo)),
        "empirical_coverage": coverage,
        "coverage_by_state": by_state_cov,
    }

