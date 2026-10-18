"""Inspección local de documentación auxiliar y disponibilidad de acceso, sin credenciales."""
from pathlib import Path
import os
import sys
import re
from html.parser import HTMLParser
PHASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PHASE/'src'))
from signalclima.common import ROOT,save,digest,now
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href','')
            if any(s in href.lower() for s in ['estacion','climat','catalog','csv','xlsx','2025']):self.links.append(href)
page=ROOT/'data/external/access/smn-stations.html';raw=page.read_bytes()
match=re.search(br'charset\s*=\s*["\x27]?([a-zA-Z0-9_-]+)',raw[:10000],re.I)
encoding=match.group(1).decode('ascii') if match else 'utf-8'
decoded=raw.decode(encoding,errors='replace');parser=Links();parser.feed(decoded)
configured=Path.home().joinpath('.cdsapirc').is_file() or bool(os.environ.get('CDSAPI_URL') and os.environ.get('CDSAPI_KEY'))
value={'at':now(),'primary_predictors_changed':False,'project_data_transmitted':False,'credentials_logged':False,
 'SMN':{'metadata_file':str(page.relative_to(ROOT)),'metadata_hash':digest(page),'declared_encoding':encoding,'encoding_mismatch':'\ufffd' in decoded,'candidate_links':[s for s in dict.fromkeys(parser.links) if '\ufffd' not in s],
        'series_2025_downloaded':False,'coverage_verified':False,'status':'metadata_only; station-series audit remains pending'},
 'ERA5-Land':{'metadata_file':'data/external/access/era5-land.html','metadata_hash':digest(ROOT/'data/external/access/era5-land.html'),
               'configured_access_detected':configured,'series_2025_downloaded':False,'coverage_verified':False,
               'status':'configured access requires coverage audit' if configured else 'excluded: no preconfigured CDS access',
               'native_scale_km':9,'distribution_grid_degrees':.1,'no_account_created':True}}
save(ROOT/'registry/auxiliary-audit.json',value)
print('SMN candidate links:',*value['SMN']['candidate_links'],sep='\n')
print('ERA5 configured access:',configured)
