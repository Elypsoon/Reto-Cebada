from pathlib import Path
import sys
PHASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PHASE/'src'))
from signalclima.common import ROOT,ID,WINDOWS,save
from signalclima.features import calendar
import pandas as pd
import numpy as np

ids=pd.read_parquet(ROOT/'data/processed/parcels.parquet',columns=[ID])[ID]
d=pd.read_parquet(ROOT/'data/processed/satellite.parquet')
d=d[d.date.between('2025-04-01','2025-10-31')&d.sensor.eq('Sentinel-2')&d.porcentaje_nubosidad.le(20)&d.ndwi_promedio.notna()].copy()
reports=[]
for width,minimum in [(7,4),(14,2)]:
    cal=calendar(width);d['interval']=((d.date-pd.Timestamp('2025-04-01')).dt.days//width).astype(int)
    counts=d.groupby([ID,'interval']).date.nunique()
    supported=[];windows={}
    for window in WINDOWS:
        bins=cal[cal.window.eq(window)].interval
        valid=counts[counts.ge(2)].reset_index();valid=valid[valid.interval.isin(bins)].groupby(ID).size().reindex(ids,fill_value=0)
        enough=valid.ge(minimum)&valid.ge(.5*len(bins));supported.append(set(ids[enough.to_numpy()]))
        windows[window]={'intervals':len(bins),'supported_parcels':int(enough.sum()),'minimum_valid_intervals':minimum,'minimum_fraction':.5}
    reports.append({'days':width,'windows':windows,'all_windows':len(set.intersection(*supported))})
save(ROOT/'registry/coverage-diagnostic.json',{'source':'NDWI original con fórmula desconocida','labels_used':False,
 'temporal_diagnostic_only':True,'native_pixel_mask_unknown':True,'semantic_admission':False,'reports':reports})
print('Cobertura temporal original:',reports)
