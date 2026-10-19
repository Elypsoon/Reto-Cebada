"""Esquemas de validación (Estratificado PyR P5 + 3 Espaciales) y modelos R00-R08."""
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel
from sklearn.ensemble import ExtraTreesRegressor
from catboost import CatBoostRegressor

from agrocebada.modeling import (
    spatial_groups, metric, CompactSelector, make_pipeline, Candidate, baseline_predictions
)
from .common import ID, TARGET, SEED


RUN_CATALOG = {
    "B0": {
        "name": "B0_regional_mean",
        "title": "Media Estatal (Línea Base Regional)",
        "family": "baseline",
        "description": "Promedio simple del estado calculado exclusivamente en el subconjunto de entrenamiento."
    },
    "R00": {
        "name": "R00_control_gpr",
        "title": "Control GPR Oficial (Sin Coordenadas)",
        "family": "gpr",
        "description": "Configuración ganadora del modelo activo (whittaker_40_10 + nasa, GPR Matérn 2.5 k=10, geo=False) sin ruido de selección entre 81 candidatos."
    },
    "R01": {
        "name": "R01_gpr_geo",
        "title": "GPR Matérn 2.5 con Coordenadas UTM (Geo=True)",
        "family": "gpr_geo",
        "description": "Proceso Gaussiano Matérn 2.5 incorporando coordenadas UTM 14N (location_x, location_y) junto con predictores espectrales y NASA POWER."
    },
    "R02": {
        "name": "R02_catboost_geo",
        "title": "CatBoost Regularizado con Coordenadas UTM",
        "family": "catboost_geo",
        "description": "Árboles potenciados por gradiente (profundidad 3, L2=10, k=20) con coordenadas UTM 14N y variables espectrales/climáticas."
    },
    "R03": {
        "name": "R03_biweekly_contrast",
        "title": "Curvas Quincenales (14d) + Contraste Vecinal 1 km + Anomalía Histórica",
        "family": "biweekly_contrast",
        "description": "Reconstrucción espectral quincenal de 14 días (que recupera 161/197 parcelas en junio-julio), anomalías 2025 vs 2022-2024 y contraste espectral en radio de 1 km."
    },
    "R04": {
        "name": "R04_extratrees_geo",
        "title": "ExtraTrees Regularizado con Contexto Geográfico",
        "family": "extratrees_geo",
        "description": "Ensamble de árboles extremadamente aleatorizados (300 árboles, max_depth=6, min_samples_leaf=3) con selección compacta k=20 y coordenadas UTM."
    },
    "R05": {
        "name": "R05_spatial_kriging",
        "title": "Prior de Kriging Espacial Multiescala Intra-Estatal (PyR P5)",
        "family": "spatial_kriging",
        "description": "Interpolación gaussiana multiescala (600 m y 1,500 m) restringida al mismo estado con encogimiento empírico de Bayes hacia la media municipal/estatal."
    },
    "R06": {
        "name": "R06_spectral_geo_ensemble",
        "title": "Ensamble Multi-Familia Espectral-Geográfico + Escalamiento por Varianza Estatal (PyR P3)",
        "family": "ensemble_spectral",
        "description": "Combinación convexa de GPR-Geo, CatBoost-Geo, Biweekly-Contrast y ExtraTrees-Geo con estandarización por varianza estatal para mitigar la cuantización de Tlaxcala."
    },
    "R07": {
        "name": "R07_hybrid_kriging_spectral",
        "title": "Híbrido Kriging-Espectral 50/50 (Óptimo para Muestreo Estratificado 70/30)",
        "family": "hybrid_stratified",
        "description": "Fusión equitativa entre el Prior Espacial Multiescala (R05) y el Ensamble Espectral-Geográfico (R06), diseñada para el muestreo aleatorio estratificado 70/30."
    },
    "R08": {
        "name": "R08_adaptive_ead",
        "title": "Ensamble Adaptativo por Distancia al Vecino (EAD — Unificado Espacial + Estratificado)",
        "family": "adaptive_ensemble",
        "description": "Pondera dinámicamente entre el anclaje vecinal (R05) y la rama espectral-geográfica (R01 + R03 + R06) según la densidad efectiva de parcelas de entrenamiento a <600 m."
    }
}


def build_strata(states_arr, municipios_arr):
    """Construye los estratos Estado-Municipio respetando el tamaño mínimo por estrato (PyR P5)."""
    major_muns = {"Chignahuapan", "Calpulalpan", "Singuilucan", "Almoloya", "Cuautepec de Hinojosa"}
    strata = np.array([
        f"{s}__{m}" if m in major_muns else f"{s}__otros"
        for s, m in zip(states_arr, municipios_arr)
    ])
    strata = np.where(states_arr == "Tlaxcala", "Tlaxcala", strata)
    return strata


def build_validation_schemes(master_df, train_indices):
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


def fit_and_predict_all_runs(tr_global, va_global, y_tr, feature_bundle):
    """Ajusta B0 y R00..R08 estrictamente en tr_global y predice en va_global."""
    X_w40 = feature_bundle["X_w40"]
    X_w40_geo = feature_bundle["X_w40_geo"]
    X_r03 = feature_bundle["X_r03"]
    states_all = feature_bundle["states_all"]
    mun_all = feature_bundle["mun_all"]
    coords_all = feature_bundle["coords_all"]

    s_tr, s_va = states_all[tr_global], states_all[va_global]
    m_tr, m_va = mun_all[tr_global], mun_all[va_global]
    c_tr, c_va = coords_all[tr_global], coords_all[va_global]

    c_r00 = Candidate("whittaker_40_10", "gpr", 5, ("nasa",), False)
    c_cb = Candidate("whittaker_40_10", "catboost", 3, ("nasa",), False)

    preds = {}
    preds["B0"] = baseline_predictions(y_tr, s_tr, s_va)["regional_mean"]
    preds["R00"] = make_pipeline(c_r00).fit(X_w40.iloc[tr_global], y_tr).predict(X_w40.iloc[va_global])
    preds["R01"] = make_pipeline(c_r00).fit(X_w40_geo.iloc[tr_global], y_tr).predict(X_w40_geo.iloc[va_global])
    preds["R02"] = make_pipeline(c_cb).fit(X_w40_geo.iloc[tr_global], y_tr).predict(X_w40_geo.iloc[va_global])

    pipe_gpr12 = Pipeline([
        ("select", CompactSelector(12)),
        ("scale", StandardScaler()),
        ("model", GaussianProcessRegressor(
            kernel=Matern(length_scale=5.0, nu=2.5) + WhiteKernel(0.15),
            optimizer=None, normalize_y=True, random_state=SEED
        ))
    ])
    p_r03_gpr = pipe_gpr12.fit(X_r03.iloc[tr_global], y_tr).predict(X_r03.iloc[va_global])

    pipe_cb25 = Pipeline([
        ("select", CompactSelector(25)),
        ("scale", StandardScaler()),
        ("model", CatBoostRegressor(
            depth=3, iterations=260, learning_rate=0.03, l2_leaf_reg=8,
            loss_function="RMSE", random_seed=SEED, thread_count=2,
            verbose=False, allow_writing_files=False
        ))
    ])
    p_r03_cb = pipe_cb25.fit(X_r03.iloc[tr_global], y_tr).predict(X_r03.iloc[va_global])
    preds["R03"] = 0.55 * p_r03_gpr + 0.45 * p_r03_cb

    pipe_et = Pipeline([
        ("select", CompactSelector(20)),
        ("scale", StandardScaler()),
        ("model", ExtraTreesRegressor(
            n_estimators=300, max_depth=6, min_samples_leaf=3, random_state=SEED, n_jobs=2
        ))
    ])
    preds["R04"] = pipe_et.fit(X_w40_geo.iloc[tr_global], y_tr).predict(X_w40_geo.iloc[va_global])

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
    krig_va = np.array([
        (w_600[i] @ y_tr + 0.5 * (w_1500[i] @ y_tr) + 2.0 * prior_va[i])
        / (w_600[i].sum() + 0.5 * w_1500[i].sum() + 2.0)
        for i in range(len(va_global))
    ])
    preds["R05"] = krig_va

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
            optimizer=None, normalize_y=False, random_state=SEED
        ))
    ])
    p_z_gpr = mu_s_va + sd_s_va * pipe_z_gpr.fit(X_w40_geo.iloc[tr_global], z_tr).predict(X_w40_geo.iloc[va_global])

    preds["R06_raw"] = (
        0.35 * preds["R01"]
        + 0.25 * preds["R02"]
        + 0.20 * preds["R03"]
        + 0.10 * preds["R04"]
        + 0.10 * p_z_gpr
    )

    # Empirical Bayes intra-state variance shrinkage (PyR P3: accounts for quantization/noise floor)
    # Computed strictly on training fold (y_tr, s_tr)
    eb_gamma = {}
    for s in np.unique(s_tr):
        var_s = float(np.var(y_tr[s_tr == s]))
        eb_gamma[s] = float(np.clip((var_s - 0.10) / max(var_s, 1e-4), 0.25, 0.90))
    gamma_va = np.array([eb_gamma.get(s, 0.75) for s in s_va])

    preds["R06"] = mu_s_va + gamma_va * (preds["R06_raw"] - mu_s_va)

    raw_r07 = 0.50 * preds["R05"] + 0.50 * preds["R06_raw"]
    preds["R07"] = mu_s_va + gamma_va * (raw_r07 - mu_s_va)

    w_eff = w_600.sum(axis=1)
    alpha = 0.55 * (w_eff / (w_eff + 1.5))
    spectral_branch = 0.50 * preds["R01"] + 0.30 * preds["R03"] + 0.20 * preds["R06_raw"]
    raw_r08 = alpha * preds["R05"] + (1.0 - alpha) * spectral_branch
    preds["R08"] = mu_s_va + gamma_va * (raw_r08 - mu_s_va)
    del preds["R06_raw"]

    return preds


def calibrate_conformal_intervals(y_true, oof_pred, states_train, nominal=0.90):
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
        # Shrink slightly towards global radius for small-sample stability
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
