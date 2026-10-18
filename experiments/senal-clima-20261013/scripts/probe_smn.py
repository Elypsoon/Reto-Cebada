"""Páginas generales SMN: consultas constantes, sin leer ni enviar ubicaciones de parcelas."""
from pathlib import Path
import sys
PHASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PHASE/'src'))
from signalclima.common import ROOT,save,now
from signalclima.acquisition import Client,AcquisitionError
client=Client();results={}
for name,url in {
 'smn-statistical.html':'https://smn.conagua.gob.mx/es/climatologia/informacion-climatologica/informacion-estadistica-climatologica',
 'smn-ema.html':'https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s',
 'smn-climatological-gui.html':'https://smn.conagua.gob.mx/tools/GUI/estaciones-climatologicas/',
 'smn-emas.kmz':'https://smn.conagua.gob.mx/tools/DATA/Observando%20el%20Tiempo/EMAS/kml/EMAS.kmz',
 'smn-gui-bundle.js':'https://smn.conagua.gob.mx/tools/GUI/estaciones-climatologicas/assets/index-BEaHJrNy.js',
 'smn-climatological-stations.geojson':'https://smn.conagua.gob.mx/tools/GUI/estaciones-climatologicas/data/estaciones_climatologicas.geojson',
}.items():
    try:
        path=client.fetch(url,name);results[name]={'status':'downloaded','file':str(path.relative_to(ROOT)),'url':url}
    except AcquisitionError as error:results[name]={'status':'rejected','reason':str(error),'url':url}
save(ROOT/'registry/smn-probe.json',{'at':now(),'project_data_transmitted':False,'results':results})
print({k:v['status'] for k,v in results.items()},flush=True)
