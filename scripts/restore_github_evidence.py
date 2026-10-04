"""Restaura los registros experimentales originales sin cambiar sus hashes."""
from pathlib import Path
import argparse,json,gzip,hashlib
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
index=json.loads((root/'github-transport.json').read_text(encoding='utf-8'))
for item in index['files']:
    destination=(root/item['path']).resolve();compressed=(root/item['gzip_path']).resolve()
    if not destination.is_relative_to(root) or not compressed.is_relative_to(root):raise ValueError('Ruta fuera del checkout')
    h=hashlib.sha256()
    with gzip.open(compressed,'rb') as source:
        for block in iter(lambda:source.read(1024**2),b''):h.update(block)
    if h.hexdigest()!=item['sha256']:raise ValueError('Registro comprimido incompatible: '+item['path'])
    if args.check:continue
    existing=hashlib.sha256(destination.read_bytes()).hexdigest() if destination.exists() else None
    if existing==item['sha256']:continue
    if existing!=item['summary_sha256']:raise ValueError('Archivo modificado; no se sobrescribe: '+item['path'])
    temporary=destination.with_name(destination.name+'.restore-tmp')
    with gzip.open(compressed,'rb') as source,temporary.open('wb') as output:
        for block in iter(lambda:source.read(1024**2),b''):output.write(block)
    if hashlib.sha256(temporary.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Restauración incompatible')
    temporary.replace(destination)
print(('Verificados' if args.check else 'Restaurados')+f' {len(index["files"])} registros con sus hashes originales.')
