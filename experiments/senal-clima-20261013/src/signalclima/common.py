from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from importlib.metadata import version

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT.parents[1]
ID, TARGET = 'ID_POLIGONO', 'RENDIMIENTO_T_HA'
START, CUTOFF = '2025-04-01', '2025-10-31'
WINDOWS = {'early': (4, 5), 'middle': (6, 7), 'late': (8, 10)}
SCHEMES = ['principal-5', 'balanceado-4', 'rotado-45-5']


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe(path):
    p = Path(path).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError('Destino fuera de la fase')
    return p


def save(path, value, exclusive=False):
    p = safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and p.exists():
        raise ValueError('No sobrescribir un recibo existente')
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False,
                      default=lambda v: v.item() if hasattr(v, 'item') else str(v))
    temp = p.with_suffix(p.suffix + '.new')
    temp.write_text(text, encoding='utf-8')
    temp.replace(p)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def runtime():
    return {name:version(name) for name in ['numpy','pandas','scipy','scikit-learn','geopandas','rasterio','joblib','pyproj','pyarrow','psutil','requests','threadpoolctl','catboost']}
