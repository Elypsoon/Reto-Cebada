"""Aislamiento de la fase; nunca sobrescribe el control ni la versión activa."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

PHASE = Path(__file__).resolve().parents[1]
ACTIVE = PHASE.parents[1]
SOURCE = ACTIVE / 'experiments/regional-20261003'

def hashes(root):
    files = []
    for folder in ['src', 'data/processed', 'docs', 'output/pdf']:
        files.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.extend(p for p in (root/'artifacts').glob('*') if p.is_file())
    files.extend(root/p for p in ['app.py', 'requirements.lock', 'pyproject.toml'])
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}

if __name__ == '__main__':
    before = hashes(ACTIVE)
    env = dict(os.environ, PYTHONPATH=str(ACTIVE/'src'), PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([str(ACTIVE/'.venv/Scripts/python.exe'), '-m', 'agrocebada.cli', 'verify'], cwd=ACTIVE, env=env, check=True)
    for folder in ['src','data/processed','data/external','docs','tests','.streamlit','openspec','artifacts']:
        shutil.copytree(SOURCE/folder, PHASE/folder, ignore=shutil.ignore_patterns('__pycache__'), dirs_exist_ok=False)
    for name in ['app.py','requirements.lock','pyproject.toml','README.md']:
        shutil.copy2(SOURCE/name, PHASE/name)
    (PHASE/'scripts/legacy').mkdir()
    for path in (SOURCE/'scripts').glob('*.py'):
        shutil.copy2(path, PHASE/'scripts/legacy'/path.name)
    (PHASE/'active-manifest.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    (PHASE/'workspace.json').write_text(json.dumps({'active_root':str(ACTIVE),'snapshot':str(ACTIVE/'artifacts/versions/selection-current-20261003'),'legacy_root':str(SOURCE),'run_id':PHASE.name}, indent=2), encoding='utf-8')
    (PHASE/'baseline-source-manifest.json').write_text(json.dumps(hashes(SOURCE), indent=2), encoding='utf-8')
    assert hashes(ACTIVE) == before
    print('Aislamiento y reproducción activa verificados:', PHASE)
