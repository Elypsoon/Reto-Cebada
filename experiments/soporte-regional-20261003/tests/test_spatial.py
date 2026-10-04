import numpy as np
import geopandas as gpd
from shapely.geometry import box
import rasterio
from rasterio.transform import from_origin
from agrocebada.spatial import zonal_mean


def test_small_parcel_without_pixel_centers(tmp_path):
    p=tmp_path/"grid.tif"
    with rasterio.open(p,"w",driver="GTiff",height=1,width=2,count=1,dtype="float32",crs="EPSG:32614",transform=from_origin(500000,2200000,100,100),nodata=-9999) as d:
        d.write(np.array([[10,20]],dtype="float32"),1)
    g=gpd.GeoDataFrame(geometry=[box(500090,2199950,500110,2199960)],crs=32614)
    v,support=zonal_mean(p,g)
    assert np.isclose(v[0],15) and np.isclose(support[0],1)


def test_nodata_is_not_zero(tmp_path):
    p=tmp_path/"empty.tif"
    with rasterio.open(p,"w",driver="GTiff",height=1,width=1,count=1,dtype="float32",crs="EPSG:32614",transform=from_origin(500000,2200000,100,100),nodata=-9999) as d:d.write(np.array([[-9999]],dtype="float32"),1)
    g=gpd.GeoDataFrame(geometry=[box(500010,2199910,500020,2199920)],crs=32614)
    v,s=zonal_mean(p,g)
    assert np.isnan(v[0]) and s[0]==0
