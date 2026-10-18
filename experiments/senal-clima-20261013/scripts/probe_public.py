"""Catálogos y documentación oficiales: no consulta rendimientos."""
from pathlib import Path
import sys
import json
import math
from urllib.parse import urlencode
PHASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE / 'src'))
from signalclima.common import ROOT, save, now
from signalclima.acquisition import Client, AcquisitionError
import geopandas as gpd

client = Client()
master = gpd.read_parquet(ROOT / 'data/processed/parcels.parquet').drop(columns=['RENDIMIENTO_T_HA'])
bounds = master.to_crs(4326).total_bounds
# The public catalogue receives a coarse regional rectangle, not parcel IDs/boundaries.
bbox = [math.floor(v*100)/100 if i<2 else math.ceil(v*100)/100 for i,v in enumerate(bounds)]
query = urlencode({'collections': 'sentinel-2-l2a', 'bbox': ','.join(map(str,bbox)),
                   'datetime': '2025-04-01T00:00:00Z/2025-10-31T23:59:59Z', 'limit': 100})
urls = {
 'chirps-daily-definition.txt': 'https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/readme.txt',
 'chirps-final-sat-index.html': 'https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/sat/',
 'sentinel-collection.json': 'https://stac.dataspace.copernicus.eu/v1/collections/sentinel-2-l2a',
 'sentinel-scenes-01.json': 'https://stac.dataspace.copernicus.eu/v1/search?' + query,
 'sentinel-definition.html': 'https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html',
 'smn-stations.html': 'https://smn.conagua.gob.mx/es/?id=177%3Aqu&option=com_content&view=article',
 'era5-land.html': 'https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview',
 'scientific-skills.html': 'https://arxiv.org/abs/2609.00065',
}
results = {}
for name,url in urls.items():
    try:
        p = client.fetch(url, name, validator=(lambda p: json.loads(p.read_text(encoding='utf-8'))) if name.endswith('.json') else None)
        results[name] = {'status': 'downloaded', 'file': str(p), 'url': url}
        if name == 'sentinel-scenes-01.json':
            obj = json.loads(p.read_text(encoding='utf-8'))
            results[name].update(scenes=len(obj.get('features',[])), next_pages=[x['href'] for x in obj.get('links',[]) if x.get('rel')=='next'])
            print('Sentinel catalogue:',len(obj.get('features',[])),'scenes')
            for item in obj.get('features',[])[:1]:
                print('Asset keys:', list(item.get('assets',{})))
                print('Acquisition properties:', {k:v for k,v in item.get('properties',{}).items() if k in ['datetime','eo:cloud_cover','s2:processing_baseline','processing:version']})
                print('Band asset links:', {k:v.get('href') for k,v in item.get('assets',{}).items() if any(x in k.upper() for x in ['B8A','B11','SCL'])})
        print(name, 'recuperado', flush=True)
    except AcquisitionError as e:
        results[name] = {'status': 'rejected', 'url': url, 'reason': str(e)}
        print(name, str(e), flush=True)
save(ROOT / 'registry/public-probe.json', {'at': now(), 'labels_used': False, 'results': results})
