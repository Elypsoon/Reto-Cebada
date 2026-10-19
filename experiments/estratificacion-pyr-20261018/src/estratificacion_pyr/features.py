"""Ingeniería de variables quincenales (14 días), anomalías multianuales y contraste vecinal 1 km."""
import numpy as np
import pandas as pd
from .common import ID, START, CUTOFF


def build_biweekly_and_historical_features(master_df, sat_df, cloud_max=30):
    """Construye curvas quincenales de 14 días para 2025 y anomalías respecto a 2022-2024."""
    pids = master_df[ID].tolist()
    out = pd.DataFrame(index=pd.Index(pids, name=ID))

    s25 = sat_df[sat_df.date.between(START, CUTOFF) & sat_df.porcentaje_nubosidad.le(cloud_max)].copy()
    s25["biweek"] = ((s25.date - pd.Timestamp(START)).dt.days // 14).clip(0, 14)

    sensor_specs = [
        ("Sentinel-2", "s2", ["ndvi_promedio", "evi_promedio", "ndwi_promedio"]),
        ("Planet", "pl", ["ndvi_promedio", "evi_promedio", "msavi_promedio"]),
        ("Landsat", "ls", ["vi6t_promedio"]),
    ]

    for sensor, prefix, cols in sensor_specs:
        sub = s25[s25.sensor == sensor]
        for col in cols:
            ix_name = col.replace("_promedio", "")
            piv = sub.pivot_table(index=ID, columns="biweek", values=col, aggfunc="median").reindex(pids)
            piv_interp = piv.interpolate(axis=1, limit=2, limit_direction="both")

            out[f"{prefix}_{ix_name}_bw_early"] = piv_interp.loc[:, piv_interp.columns.isin([0, 1, 2, 3])].mean(axis=1)
            out[f"{prefix}_{ix_name}_bw_mid"] = piv_interp.loc[:, piv_interp.columns.isin([4, 5, 6, 7])].mean(axis=1)
            out[f"{prefix}_{ix_name}_bw_grain"] = piv_interp.loc[:, piv_interp.columns.isin([8, 9, 10, 11])].mean(axis=1)
            out[f"{prefix}_{ix_name}_bw_late"] = piv_interp.loc[:, piv_interp.columns.isin([12, 13, 14])].mean(axis=1)
            out[f"{prefix}_{ix_name}_bw_max"] = piv_interp.max(axis=1)
            out[f"{prefix}_{ix_name}_bw_min"] = piv_interp.min(axis=1)
            out[f"{prefix}_{ix_name}_bw_amp"] = out[f"{prefix}_{ix_name}_bw_max"] - out[f"{prefix}_{ix_name}_bw_min"]
            out[f"{prefix}_{ix_name}_bw_auc"] = piv_interp.mean(axis=1)
            out[f"{prefix}_{ix_name}_bw_repro_gain"] = out[f"{prefix}_{ix_name}_bw_mid"] - out[f"{prefix}_{ix_name}_bw_early"]
            out[f"{prefix}_{ix_name}_bw_senescence_drop"] = out[f"{prefix}_{ix_name}_bw_grain"] - out[f"{prefix}_{ix_name}_bw_mid"]

    shist = sat_df[
        sat_df.date.dt.year.isin([2022, 2023, 2024])
        & sat_df.date.dt.month.between(4, 10)
        & sat_df.porcentaje_nubosidad.le(cloud_max)
    ].copy()
    shist["year"] = shist.date.dt.year

    for sensor, prefix, col in [("Sentinel-2", "s2", "ndvi_promedio"), ("Planet", "pl", "ndvi_promedio")]:
        sub_h = shist[shist.sensor == sensor]
        if len(sub_h) == 0:
            continue
        yr_max = sub_h.groupby([ID, "year"])[col].quantile(0.90).unstack("year").reindex(pids)
        yr_mean = sub_h.groupby([ID, "year"])[col].median().unstack("year").reindex(pids)
        out[f"{prefix}_hist_q90_mean"] = yr_max.mean(axis=1)
        out[f"{prefix}_hist_q90_max"] = yr_max.max(axis=1)
        out[f"{prefix}_hist_median"] = yr_mean.mean(axis=1)
        out[f"{prefix}_anom_peak_vs_hist"] = out[f"{prefix}_ndvi_bw_max"] - out[f"{prefix}_hist_q90_mean"]
        out[f"{prefix}_anom_auc_vs_hist"] = out[f"{prefix}_ndvi_bw_auc"] - out[f"{prefix}_hist_median"]

    return out


def build_spatial_contrast_features(X_base, location_df, bandwidth_m=1000.0):
    """Calcula el contraste espectral y topográfico respecto al vecindario local (sin usar etiquetas y)."""
    coords = location_df[["location_x", "location_y"]].to_numpy()
    dists = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(axis=2))
    W = np.exp(-0.5 * (dists / bandwidth_m) ** 2)
    np.fill_diagonal(W, 0.0)
    W_norm = W / np.maximum(W.sum(axis=1, keepdims=True), 1e-8)

    candidate_cols = [
        "s2_ndvi_peak", "s2_ndvi_auc", "s2_evi_middle", "s2_ndwi_middle",
        "planet_ndvi_peak", "planet_msavi_middle", "landsat_vi6t_middle",
        "elevation", "slope", "log_area"
    ]
    cols = [c for c in candidate_cols if c in X_base.columns]
    out = pd.DataFrame(index=X_base.index)
    for c in cols:
        vals = X_base[c].fillna(X_base[c].median()).to_numpy()
        local_avg = W_norm @ vals
        out[f"{c}_diff_local1km"] = vals - local_avg

    out["parcel_density_1km"] = (dists < 1000.0).sum(axis=1) - 1
    out["parcel_density_2km"] = (dists < 2000.0).sum(axis=1) - 1
    return out

