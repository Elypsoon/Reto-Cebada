"""Acceso público normal de Dataverse, versiones y verificaciones de originales."""
from pathlib import Path
import urllib.request
import urllib.error
import json
import time
from .common import ROOT, digest, save, read, now

BASE = 'https://data.cimmyt.org'
METADATA = BASE + '/api/datasets/:persistentId/?persistentId=hdl:11529/10548986'
FILES = ['1.-Farmer_Plot_Logbook_2012-2022_03.xlsx',
         '2.-Sowing_harvest_yields_2012-2022_02.xlsx', 'Spanish-English Glossary.xlsx']


def acquire():
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    path = raw / 'dataset-v6-metadata.json'
    if not path.exists():
        with urllib.request.urlopen(METADATA, timeout=45) as response:
            save(path, json.load(response))
    version = read(path)['data']['latestVersion']
    if (version['versionNumber'], version['versionMinorNumber']) != (6, 0):
        raise ValueError('Versión diferente de la verificada: revisar antes de adquirir')
    chosen = [f for f in version['files'] if f['dataFile']['filename'] in FILES]
    if len(chosen) != 3 or any(f.get('restricted') for f in chosen):
        raise ValueError('Acceso no público o inventario distinto; no intentar evadirlo')
    manifest = {'persistent_id': 'hdl:11529/10548986', 'version': '6.0', 'at': now(),
        'metadata_url': METADATA, 'metadata_sha256': digest(path), 'files': [],
        'purpose': 'Investigación local experimental no comercial; sin redistribución de originales',
        'terms_of_use': version.get('termsOfUse'), 'terms_of_access': version.get('termsOfAccess'),
        'published_barley_records': 968, 'audited_barley_records': None,
        'citation': 'Gardeazábal-Monsalve, A.; Ramirez Ortega, M. L.; Pacheco Rodríguez, G. M.; Garza Sánchez, E. (2024). Historical Agronomic Dataset - Insights from Mexico (2012 - 2022). CIMMYT, V6. https://hdl.handle.net/11529/10548986',
        'evidence': {'C01': 'https://hdl.handle.net/11529/10548986',
          'C02': 'https://www.nature.com/articles/s41597-025-06143-w',
          'C03': str(ROOT.parents[1] / 'docs/Reto Agrocebada Bases.md'),
          'C04': str(ROOT.parents[1] / 'experiments/prioridades-predictivas-20261006/docs/conclusions.md'),
          'C05': 'https://power.larc.nasa.gov/docs/services/api/temporal/daily/'}}
    save(ROOT / 'registry/sources.json', manifest)
    for item in chosen:
        file = item['dataFile']
        target = raw / file['filename']
        url = f"{BASE}/api/access/datafile/{file['id']}"
        if not target.exists():
            try:
                with urllib.request.urlopen(url, timeout=180) as response:
                    target.write_bytes(response.read())
            except urllib.error.HTTPError as error:
                save(ROOT / 'registry/access.json', {'status': 'pending_access' if error.code in (401, 403) else 'failed',
                     'file': file['filename'], 'http_status': error.code, 'at': now()})
                raise
        checksum = file['checksum']
        if target.stat().st_size != file['filesize'] or digest(target, checksum['type'].lower()) != checksum['value']:
            raise ValueError('Original incompleto o checksum incompatible: ' + target.name)
        manifest['files'].append({'filename': target.name, 'url': url, 'id': file['id'],
             'bytes': target.stat().st_size, 'sha256': digest(target), 'provider_checksum': checksum, 'acquired': True})
    save(ROOT / 'registry/sources.json', manifest)
    save(ROOT / 'registry/access.json', {'status': 'completed', 'public_api': True,
           'authentication_used': False, 'files_verified': 3, 'at': now()})
    print('CIMMYT V6: tres originales verificados contra sus checksums públicos')
    return manifest
