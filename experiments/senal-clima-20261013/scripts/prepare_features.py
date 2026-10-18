"""Construye entradas sin etiquetas solo después de cerrar las auditorías de acceso."""
from pathlib import Path
import sys
PHASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PHASE/'src'))
from signalclima.common import ROOT,ID,START,CUTOFF,WINDOWS,read,save,digest,now
from signalclima.features import daily_features,signal_intervals,paired_weather
from signalclima.raster import zonal,validate_grid
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

if (ROOT/'registry/frozen-protocol.json').exists():raise ValueError('No modificar entradas congeladas')
required=['chirps-acquisition','sentinel-acquisition']
if any(not (ROOT/f'registry/{name}.json').exists() for name in required):
    raise ValueError('Auditorías de adquisición pendientes: no inferir no viabilidad de una autorización sin respuesta')
rain_audit,signal_audit=[read(ROOT/f'registry/{name}.json') for name in required]
if any(a.get('pending_authorization') or a.get('status') not in ['complete','not_viable'] for a in [rain_audit,signal_audit]):
    raise ValueError('Auditoría/autoridad de acceso pendiente')
parcels=gpd.read_parquet(ROOT/'data/processed/parcels.parquet',columns=[ID,'geometry']);ids=parcels[ID].tolist()
if len(ids)!=197 or not parcels[ID].is_unique:raise ValueError('Población incompatible')
weather=pd.read_parquet(ROOT/'data/processed/weather-daily.parquet')
if not read(ROOT/'registry/nasa-audit.json')['passed']:raise ValueError('NASA no verificado')
dates=pd.date_range(START,CUTOFF);precip=pd.DataFrame(np.nan,index=dates,columns=ids);spatial=precip.copy()
if rain_audit['status']=='complete':
    records=rain_audit['records']
    if len(records)!=214 or len({r['date'] for r in records})!=214:raise ValueError('Serie CHIRPS incompleta/duplicada')
    for record in records:
        path=Path(record['path'])
        if not path.resolve().is_relative_to(ROOT) or digest(path)!=record['sha256']:raise ValueError('Original CHIRPS alterado/fuera de la fase')
        if record['product']!='CHIRPS v3 final daily sat' or record['units']!='mm/day':raise ValueError('Producto/unidades incompatibles')
        with rasterio.open(path) as src:
            validate_grid(src,.05,'EPSG:4326');values=zonal(src,parcels,minimum=.95,valid_values=lambda a:a>=0).set_index(ID)
        day=pd.Timestamp(record['date'])
        if day not in dates:raise ValueError('Fecha CHIRPS fuera de campaña')
        precip.loc[day]=values.reindex(ids).value.to_numpy();spatial.loc[day]=values.reindex(ids).coverage.to_numpy()
d,ds=daily_features(ids,precip,weather)
d_supported=d.notna().all(axis=1);d_admitted=rain_audit['status']=='complete' and float(d_supported.mean())>=.9
observations=pd.DataFrame(columns=[ID,'date','value','coverage'])
if signal_audit['status']=='complete':
    path=Path(signal_audit['series_file'])
    if not path.resolve().is_relative_to(ROOT) or digest(path)!=signal_audit['series_sha256']:raise ValueError('Serie vegetal alterada/fuera de la fase')
    if not signal_audit.get('semantic_verified') or signal_audit.get('identity')!='ndmi_b8a_b11':raise ValueError('Identidad de señal no comprobada')
    observations=pd.read_parquet(path)
    if not observations[ID].isin(ids).all():raise ValueError('Serie con IDs ajenos')
h,q,p,hs=signal_intervals(ids,observations)
h_supported=hs.all(axis=1);h_admitted=signal_audit['status']=='complete' and float(h_supported.mean())>=.7
main,context=paired_weather(p,weather)
combined=pd.concat([d,h,main],axis=1)
pair_supported=combined.notna().all(axis=1)
combined_admitted=d_admitted and h_admitted and float(pair_supported.mean())>=.7
available=[name for name,admitted in [('D',d_admitted),('H',h_admitted),('M',combined_admitted),('I',combined_admitted)] if admitted]
processed=ROOT/'data/processed'
for name,frame in [('block-D',d),('block-H',h),('block-M',combined),('quality-common',q if h_admitted else pd.DataFrame(index=h.index)),
                   ('daily-support',ds),('signal-support',hs)]:
    if not frame.index.equals(pd.Index(ids,name=ID)):raise ValueError('Filas/orden alterados')
    frame.to_parquet(processed/f'{name}.parquet')
p.to_parquet(processed/'signal-intervals.parquet',index=False);context.to_parquet(processed/'paired-intervals.parquet',index=False)
precip.to_parquet(processed/'precipitation-daily.parquet');spatial.to_parquet(processed/'precipitation-spatial-support.parquet')
save(ROOT/'registry/viability.json',{'at':now(),'pending_authorization':False,'labels_used':False,'n':197,'available':available,
 'D':{'admitted':d_admitted,'required_fraction':.9,'supported':int(d_supported.sum()),'fraction':float(d_supported.mean()),'source_status':rain_audit['status'],'reason':rain_audit.get('failure')},
 'H':{'admitted':h_admitted,'required_fraction':.7,'supported':int(h_supported.sum()),'fraction':float(h_supported.mean()),'source_status':signal_audit['status'],'reason':signal_audit.get('failure')},
 'M':{'admitted':combined_admitted,'required_fraction':.7,'supported':int(pair_supported.sum()),'fraction':float(pair_supported.mean()),'dependencies':['D','H','paired weather']},
 'I':{'admitted':combined_admitted,'dependencies':['M','semantic signal'],'training_only_transform':True},
 'common_quality':bool(h_admitted),'rows_removed':0,'spatial_minimum_rain':.95,'spatial_minimum_signal':.8})
print('Viabilidad resuelta sin etiquetas:',available,flush=True)
