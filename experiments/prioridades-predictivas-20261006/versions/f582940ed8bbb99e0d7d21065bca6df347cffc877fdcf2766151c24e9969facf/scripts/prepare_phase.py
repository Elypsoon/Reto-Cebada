"""Preparación reproducible sin entrenamiento ni resultados externos nuevos."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import sys

PHASE = Path(__file__).resolve().parents[1]
PROJECT = PHASE.parents[1]
SUPPORT = PROJECT / 'experiments/soporte-regional-20261003'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def copy_verified(source, target, origins):
    if target.exists() and digest(source) != digest(target):
        raise ValueError(f'Destino distinto del origen: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(source, target)
    origins[target.relative_to(PHASE).as_posix()] = {
        'source': str(source), 'sha256': digest(source), 'verified_copy': digest(target) == digest(source)
    }


def copy_code(source, destination, origins):
    for path in sorted((source / 'src/agrocebada').glob('*.py')):
        copy_verified(path, destination / 'src/agrocebada' / path.name, origins)
    for name in ['requirements.lock', 'pyproject.toml']:
        copy_verified(source / name, destination / name, origins)


def main():
    receipt = PHASE / 'registry/preparation-receipt.json'
    if receipt.exists():
        raise ValueError('Preparación ya realizada: verificar recibo, no sobrescribir')
    origins = {}
    copy_code(SUPPORT, PHASE, origins)
    # Tablas originales, auditorías y diccionarios; no artefactos predictivos ni entornos.
    for folder in ['data/processed', 'data/external']:
        for path in sorted((SUPPORT / folder).glob('*')):
            if path.is_file():
                copy_verified(path, PHASE / folder / path.name, origins)
    save(PHASE / 'workspace.json', {'active_root': str(PROJECT), 'run_id': PHASE.name,
         'snapshot': str(PROJECT / 'artifacts/versions/selection-current-20261003'),
         'legacy_root': str(SUPPORT), 'training_started': False})
    for folder in ['artifacts', 'runs', 'tests', 'docs', 'registry', 'controls']:
        (PHASE / folder).mkdir(exist_ok=True)
    copy_verified(SUPPORT / 'registry/schemes.csv', PHASE / 'registry/schemes.csv', origins)
    copy_verified(SUPPORT / 'registry/scheme-validation.json', PHASE / 'registry/scheme-validation-origin.json', origins)
    source_manifest = {}
    for root, prefix in [(PROJECT, 'activa'), (SUPPORT, 'soporte')]:
        for folder in ['src', 'data/processed', 'data/external']:
            for path in sorted((root / folder).rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts:
                    source_manifest[f'{prefix}/{path.relative_to(root).as_posix()}'] = {
                        'source': str(path), 'sha256': digest(path)}
        for name in ['requirements.lock', 'pyproject.toml']:
            path = root / name
            source_manifest[f'{prefix}/{name}'] = {'source': str(path), 'sha256': digest(path)}
    save(PHASE / 'registry/source-integrity.json', source_manifest)
    save(PHASE / 'registry/copy-origins.json', origins)
    code = {path.relative_to(PHASE).as_posix(): digest(path)
            for path in sorted((PHASE / 'src').rglob('*.py'))}
    code_version = hashlib.sha256(json.dumps(code, sort_keys=True).encode()).hexdigest()
    version = PHASE / 'versions' / code_version
    for name in code:
        path = version / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PHASE / name, path)
    for name in ['pyproject.toml', 'requirements.lock']:
        shutil.copy2(PHASE / name, version / name)
    save(version / 'manifest.json', {path.relative_to(version).as_posix(): digest(path)
         for path in sorted(version.rglob('*')) if path.is_file()})
    save(receipt, {'phase_id': PHASE.name, 'created_at': datetime.now(timezone.utc).isoformat(),
         'source': str(SUPPORT), 'source_version': code_version, 'copies': len(origins),
         'copy_manifest_sha256': digest(PHASE / 'registry/copy-origins.json'),
         'source_integrity_sha256': digest(PHASE / 'registry/source-integrity.json'),
         'training_started': False, 'new_metrics': None,
         'excluded': ['entornos', 'temporales', 'resultados históricos como ejecuciones nuevas']})
    print(json.dumps({'copied_files': len(origins), 'version': code_version, 'training_started': False}))


if __name__ == '__main__':
    main()
