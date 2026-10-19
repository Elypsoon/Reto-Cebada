"""Constantes, rutas y utilidades criptográficas y estadísticas para la fase fisiologia-siniestros-20261018."""
from __future__ import annotations

import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PHASE_ROOT = Path(__file__).resolve().parents[2]
ROOT = PHASE_ROOT.parents[1]
PROCESSED = ROOT / "data/processed"
ARTIFACTS = ROOT / "artifacts"
DATASET = ROOT / "DataSet"

DOCS = PHASE_ROOT / "docs"
REGISTRY = PHASE_ROOT / "registry"
RUNS = PHASE_ROOT / "runs"

ID = "ID_POLIGONO"
TARGET = "RENDIMIENTO_T_HA"
SEED = 2026
START = "2025-04-01"
CUTOFF = "2025-10-31"


def sha256(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path | str, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    def default(v: Any) -> Any:
        if isinstance(v, np.generic):
            return v.item()
        if isinstance(v, Path):
            return str(v)
        raise TypeError(type(v).__name__)

    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=default), encoding="utf-8")


def dependencies() -> dict[str, Any]:
    pkgs = ["numpy", "pandas", "scikit-learn", "geopandas", "rasterio", "catboost", "streamlit"]
    return {"python": platform.python_version(), **{p: version(p) for p in pkgs}}


def phase_code_hash() -> str:
    h = hashlib.sha256()
    for p in sorted((PHASE_ROOT / "src/fisiologia_siniestros").glob("*.py")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def metric(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)) if len(y_true) >= 2 else float("nan"),
    }


def paired_comparison(
    y_true: np.ndarray,
    pred_candidate: np.ndarray,
    pred_control: np.ndarray,
    folds: np.ndarray,
    seed: int = SEED,
    n_boot: int = 2000,
) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=float)
    pred_candidate = np.asarray(pred_candidate, dtype=float)
    pred_control = np.asarray(pred_control, dtype=float)
    folds = np.asarray(folds)

    cand_m = metric(y_true, pred_candidate)
    ctrl_m = metric(y_true, pred_control)
    delta_rmse = cand_m["rmse"] - ctrl_m["rmse"]
    delta_mae = cand_m["mae"] - ctrl_m["mae"]
    delta_r2 = cand_m["r2"] - ctrl_m["r2"]

    loss_diff = (y_true - pred_candidate) ** 2 - (y_true - pred_control) ** 2
    abs_diff = np.abs(y_true - pred_candidate) - np.abs(y_true - pred_control)

    rng = np.random.default_rng(seed)
    n = len(y_true)
    boot_d_rmse = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        rmse_c = np.sqrt(np.mean((y_true[idx] - pred_candidate[idx]) ** 2))
        rmse_0 = np.sqrt(np.mean((y_true[idx] - pred_control[idx]) ** 2))
        boot_d_rmse[b] = rmse_c - rmse_0

    ci95 = [float(np.percentile(boot_d_rmse, 2.5)), float(np.percentile(boot_d_rmse, 97.5))]

    signs = rng.choice([-1.0, 1.0], size=(n_boot, n))
    perm_means = (signs * loss_diff[None, :]).mean(axis=1)
    obs_mean = float(loss_diff.mean())
    p_perm_two_sided = float(np.mean(np.abs(perm_means) >= abs(obs_mean)))
    p_perm_better = float(np.mean(perm_means <= obs_mean))

    fold_deltas = {}
    unique_folds = sorted(pd.unique(folds))
    folds_improved = 0
    for f in unique_folds:
        m = folds == f
        d_f = metric(y_true[m], pred_candidate[m])["rmse"] - metric(y_true[m], pred_control[m])["rmse"]
        fold_deltas[str(f)] = float(d_f)
        if d_f < 0:
            folds_improved += 1

    return {
        "candidate": cand_m,
        "control": ctrl_m,
        "delta_rmse": float(delta_rmse),
        "delta_mae": float(delta_mae),
        "delta_r2": float(delta_r2),
        "rmse_diff_ci95": ci95,
        "p_perm_two_sided": p_perm_two_sided,
        "p_perm_one_sided_better": p_perm_better,
        "mean_loss_diff": obs_mean,
        "mean_abs_diff": float(abs_diff.mean()),
        "folds_improved": int(folds_improved),
        "total_folds": int(len(unique_folds)),
        "fold_deltas": fold_deltas,
    }

