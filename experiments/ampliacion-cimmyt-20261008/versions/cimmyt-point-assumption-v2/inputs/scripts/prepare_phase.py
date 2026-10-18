"""Copia aislada y verificable; no entrena ni modifica versiones históricas."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import importlib.metadata as metadata

PHASE = Path(__file__).resolve().parents[1]
PROJECT = PHASE.parents[1]
PREVIOUS = PROJECT / 'experiments/prioridades-predictivas-20261006'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    receipt = PHASE / 'registry/preparation.json'
    if receipt.exists():
        raise ValueError('Fase ya preparada: verificar recibo, no sobrescribir')
    protected, copies = {}, {}
    for base, folders in [(PROJECT, ['src', 'artifacts', 'data/processed', 'data/external']),
                          (PREVIOUS, ['src', 'scripts', 'registry', 'runs', 'controls', 'optional', 'versions', 'data', 'docs'])]:
        for folder in folders:
            for path in sorted((base / folder).rglob('*')):
                if path.is_file() and not set(path.parts).intersection({'__pycache__', '.venv', 'env', 'tmp'}):
                    protected[str(path)] = digest(path)
        for name in ['requirements.lock', 'pyproject.toml', 'workspace.json']:
            path = base / name
            if path.exists():
                protected[str(path)] = digest(path)
    save(PHASE / 'registry/protected-files.json', protected)

    def copy(source, target):
        if target.exists():
            raise ValueError('Destino ya existe: ' + str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copies[target.relative_to(PHASE).as_posix()] = {'source': str(source), 'sha256': digest(source)}
        assert digest(target) == digest(source)

    for path in (PREVIOUS / 'src/agrocebada').glob('*.py'):
        copy(path, PHASE / 'src/agrocebada' / path.name)
    for folder in ['data/processed', 'data/external']:
        for path in (PREVIOUS / folder).glob('*'):
            if path.is_file():
                copy(path, PHASE / folder / path.name)
    for name in ['pyproject.toml', 'requirements.lock']:
        copy(PREVIOUS / name, PHASE / name)
    copy(PREVIOUS / 'registry/schemes.csv', PHASE / 'registry/schemes.csv')
    copy(PREVIOUS / 'scripts/offline_worker.py', PHASE / 'scripts/offline_worker.py')
    source = PREVIOUS / 'controls/C-activa'
    destination = PHASE / 'controls/C-activa'
    for folder in ['src', 'data/processed', 'data/external', 'provenance']:
        for path in (source / folder).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                copy(path, destination / path.relative_to(source))
    for name in ['requirements.lock', 'pyproject.toml']:
        copy(source / name, destination / name)
    for path in (PREVIOUS / 'runs/P00-C-activa/artifacts').glob('*'):
        if path.suffix in {'.csv', '.joblib'} or path.name.startswith('metrics-'):
            copy(path, PHASE / 'runs/A00/artifacts' / path.name)
    for folder in ['data/raw', 'data/processed', 'docs', 'tests', 'registry', 'runs', 'src/cimmyt', 'vendor']:
        (PHASE / folder).mkdir(parents=True, exist_ok=True)
    save(PHASE / 'workspace.json', {'active_root': str(PROJECT), 'run_id': PHASE.name,
                                  'legacy_root': str(PREVIOUS), 'training_started': False})
    save(PHASE / 'registry/copy-origins.json', copies)
    save(receipt, {'created_at': datetime.now(timezone.utc).isoformat(), 'copies': len(copies),
                   'protected_files': len(protected), 'training_started': False,
                   'runtime': {n: metadata.version(n) for n in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'geopandas', 'pyproj', 'pyarrow', 'joblib', 'psutil']}})
    print(json.dumps({'copies': len(copies), 'protected_files': len(protected), 'training_started': False}))


if __name__ == '__main__':
    main()
