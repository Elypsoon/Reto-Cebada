"""Descarga recortes WCS en la rejilla nativa, nunca mapas globales."""
import sys,time,math
from pathlib import Path
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
import requests
import geopandas as gpd
import rasterio
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.common import ROOT,save,read,digest,now
from hydric.soil import DEPTHS

record=read(ROOT/'registry/soil-acquisition.json')
events=record['events'];used=record['bytes'];started=time.monotonic()
budget=record['budget_bytes'];previous_seconds=record['seconds']
describe=ET.parse(ROOT/'registry/soil-access/describe.response')
ns={'gml':'http://www.opengis.net/gml/3.2'}
origin=[float(x) for x in describe.find('.//gml:pos',ns).text.split()]
offsets=[n.text for n in describe.findall('.//gml:offsetVector',ns)]
assert offsets==['250.000000 0','0 -250.000000']
crs='+proj=igh +datum=WGS84 +units=m +no_defs'
master=gpd.read_parquet(ROOT/'data/processed/parcels.parquet')
bounds=master.to_crs(crs).total_bounds
# Native cell edges, with one cell margin; identical requested extent for all layers.
left=origin[0]-125;top=origin[1]+125
x0=left+250*(math.floor((bounds[0]-left)/250)-1)
x1=left+250*(math.ceil((bounds[2]-left)/250)+1)
y0=top+250*(math.floor((bounds[1]-top)/250)-1)
y1=top+250*(math.ceil((bounds[3]-top)/250)+1)
layers=[];failed=None
for property,pressure in [('wv0033',33),('wv1500',1500)]:
    capabilities=ET.parse(ROOT/'registry/soil-access'/('06.response' if pressure==33 else '07.response'))
    ids={x.text for x in capabilities.findall('.//{http://www.opengis.net/wcs/2.0}CoverageId')}
    for depth,_ in DEPTHS:
        for stat,suffix in [('mean','mean'),('Q05','Q0.05'),('Q95','Q0.95')]:
            coverage=f'{property}_{depth}_{suffix}'
            assert coverage in ids
            parameters=[('map',f'/map/{property}.map'),('SERVICE','WCS'),('VERSION','2.0.1'),('REQUEST','GetCoverage'),
              ('COVERAGEID',coverage),('FORMAT','image/tiff'),('SUBSET',f'x({x0},{x1})'),('SUBSET',f'y({y0},{y1})')]
            url='https://maps.isric.org/mapserv?'+urlencode(parameters)
            event={'url':url,'at':now(),'coverage':coverage};t=time.monotonic()
            target=ROOT/'data/soil'/f'{coverage}.tif'
            try:
                if used>=budget or previous_seconds+time.monotonic()-started>=1800: raise TimeoutError('Presupuesto agotado')
                if target.exists(): raise ValueError('Recorte ya existente; conservar intento')
                response=requests.get(url,timeout=(10,60),stream=True)
                with target.open('wb') as f:
                    for chunk in response.iter_content(65536):
                        used+=len(chunk)
                        if used>budget or previous_seconds+time.monotonic()-started>=1800: raise ValueError('Presupuesto agotado')
                        f.write(chunk)
                response.raise_for_status()
                # Local unpacked file only. No remote GDAL I/O.
                with rasterio.open(target) as src:
                    if src.crs is None or tuple(abs(v) for v in src.res)!=(250.,250.): raise ValueError('Resolución/CRS no nativos')
                    if src.width>5000 or src.height>5000: raise ValueError('Recorte fuera de límite espacial')
                    event['raster']={'width':src.width,'height':src.height,'crs':src.crs.to_wkt(),'transform':list(src.transform),'nodata':src.nodata}
                event.update(status_code=response.status_code,bytes=target.stat().st_size,sha256=digest(target),file=str(target))
                layers.append({'depth':depth,'pressure':pressure,'stat':stat,'file':str(target),'sha256':digest(target),'coverage_id':coverage})
                print(coverage,target.stat().st_size,flush=True)
            except Exception as error:
                event['error']=repr(error);failed=repr(error)
            event['seconds']=time.monotonic()-t;events.append(event)
            save(ROOT/'registry/soil-acquisition.json',{**record,'at':now(),'events':events,'bytes':used,'seconds':previous_seconds+time.monotonic()-started,'layers':layers,'status':'descarga en curso','raster_acquired':len(layers)==24})
            if failed: break
        if failed: break
    if failed: break
save(ROOT/'registry/soil-acquisition.json',{**record,'at':now(),'events':events,'bytes':used,'seconds':previous_seconds+time.monotonic()-started,'layers':layers,'status':'recortes completos' if len(layers)==24 else 'no viable','reason':failed,'raster_acquired':len(layers)==24})
