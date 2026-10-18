from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT.parents[1]
ID = 'ID_POLIGONO'
TARGET = 'RENDIMIENTO_T_HA'
SCHEMES = ['principal-5', 'balanceado-4', 'rotado-45-5']
WINDOWS = {'early': (4,5), 'middle': (6,7), 'late': (8,10)}
START, CUTOFF = '2025-04-01', '2025-10-31'

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def save(path, obj):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Destino fuera de la fase aislada')
    path.parent.mkdir(parents=True, exist_ok=True)
    def default(x):
        if isinstance(x,np.generic): return x.item()
        if isinstance(x,Path): return str(x)
        raise TypeError(type(x).__name__)
    data = json.dumps(obj,ensure_ascii=False,indent=2,default=default,allow_nan=False)
    temporary = path.with_suffix(path.suffix+'.pending')
    temporary.write_text(data,encoding='utf-8')
    temporary.replace(path)

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))
