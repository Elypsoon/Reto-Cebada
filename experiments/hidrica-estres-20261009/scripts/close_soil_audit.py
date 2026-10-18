import sys
from pathlib import Path
import xml.etree.ElementTree as ET
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.common import ROOT,read,save,digest,now
from hydric.soil import validate_metadata
record=read(ROOT/'registry/soil-acquisition.json')
assert record['status']=='no viable' and not record['raster_acquired']
assert 'CRS' in record['reason']
p=ROOT/'registry/soil-access/iso-wv0033.xml'
text=' '.join(ET.parse(p).getroot().itertext())
assert 'Volumetric Water Content at 33kPa' in text and '10-3 cm3cm-3' in text
metadata={'provider':'ISRIC','version':'SoilGrids250m 2.0 water retention','published_at':'2021-11-05',
  'license':'CC BY 4.0 según documentación oficial','units':'0.001 m3/m3','volume_reference':'volumen de suelo según ficha ISO',
  'resolution_m':250,'pressures_kpa':[33,1500],'depths':['0-5cm','5-15cm','15-30cm','30-60cm'],
  'statistics':['mean','Q05','Q95'],'source_sha256':digest(p),'crs':None,'nodata_verified':False}
decision=validate_metadata(metadata)
assert not decision['admitted']
save(ROOT/'registry/soil-admission.json',{'at':now(),'G_admitted':False,'metadata':metadata,
  'required_layer_count':24,'complete_valid_layer_count':0,'audit':decision,
  'reason':'Primera cobertura WCS recuperada a 250 m sin CRS ni NoData en el GeoTIFF; DescribeCoverage contiene unidad radiométrica incongruente y nilValues vacío. La ficha ISO confirma retención/unidades para 33 kPa, pero no completa la máscara ni la integridad del conjunto de 24 capas. Se conserva el intento y se excluye G con la regla previa.',
  'read_documents':[{'file':str(p),'sha256':digest(p)}],
  'not_evaluated_scientifically':True,'scope_not_replaced':True,'labels_used':False})
save(ROOT/'registry/soil-sensitivity.json',{'available':False,'reason':'G no admitido; no hay conjunto compatible para calcular envolventes reales. Función verificada con casos sintéticos.','ten_kpa_acquired':False,'calibrated_interval':False})
print('G no viable: metadatos y conjunto de capas incompletos; intento preservado')
