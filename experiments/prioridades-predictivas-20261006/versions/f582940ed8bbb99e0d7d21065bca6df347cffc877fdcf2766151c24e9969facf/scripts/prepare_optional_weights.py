"""Un checkpoint por generación, revisión pública y hash verificado antes de usarlo."""
import json
import urllib.request
from pathlib import Path
from prepare_phase import PHASE, digest, save

sources = json.loads((PHASE/'optional/source-inspection.json').read_text(encoding='utf-8'))
definitions = [('tabicl-v2', 'jingang/TabICL', 'tabicl-regressor-v2-20260212.ckpt', 'tabicl', '2.2.0'),
               ('tabpfn-3', 'Prior-Labs/tabpfn_3', 'tabpfn-v3-regressor-v3_default.ckpt', 'tabpfn', '9.1.0')]


def download(url, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return
    partial = destination.with_suffix(destination.suffix+'.partial')
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'AgroCebada-research'}), timeout=60) as stream:
        with partial.open('wb') as output:
            while block := stream.read(1024*1024):
                output.write(block)
    partial.replace(destination)


for name, repository, checkpoint, package, package_version in definitions:
    metadata = sources[repository]
    folder = PHASE/'optional'/name
    folder.mkdir(parents=True, exist_ok=True)
    revision = metadata['sha']
    weight_info = next(f for f in metadata['siblings'] if f['rfilename'] == checkpoint)
    if metadata.get('gated'):
        save(folder/'preflight.json', {'available':False,'reason':'Acceso requiere aceptación interactiva no resuelta.'})
        continue
    try:
        download(f'https://huggingface.co/{repository}/resolve/{revision}/{checkpoint}', folder/checkpoint)
        expected = weight_info['lfs']['sha256']
        if digest(folder/checkpoint) != expected:
            raise ValueError('Hash de checkpoint distinto del publicado')
        license_file = next((f['rfilename'] for f in metadata['siblings'] if f['rfilename'].lower() in ['license', 'license.md', 'license.txt']), None)
        if license_file:
            download(f'https://huggingface.co/{repository}/resolve/{revision}/{license_file}', folder/'LICENSE')
        elif name == 'tabicl-v2':
            code_revision = sources['soda-inria/tabicl']['revision']
            download(f'https://raw.githubusercontent.com/soda-inria/tabicl/{code_revision}/LICENSE', folder/'LICENSE')
        else:
            raise ValueError('Condiciones de pesos no localizables')
        save(folder/'manifest.json', {'model':name, 'repository':repository,'revision':revision,
             'checkpoint':checkpoint,'sha256':expected,'bytes':weight_info['size'],
             'license_sha256':digest(folder/'LICENSE'),'package':package,'package_version':package_version,
             'code_repository_revision':sources['soda-inria/tabicl' if name == 'tabicl-v2' else 'PriorLabs/TabPFN']['revision'],
             'purpose':'Evaluación local experimental; sin activación ni entrega comercial.',
             'parameters':{'device':'cpu','n_estimators':8,'random_state':2026},'threads':2})
        print(name, 'checkpoint verificado', expected, flush=True)
    except Exception as error:
        save(folder/'preflight.json', {'available':False,'reason':str(error), 'repository':repository,
             'revision':revision,'checkpoint':checkpoint,'generation_substituted':False})
        print(name, 'ausente:', repr(error), flush=True)
