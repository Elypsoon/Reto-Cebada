import re
import numpy as np
import geopandas as gpd
import rasterio
import pytest
from shapely.geometry import box
from rasterio.transform import from_origin
from signalclima.acquisition import Client, AcquisitionError
from signalclima.rangefile import RangeFile
from signalclima.raster import ndmi_raster,zonal,validate_grid


def test_range_protocol_and_offline_integrity(tmp_path,monkeypatch):
    import signalclima.common as common
    monkeypatch.setattr(common,'ROOT',tmp_path)
    monkeypatch.setattr(RangeFile,'block_size',4)
    class Response:
        def __init__(self,start,end):
            self.status_code=206;self.data=b'abcdefghij'[start:end+1]
            self.headers={'Content-Length':str(len(self.data)),'Content-Range':f'bytes {start}-{end}/10','ETag':'stable'}
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def raise_for_status(self):pass
        def iter_content(self,n):yield self.data
    class Session:
        def get(self,url,**kw):
            start,end=map(int,re.search(r'(\d+)-(\d+)',kw['headers']['Range']).groups())
            return Response(start,min(end,9))
    client=Client(tmp_path/'cache',Session())
    f=RangeFile(client,'https://example.org/a','a');f.seek(2)
    assert f.read(6)==b'cdefgh'
    offline=RangeFile(client,'https://example.org/a','a',offline=True);offline.seek(2)
    assert offline.read(6)==b'cdefgh'
    (client.folder/'a.range-0.bin').write_bytes(b'xxxx')
    with pytest.raises(AcquisitionError,match='alterado'):RangeFile(client,'https://example.org/a','a',offline=True)


def write(path,values,nodata=-9999):
    with rasterio.open(path,'w',driver='GTiff',height=2,width=2,count=1,dtype='float32',crs='EPSG:32614',transform=from_origin(500000,2200000,20,20),nodata=nodata) as src:src.write(np.asarray(values,dtype='float32'),1)


def test_ndmi_quality_native_grid_and_partial_coverage(tmp_path,monkeypatch):
    import signalclima.common as common
    monkeypatch.setattr(common,'ROOT',tmp_path)
    for name,values in [('nir',[[3000,3000],[3000,3000]]),('swir',[[2000,2000],[2000,2000]]),('scl',[[4,9],[4,4]])]:write(tmp_path/f'{name}.tif',values)
    path=ndmi_raster(*(tmp_path/f'{n}.tif' for n in ['nir','swir','scl']),tmp_path/'ndmi.tif',.0001,-.1)
    parcels=gpd.GeoDataFrame({'ID_POLIGONO':['a','b']},geometry=[box(500000,2199960,500040,2200000),box(500000,2199980,500020,2200000)],crs=32614)
    with rasterio.open(path) as src:
        assert zonal(src,parcels,minimum=.8).iloc[0]['coverage']==pytest.approx(.75)
        assert np.isnan(zonal(src,parcels,minimum=.8).iloc[0]['value'])
        assert zonal(src,parcels,minimum=.8).iloc[1]['value']==pytest.approx(1/3)
        with pytest.raises(ValueError,match='Resolución'):validate_grid(src,10)


def test_rasterio_opener_crop_and_offline_replay(tmp_path,monkeypatch):
    import signalclima.common as common
    monkeypatch.setattr(common,'ROOT',tmp_path)
    source=tmp_path/'source.tif';write(source,[[1,2],[3,4]])
    data=source.read_bytes()
    class Response:
        def __init__(self,start,end):
            self.status_code=206;self.data=data[start:end+1]
            self.headers={'Content-Length':str(len(self.data)),'Content-Range':f'bytes {start}-{end}/{len(data)}','ETag':'fixture'}
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def raise_for_status(self):pass
        def iter_content(self,n):yield self.data
    class Session:
        offline=False
        def get(self,url,**kw):
            if self.offline:raise AssertionError('Consulta de red durante reproducción')
            start,end=map(int,re.search(r'(\d+)-(\d+)',kw['headers']['Range']).groups())
            return Response(start,min(end,len(data)-1))
    session=Session();client=Client(tmp_path/'cache',session)
    opener=lambda fp,mode='rb':RangeFile(client,'https://example.org/source.tif','source')
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        with rasterio.open('virtual-source.tif',opener=opener) as src:
            got=src.read(1,window=rasterio.windows.Window(0,0,1,1))
        session.offline=True
        with rasterio.open('virtual-source.tif',opener=lambda fp,mode='rb':RangeFile(client,'https://example.org/source.tif','source',offline=True)) as src:
            np.testing.assert_array_equal(got,src.read(1,window=rasterio.windows.Window(0,0,1,1)))
    assert got[0,0]==1
