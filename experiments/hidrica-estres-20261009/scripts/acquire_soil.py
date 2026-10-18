"""Consulta oficial acotada; registra metadatos/fallos antes de admitir suelo."""
import sys,time
from pathlib import Path
import requests
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.common import ROOT,save,digest,now
budget=2*1024**3;started=time.monotonic();events=[];used=0
target=ROOT/'registry/soil-access'
target.mkdir(parents=True,exist_ok=True)
urls=[
 'https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html',
 'https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_02.html',
 'https://files.isric.org/soilgrids/latest/data/',
 'https://files.isric.org/soilgrids/latest/data/wv0033/',
 'https://files.isric.org/soilgrids/latest/data/wv1500/',
 'https://maps.isric.org/',
 'https://maps.isric.org/mapserv?map=/map/wv0033.map&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCapabilities',
 'https://maps.isric.org/mapserv?map=/map/wv1500.map&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCapabilities',
]
for i,url in enumerate(urls):
    event={'url':url,'at':now()};begin=time.monotonic()
    try:
        if time.monotonic()-started>=1800: raise TimeoutError('Presupuesto de adquisición agotado')
        response=requests.get(url,timeout=(10,35),stream=True)
        path=target/f'{i:02}.response'
        with path.open('wb') as f:
            for chunk in response.iter_content(65536):
                used+=len(chunk)
                if used>budget or time.monotonic()-started>=1800: raise ValueError('Presupuesto de adquisición agotado')
                f.write(chunk)
        event.update(status_code=response.status_code,bytes=path.stat().st_size,sha256=digest(path),file=str(path),
          content_type=response.headers.get('Content-Type'),last_modified=response.headers.get('Last-Modified'))
    except Exception as error:
        event['error']=repr(error)
    event['seconds']=time.monotonic()-begin;events.append(event)
    save(ROOT/'registry/soil-acquisition.json',{'started':started,'at':now(),'events':events,'bytes':used,'seconds':time.monotonic()-started,'budget_bytes':budget,'budget_seconds':1800,'status':'auditoría de acceso en curso','raster_acquired':False})
    print(i,event.get('status_code',event.get('error')),flush=True)
save(ROOT/'registry/soil-acquisition.json',{'at':now(),'events':events,'bytes':used,'seconds':time.monotonic()-started,'budget_bytes':budget,'budget_seconds':1800,'status':'catálogo consultado; revisar capacidades','raster_acquired':False})
