"""Descarga únicamente documentación y catálogos generales, sin datos del proyecto."""
from pathlib import Path
import sys
import json
PHASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE / 'src'))
from signalclima.common import ROOT, save, now
from signalclima.acquisition import Client, AcquisitionError

urls = {
 'chirps-daily-definition.txt': 'https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/readme.txt',
 'chirps-final-sat-index.html': 'https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/sat/',
 'sentinel-collection.json': 'https://stac.dataspace.copernicus.eu/v1/collections/sentinel-2-l2a',
 'sentinel-definition.html': 'https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html',
 'smn-stations.html': 'https://smn.conagua.gob.mx/es/?id=177%3Aqu&option=com_content&view=article',
 'era5-land.html': 'https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview',
 'scientific-skills.html': 'https://arxiv.org/abs/2609.00065',
}
client = Client()
results = {}
for name,url in urls.items():
    try:
        p = client.fetch(url, name, validator=(lambda p: json.loads(p.read_text(encoding='utf-8'))) if name.endswith('.json') else None)
        results[name] = {'status': 'downloaded', 'file': str(p), 'url': url}
        print(name, 'recuperado', flush=True)
    except AcquisitionError as e:
        results[name] = {'status': 'rejected', 'url': url, 'reason': str(e)}
        print(name, str(e), flush=True)
save(ROOT / 'registry/public-metadata.json', {'at': now(), 'project_data_transmitted': False, 'results': results})
