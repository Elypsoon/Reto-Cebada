"""Verifica originales y controles históricos sin escribir en sus raíces."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from agrocebada.common import sha256
from agrocebada.tracking import read,atomic_json
workspace=read(root/'workspace.json');active=Path(workspace['active_root']);legacy=Path(workspace['legacy_root'])
originals=read(root/'data/processed/source-manifest.json')
for entry in originals:
    source=active/entry['path']
    assert source.is_file() and sha256(source)==entry['sha256'],str(source)
for name,path in [('active-manifest.json',active),('baseline-source-manifest.json',legacy)]:
    assert all((path/relative).is_file() and sha256(path/relative)==expected for relative,expected in read(root/name).items())
atomic_json(root/'registry/source-integrity.json',{'verified_original_files':len(originals),'all_original_hashes_match':True,'active_matches_initial_manifest':True,'H01_matches_initial_manifest':True})
print('Originales y controles verificados:',len(originals),flush=True)
