import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box
import pytest
from hydric.soil import awc,extract,admitted_table,validate_metadata,DEPTHS

def test_units_and_physical_rejection():
    assert sum(float(awc(.20,.10,h)) for _,h in DEPTHS[:3])==pytest.approx(30)
    assert float(awc(.20,.10,.30))==pytest.approx(30)
    assert np.isnan(awc(.10,.20,.30))
    assert np.isnan(awc(1.2,.1,.30))
    assert not validate_metadata({})['admitted']

def create_maps(tmp_path,missing=False):
    paths={}
    for d,_ in DEPTHS:
        for p in [33,1500]:
            for stat in ['mean','Q05','Q95']:
                value=(200 if p==33 else 100)+{'mean':0,'Q05':-70,'Q95':70}[stat]
                a=np.full((2,2),value,dtype=np.int16)
                if missing and (d,p,stat)==('15-30cm',1500,'mean'): a[0,0]=-9999
                f=tmp_path/f'{d}-{p}-{stat}.tif'
                with rasterio.open(f,'w',driver='GTiff',width=2,height=2,count=1,dtype='int16',crs=32614,transform=from_origin(500000,2200000,250,250),nodata=-9999) as ds: ds.write(a,1)
                paths[(d,p,stat)]=f
    return paths

def test_subpixel_without_center_and_common_mask(tmp_path):
    parcels=gpd.GeoDataFrame({'ID_POLIGONO':['a','b']},geometry=[box(500010,2199990,500020,2199980),box(500000,2199750,500500,2200000)],crs=32614)
    paths=create_maps(tmp_path)
    values,coverage,envelopes,decision=extract(paths,parcels)
    np.testing.assert_allclose(values,30)
    np.testing.assert_allclose(coverage,1)
    assert (envelopes[['lower_0_30','lower_30_60']]<0).all().all()
    assert decision['G_admitted'] and len(values)==2
    paths=create_maps(tmp_path,missing=True)
    values,coverage,_,decision=extract(paths,parcels)
    assert len(values)==2 and values.isna().all().all()
    assert coverage.iloc[0]==0 and coverage.iloc[1]==pytest.approx(.5)
    assert not decision['G_admitted']

def test_population_retained_and_threshold():
    data=pd.DataFrame({'AWC_0_30_mm':[30]*197,'AWC_30_60_mm':[30]*197})
    support=pd.Series([1.]*177+[.94]*20)
    out,decision=admitted_table(data,support)
    assert len(out)==197 and decision['n_complete']==177 and not decision['G_admitted']
    support.iloc[177]=.95
    assert admitted_table(data,support)[1]['G_admitted']
