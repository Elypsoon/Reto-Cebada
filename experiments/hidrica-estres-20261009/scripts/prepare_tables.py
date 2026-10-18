import sys
from pathlib import Path
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.common import ROOT,ID,WINDOWS,read,save,digest
from hydric.stress import calendar,weekly_observations
import numpy as np
import pandas as pd

base=pd.read_parquet(ROOT/'data/processed/features_monthly_20_10.parquet')
external=pd.read_parquet(ROOT/'data/processed/external_nasa.parquet')
master=pd.read_parquet(ROOT/'data/processed/parcels.parquet')
assert base.index.equals(pd.Index(master[ID])) and len(base)==197 and not any(c.startswith('nasa_') for c in base)
vpd=[f'nasa_vpd_{w}' for w in WINDOWS]+['nasa_gdd_base0_cap26']
solar=[f'nasa_solar_{w}' for w in WINDOWS]
enriched=base.join(external[vpd],validate='one_to_one')
radiation=external[solar].copy()
assert not any('solar' in c for c in enriched) and radiation.index.equals(base.index)
assert np.isfinite(external[vpd+solar]).all().all()
base.to_parquet(ROOT/'data/processed/control-official.parquet')
enriched.to_parquet(ROOT/'data/processed/control-enriched.parquet')
radiation.to_parquet(ROOT/'data/processed/block-radiation.parquet')
cells=pd.read_csv(ROOT/'data/processed/nasa-cells.csv')
weather=[]
native={}
for p in (ROOT/'data/external').glob('nasa*.json'):
    raw=read(p);lon,lat,*_=raw['geometry']['coordinates']
    f=pd.DataFrame(raw['properties']['parameter']);f.index=pd.to_datetime(f.index,format='%Y%m%d')
    es=lambda x:.6108*np.exp(17.27*x/(x+237.3))
    daily=((es(f.T2M_MIN)+es(f.T2M_MAX))/2-es(f.T2MDEW)).clip(lower=0)
    native[(lon,lat)]=daily
for row in cells.itertuples():
    key=(row.longitude,row.latitude);daily=native[key]
    for week in calendar().itertuples():
        weather.append({ID:getattr(row,ID),'cell':f'{key[0]}_{key[1]}','week':week.week,'vpd':float(daily.loc[week.start:week.stop].mean())})
weekly=weekly_observations(pd.read_parquet(ROOT/'data/processed/satellite.parquet'),pd.DataFrame(weather))
weekly.to_parquet(ROOT/'data/processed/weekly-inputs.parquet',index=False)
assert len(weekly)==197*len(calendar()) and not weekly[[ID,'week']].duplicated().any()
save(ROOT/'registry/table-check.json',{'passed':True,'n':197,'official_columns':list(base.columns),'enriched_extra':vpd,
 'radiation_extra':solar,'official_has_nasa':False,'enriched_has_solar':False,'solar_units':'MJ/m2 por ventana',
 'n_native_cells':len(cells[['longitude','latitude']].drop_duplicates()),'semantic_S_admitted':read(ROOT/'registry/spectral-audit.json')['S_admitted'],
 'hashes':{p.name:digest(p) for p in (ROOT/'data/processed').glob('control-*.parquet')},
 'weekly_rows':len(weekly),'window_units':{'vpd':'kPa','temperature':'C','NDWI':'índice espectral de definición no comprobada'}})
print('Tablas O/E/R verificadas; semanas conservan soporte, S no admitido')
