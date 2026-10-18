"""Metadatos públicos; sin credenciales ni aceptación de licencias interactivas."""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'AgroCebada-research'}), timeout=30) as stream:
        return json.load(stream)


results = {}
for name in ['tabicl', 'tabpfn']:
    data = get(f'https://pypi.org/pypi/{name}/json')
    results[name] = {'version': data['info']['version'], 'requires_dist': data['info']['requires_dist'],
                     'official_home': data['info']['project_urls']}
for repository in ['soda-inria/tabicl', 'PriorLabs/TabPFN']:
    data = get(f'https://api.github.com/repos/{repository}/commits/main')
    results[repository] = {'revision': data['sha']}
for repository in ['jingang/TabICL', 'jingang/TabICL-v2', 'Prior-Labs/tabpfn_3']:
    try:
        data = get(f'https://huggingface.co/api/models/{repository}?blobs=true')
        results[repository] = {k: data.get(k) for k in ['id', 'sha', 'gated', 'cardData', 'siblings']}
    except urllib.error.HTTPError as error:
        results[repository] = {'http_status': error.code}
folder = ROOT/'optional'
folder.mkdir(exist_ok=True)
(folder/'source-inspection.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
for key, value in results.items():
    print(key, json.dumps({k: value[k] for k in ['version', 'requires_dist', 'revision', 'sha', 'gated', 'http_status'] if k in value}))
    for item in value.get('siblings', []):
        if any(suffix in item['rfilename'] for suffix in ['regressor', '202605', 'LICENSE', 'safetensors']):
            print(item)
