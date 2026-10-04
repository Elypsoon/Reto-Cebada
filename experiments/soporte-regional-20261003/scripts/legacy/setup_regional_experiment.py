"""Snapshot íntegro antes de editar la implementación experimental."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import os

ROOT = Path(__file__).resolve().parents[1]
VERSION = ROOT / 'artifacts/versions/selection-current-20261003'
EXPERIMENT = ROOT / 'experiments/regional-20261003'

def hashes(root):
    paths = []
    for folder in ['src', 'data/processed', 'docs', 'output/pdf']:
        paths.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.extend(p for p in (root/'artifacts').glob('*') if p.is_file())
    paths.extend(root/p for p in ['app.py','requirements.lock','pyproject.toml'])
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def copy_package(destination):
    destination.mkdir(parents=True, exist_ok=False)
    for folder in ['src','data/processed','docs','scripts','tests','.streamlit','output/pdf','openspec']:
        if (ROOT/folder).exists():
            shutil.copytree(ROOT/folder,destination/folder,ignore=shutil.ignore_patterns('__pycache__'))
    (destination/'artifacts').mkdir()
    for p in (ROOT/'artifacts').glob('*'):
        if p.is_file():shutil.copy2(p,destination/'artifacts'/p.name)
    for name in ['app.py','requirements.lock','pyproject.toml','README.md']:
        shutil.copy2(ROOT/name,destination/name)

if __name__ == '__main__':
    before = hashes(ROOT)
    copy_package(VERSION)
    env = dict(os.environ, PYTHONPATH=str(VERSION/'src'))
    subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),'-m','agrocebada.cli','verify'],cwd=VERSION,env=env,check=True)
    assert hashes(ROOT)==before
    (VERSION/'version-manifest.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    copy_package(EXPERIMENT)
    (EXPERIMENT/'active-manifest.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    (EXPERIMENT/'workspace.json').write_text(json.dumps({'active_root':str(ROOT),'snapshot':str(VERSION),'run_id':'regional-20261003'},indent=2),encoding='utf-8')
    print('Snapshot verificado y experimento:',EXPERIMENT)
