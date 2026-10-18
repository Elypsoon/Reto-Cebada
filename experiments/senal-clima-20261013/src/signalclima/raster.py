from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window, from_bounds
from shapely.geometry import box
from shapely.ops import transform
from pyproj import Transformer
from .common import ID, safe


def validate_grid(src, resolution, expected_crs=None):
    if src.crs is None or src.nodata is None or src.count != 1 or src.transform.b or src.transform.d:
        raise ValueError('CRS, NoData, banda o rejilla no comprobados')
    if not np.allclose(np.abs(src.res), resolution, atol=1e-8, rtol=0):
        raise ValueError('Resolución nativa incompatible')
    if expected_crs and src.crs != rasterio.crs.CRS.from_user_input(expected_crs):
        raise ValueError('CRS incompatible con el producto')


def pixel_weights(src, parcels):
    if parcels.crs is None or not parcels[ID].is_unique or not parcels.geometry.is_valid.all():
        raise ValueError('Identidad o geometría incompatible')
    geometries = parcels.to_crs(src.crs).geometry
    area_transform = Transformer.from_crs(src.crs, 32614, always_xy=True).transform
    rows = []
    for pid, geom in zip(parcels[ID], geometries):
        raw = from_bounds(*geom.bounds, src.transform)
        left, top = max(0, int(np.floor(raw.col_off))), max(0, int(np.floor(raw.row_off)))
        right = min(src.width, int(np.ceil(raw.col_off+raw.width)))
        bottom = min(src.height, int(np.ceil(raw.row_off+raw.height)))
        window = Window(left, top, max(0, right-left), max(0, bottom-top))
        weights = np.zeros((int(window.height), int(window.width)))
        for rr, cc in np.ndindex(weights.shape):
            x0, y0 = src.transform@(left+cc, top+rr)
            x1, y1 = src.transform@(left+cc+1, top+rr+1)
            intersection = geom.intersection(box(min(x0,x1), min(y0,y1), max(x0,x1), max(y0,y1)))
            if not intersection.is_empty:
                weights[rr, cc] = transform(area_transform, intersection).area
        rows.append((pid, window, weights, transform(area_transform,geom).area))
    return rows


def zonal(src, parcels, minimum=.95, valid_values=None):
    output = []
    for pid, window, weights, total in pixel_weights(src, parcels):
        if not weights.size:
            output.append({ID: pid, 'value': np.nan, 'coverage': 0., 'effective_pixels': 0.})
            continue
        data = src.read(1, window=window, masked=True).astype(float)
        values = data.filled(np.nan)
        valid = (~np.ma.getmaskarray(data)) & np.isfinite(values)
        if valid_values:
            valid &= valid_values(values)
        support = weights[valid].sum()
        fraction = support/total if total > 0 else 0.
        value = float((values[valid]*weights[valid]).sum()/support) if support > 0 and fraction >= minimum else np.nan
        effective = float(support**2/(weights[valid]**2).sum()) if support > 0 else 0.
        output.append({ID: pid, 'value': value, 'coverage': fraction, 'effective_pixels': effective})
    return pd.DataFrame(output)


def ndmi_raster(nir_path, swir_path, scl_path, output, scale, offset):
    if not np.isfinite([scale, offset]).all() or scale <= 0:
        raise ValueError('Conversión de reflectancia no comprobada')
    with rasterio.open(nir_path) as nir, rasterio.open(swir_path) as swir, rasterio.open(scl_path) as scl:
        for src in [nir,swir,scl]: validate_grid(src, 20)
        signature = lambda src: (src.crs,src.transform,src.width,src.height)
        if signature(nir) != signature(swir) or signature(nir) != signature(scl):
            raise ValueError('Bandas no comparten rejilla nativa; no remuestrear')
        a, b, quality = nir.read(1,masked=True), swir.read(1,masked=True), scl.read(1,masked=True)
        ar, br = a.astype(float)*scale+offset, b.astype(float)*scale+offset
        valid = ~np.ma.getmaskarray(a) & ~np.ma.getmaskarray(b) & ~np.ma.getmaskarray(quality)
        valid &= np.isin(np.asarray(quality),[4,5]) & np.isfinite(ar.filled(np.nan)) & np.isfinite(br.filled(np.nan))
        valid &= (ar.filled(-1)>=0)&(br.filled(-1)>=0)&((ar+br).filled(0)>1e-12)
        out = np.full(a.shape,-9999.,dtype='float32')
        out[valid] = ((ar-br)/(ar+br)).filled(np.nan)[valid]
        profile = nir.profile.copy()
        profile.update(driver='GTiff',dtype='float32',nodata=-9999.,count=1,compress='deflate')
        destination = safe(output)
        if destination.exists(): raise ValueError('No sobrescribir señal derivada')
        destination.parent.mkdir(parents=True,exist_ok=True)
        with rasterio.open(destination,'w',**profile) as result:
            result.write(out,1)
            result.update_tags(formula='(B8A-B11)/(B8A+B11)',scale=scale,offset=offset,identity='ndmi_b8a_b11',quality='SCL 4,5')
    with rasterio.open(destination) as src: validate_grid(src,20)
    return destination
