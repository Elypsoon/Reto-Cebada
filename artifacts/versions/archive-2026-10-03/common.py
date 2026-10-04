from pathlib import Path
import hashlib
import json
import platform
from importlib.metadata import version
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "Reto-Cebada" / "DataSet"
CHANGE = ROOT / "openspec/changes/prediccion-cebada-con-datos-verificados"
PROCESSED = ROOT / "data/processed"
EXTERNAL = ROOT / "data/external"
ARTIFACTS = ROOT / "artifacts"
CUTOFF = "2025-10-31"
START = "2025-04-01"
SEED = 2026
ID = "ID_POLIGONO"
TARGET = "RENDIMIENTO_T_HA"


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
    return {"python": platform.python_version(), **{p: version(p) for p in ["numpy", "pandas", "scikit-learn", "geopandas", "rasterio", "catboost", "streamlit"]}}


def code_hash():
    h = hashlib.sha256()
    for p in sorted((ROOT / "src/agrocebada").glob("*.py")):
        h.update(p.name.encode()); h.update(p.read_bytes())
    return h.hexdigest()
