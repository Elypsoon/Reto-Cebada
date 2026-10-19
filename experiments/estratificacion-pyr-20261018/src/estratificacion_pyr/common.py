"""Constantes, rutas y utilidades criptográficas para la fase estratificacion-pyr-20261018."""
from pathlib import Path
import hashlib
import json
import platform
from importlib.metadata import version
import numpy as np

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


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    def default(v):
        if isinstance(v, np.generic):
            return v.item()
        if isinstance(v, Path):
            return str(v)
        raise TypeError(type(v).__name__)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=default), encoding="utf-8")


def dependencies():
    pkgs = ["numpy", "pandas", "scikit-learn", "geopandas", "rasterio", "catboost", "streamlit"]
    return {"python": platform.python_version(), **{p: version(p) for p in pkgs}}


def phase_code_hash():
    h = hashlib.sha256()
    for p in sorted((PHASE_ROOT / "src/estratificacion_pyr").glob("*.py")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()

