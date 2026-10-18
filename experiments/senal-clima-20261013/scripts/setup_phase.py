"""Copia insumos locales comprobados sin transformar ni entrenar."""
import sys
import shutil
from pathlib import Path
from importlib.metadata import version

PHASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE / 'src'))
from signalclima.common import ROOT, PROJECT, ID, TARGET, SCHEMES, CUTOFF, safe, save, read, digest, now
import pandas as pd
import geopandas as gpd
import numpy as np

if (ROOT / 'registry/copy-origins.json').exists():
    raise ValueError('Fase preparada; no sobrescribir')
for d in ['data/processed', 'data/external', 'registry', 'runs', 'docs', 'tests', 'controls']:
    (ROOT / d).mkdir(parents=True, exist_ok=True)
prior = PROJECT / 'experiments/hidrica-estres-20261009'
copies = []


def copy(src, target):
    target = safe(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ValueError('Copia ya existente')
    shutil.copy2(src, target)
    sha = digest(src)
    assert digest(target) == sha
    copies.append({'source': str(Path(src).resolve()), 'target': str(target), 'sha256': sha})


for name in ['C-activa', 'W00-artifacts']:
    base = prior / 'controls' / name
    for p in sorted(base.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            copy(p, ROOT / 'controls' / name / p.relative_to(base))
for name in ['parcels.parquet', 'satellite.parquet', 'external_nasa.parquet', 'nasa-cells.csv', 'nasa-quality.json', 'source-manifest.json']:
    copy(prior / 'data/processed' / name, ROOT / 'data/processed' / name)
for name in ['features_monthly_40_10.parquet', 'features_whittaker_40_10.parquet']:
    copy(prior / 'controls/C-activa/data/processed' / name, ROOT / 'data/processed' / name)
for p in sorted((prior / 'data/external').glob('nasa*.json')):
    copy(p, ROOT / 'data/external' / p.name)
for name in ['schemes.csv', 'scheme-validation.json', 'spectral-audit.json']:
    copy(prior / 'registry' / name, ROOT / 'registry' / ('previous-' + name if name == 'spectral-audit.json' else name))
copy(prior / 'scripts/offline_worker.py', ROOT / 'scripts/offline_worker.py')
copy(PROJECT / 'requirements.lock', ROOT / 'requirements.lock')
save(ROOT / 'registry/copy-origins.json', {'at': now(), 'copies': copies, 'all_verified': True}, exclusive=True)

protected = {Path(p) for p in read(prior / 'registry/protected-files.json') if Path(p).is_file()}
for base in [PROJECT / 'src', PROJECT / 'data', PROJECT / 'artifacts', PROJECT / 'Reto-Cebada', prior]:
    for p in base.rglob('*'):
        if p.is_file() and not any(v in p.parts for v in ['__pycache__', 'tmp', '.venv', 'env', 'vendor', '.pytest_cache']):
            protected.add(p)
save(ROOT / 'registry/protected-files.json', {str(p.resolve()): digest(p) for p in sorted(protected)}, exclusive=True)
master = gpd.read_parquet(ROOT / 'data/processed/parcels.parquet')
assert len(master) == 197 and master[ID].is_unique and master.crs is not None
assert master.geometry.is_valid.all() and not master.geometry.is_empty.any()
assert master[TARGET].notna().sum() == 138 and master[TARGET].isna().sum() == 59
assert np.isfinite(master.loc[master[TARGET].notna(), TARGET]).all()
schemes = pd.read_csv(ROOT / 'registry/schemes.csv')
assert digest(ROOT / 'registry/schemes.csv') == read(ROOT / 'registry/scheme-validation.json')['scheme_hash']
for scheme in SCHEMES:
    rows = schemes[schemes.scheme.eq(scheme)]
    assert len(rows) == 138 and rows[ID].is_unique
    assert set(rows[ID]) == set(master.loc[master[TARGET].notna(), ID])
save(ROOT / 'registry/population-check.json', {'passed': True, 'n': 197, 'labeled': 138, 'hidden': 59,
     'crs': str(master.crs), 'valid_geometry': True, 'schemes': SCHEMES, 'cutoff': CUTOFF})
runtime = {p: version(p) for p in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'geopandas', 'rasterio', 'joblib', 'pyproj', 'pyarrow', 'psutil', 'requests']}
save(ROOT / 'registry/preparation-receipt.json', {'at': now(), 'runtime': runtime, 'protected_files': len(protected),
     'training_started': False, 'passed': True})
save(ROOT / 'workspace.json', {'project_root': str(PROJECT), 'phase_root': str(ROOT), 'created': now()})
print('Fase aislada:', len(copies), 'copias; población y', len(protected), 'archivos protegidos verificados')
