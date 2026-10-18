"""Recortes de COG oficial mediante fragmentos reproducibles; no transmite coordenadas."""
from pathlib import Path
import sys
import math
import argparse
PHASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE / 'src'))
from signalclima.common import ROOT, START, CUTOFF, save, read, digest, now, safe
from signalclima.acquisition import Client, AcquisitionError
from signalclima.rangefile import RangeFile
from signalclima.raster import validate_grid
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import Window,from_bounds

parser=argparse.ArgumentParser();parser.add_argument('--sample',action='store_true');args=parser.parse_args()
client=Client()
parcels=gpd.read_parquet(ROOT/'data/processed/parcels.parquet',columns=['ID_POLIGONO','geometry'])
dates=pd.date_range(START,CUTOFF)
if args.sample:dates=dates[:1]
folder=ROOT/'data/external/chirps';folder.mkdir(parents=True,exist_ok=True)
records=[];failure=None
for date in dates:
    basename=f'chirps-v3.0.sat.{date:%Y.%m.%d}.cog'
    url='https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/sat/cogs/2025/'+basename
    target=safe(folder/f'{date:%Y%m%d}.tif');receipt=target.with_suffix('.json')
    try:
        if receipt.exists():
            record=read(receipt)
            if digest(target)!=record['sha256']:raise AcquisitionError('Recorte local alterado')
            records.append(record);continue
        def opener(fp,mode='rb',offline=False):
            if str(fp)!=basename or mode not in ['r','rb']:raise FileNotFoundError(str(fp))
            return RangeFile(client,url,basename,offline=offline)
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
            with rasterio.open(basename,opener=opener) as src:
                validate_grid(src,.05,'EPSG:4326')
                bounds=parcels.to_crs(src.crs).total_bounds
                raw=from_bounds(*bounds,src.transform)
                left,top=int(math.floor(raw.col_off)),int(math.floor(raw.row_off))
                right,bottom=int(math.ceil(raw.col_off+raw.width)),int(math.ceil(raw.row_off+raw.height))
                window=Window(left,top,right-left,bottom-top)
                if left<0 or top<0 or right>src.width or bottom>src.height:raise AcquisitionError('Área fuera de la fuente')
                values=src.read(1,window=window,masked=True)
                profile=src.profile.copy();profile.update(driver='GTiff',height=values.shape[0],width=values.shape[1],transform=src.window_transform(window),compress='deflate')
                for key in ['blockxsize','blockysize','tiled']:profile.pop(key,None)
                with rasterio.open(target,'w',**profile) as out:
                    out.write(values.filled(src.nodata),1)
                    out.update_tags(provider='CHC UCSB',product='CHIRPS v3 final daily sat',units='mm/day',date=f'{date:%Y-%m-%d}',source=url,method='native window from cached HTTP fragments')
                metadata={'crs':str(src.crs),'native_resolution_degrees':list(src.res),'nodata':float(src.nodata),'source_shape':[src.height,src.width],'window':[left,top,right-left,bottom-top]}
            # The same window must reproduce solely from stored source fragments.
            with rasterio.open(basename,opener=lambda fp,mode='rb':opener(fp,mode,offline=True)) as src:
                reproduced=src.read(1,window=window,masked=True)
                np.testing.assert_array_equal(values.filled(src.nodata),reproduced.filled(src.nodata))
        with rasterio.open(target) as check:validate_grid(check,.05,'EPSG:4326')
        fragments={k:v for k,v in client.state['files'].items() if k.startswith(basename+'.range-')}
        record={'date':f'{date:%Y-%m-%d}','path':str(target),'sha256':digest(target),'source':url,'product':'CHIRPS v3 final daily sat','version':'3.0',
                'units':'mm/day','time':'UTC labels for IMERG disaggregation; underlying station windows heterogeneous',
                'license':'CHC public data; attribute CHC and Funk et al. 2026','metadata':metadata,'fragments':fragments,'offline_crop_reproduced':True,'downloaded_at':now()}
        save(receipt,record,exclusive=True);records.append(record)
        print('CHIRPS',f'{date:%Y-%m-%d}','recorte verificado;',len(fragments),'fragmentos',flush=True)
    except Exception as error:
        failure=type(error).__name__+': '+str(error).split('\n')[0][:220]
        print('CHIRPS acceso no viable:',failure,flush=True)
        break
save(ROOT/'registry'/('chirps-sample.json' if args.sample else 'chirps-acquisition.json'),{
 'at':now(),'status':'sample_verified' if args.sample and not failure else 'complete' if len(records)==214 and not failure else 'not_viable',
 'failure':failure,'dates_required':len(dates),'dates_verified':len(records),'records':records,'labels_used':False,
 'coordinates_transmitted':False,'bytes':client.state['bytes'],'seconds':client.state['seconds']})
