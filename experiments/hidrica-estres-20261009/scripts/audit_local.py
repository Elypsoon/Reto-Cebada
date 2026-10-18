"""Auditorías de entradas originales; no utiliza rendimiento para decisiones."""
import sys
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.common import ROOT,PROJECT,read,save,digest,now,ID,START,CUTOFF
import pandas as pd

original=PROJECT/'Reto-Cebada/DataSet'
if sys.argv[1]=='spectral':
    p=original/'Diccionario_de_indices_satelitales.docx'
    with ZipFile(p) as z: root=ET.fromstring(z.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paragraphs=[''.join(t.text or '' for t in x.findall('.//w:t',ns)) for x in root.findall('.//w:p',ns)]
    i=paragraphs.index('NDWI');definition=paragraphs[i:i+3]
    assert not any('=' in x or 'SWIR' in x or 'NIR' in x for x in definition)
    satellite=pd.read_parquet(ROOT/'data/processed/satellite.parquet')
    satellite=satellite[satellite.date.between(START,CUTOFF)]
    coverage={str(sensor):{'n':len(g),'ndwi_nonmissing':int(g.ndwi_promedio.notna().sum()),
      'ndwi_clear_nonmissing':int((g.ndwi_promedio.notna()&g.porcentaje_nubosidad.le(20)).sum())}
      for sensor,g in satellite.groupby('sensor')}
    sources=[{'path':str(p),'sha256':digest(p),'kind':'diccionario original'}]
    for q in (original/'Data').glob('*.csv'):
        sources.append({'path':str(q),'sha256':digest(q),'columns':list(pd.read_csv(q,nrows=0).columns)})
    save(ROOT/'registry/spectral-audit.json',{'at':now(),'definition':definition,'bands':None,'formula':None,
      'orientation':None,'sensor_coverage':coverage,'sources':sources,'S_admitted':False,
      'status':'definición no comprobada','reason':'Los originales entregados no especifican bandas ni fórmula de NDWI; no hay código productor identificable. Referencias genéricas no identifican la definición de esta columna.',
      'labels_used':False,'interpretation':'Señal espectral original, sin atribución de agua foliar.'})
    print('S excluido: fórmula y bandas no comprobadas')
elif sys.argv[1]=='metadata':
    master=pd.read_parquet(ROOT/'data/processed/parcels.parquet')
    checks={}
    for field in ['variedad','cultivar','siembra','fecha_siembra','riego']:
        checks[field]={'present_in_official_master':field in master.columns,'assigned':False}
    climate=[]
    for p in sorted((ROOT/'data/external').glob('nasa*.json')):
        d=read(p);vals=list(d['properties']['parameter']['T2M_MIN'].values())
        climate.append({'file':p.name,'sha256':digest(p),'min_tmin_c':min(vals),'days_below_zero':sum(v<0 for v in vals)})
    save(ROOT/'registry/agronomic-metadata-audit.json',{'at':now(),'fields':checks,'official_columns':list(master.columns),
      'nasa_regional_temperature':climate,'local_frost_observations':None,'variety_by_official_id':None,
      'sowing_by_official_id':None,'new_predictive_fields':[],'labels_used':False,
      'search_scope':'Tabla oficial, cabeceras originales, diccionario y series NASA verificadas. Datos auxiliares CIMMYT no identifican variedades/siembra de IDs oficiales.',
      'interpretation':'Cero días regionales bajo cero no descarta heladas parcelarias; ausencia de metadatos queda desconocida.'})
    print('Metadatos desconocidos preservados; cero campos nuevos')
else: raise ValueError('Auditoría desconocida')
