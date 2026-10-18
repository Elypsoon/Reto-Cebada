"""Estadística zonal por intersección real de celdas; sin remuestreo."""
import numpy as np
import rasterio
from rasterio.windows import from_bounds, Window
from shapely.geometry import box
from shapely.ops import transform
from pyproj import Transformer


def zonal_mean(path, parcels):
    values = []
    support = []
    with rasterio.open(path) as src:
        geo = parcels.to_crs(src.crs)
        area_transform = Transformer.from_crs(src.crs, 32614, always_xy=True).transform
        for geom in geo.geometry:
            win = from_bounds(*geom.bounds, transform=src.transform)
            c0, r0 = max(0, int(np.floor(win.col_off))), max(0, int(np.floor(win.row_off)))
            c1 = min(src.width, int(np.ceil(win.col_off + win.width)))
            r1 = min(src.height, int(np.ceil(win.row_off + win.height)))
            if c1 <= c0 or r1 <= r0:
                values.append(np.nan); support.append(0); continue
            a = src.read(1, window=Window(c0, r0, c1-c0, r1-r0), masked=True)
            weighted = total = 0.
            for rr in range(a.shape[0]):
                for cc in range(a.shape[1]):
                    if np.ma.is_masked(a[rr, cc]) or not np.isfinite(a[rr, cc]):
                        continue
                    x0,y0=src.transform*(c0+cc,r0+rr)
                    x1,y1=src.transform*(c0+cc+1,r0+rr+1)
                    inter=geom.intersection(box(min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)))
                    if not inter.is_empty:
                        area=transform(area_transform,inter).area
                        weighted+=float(a[rr,cc])*area; total+=area
            expected=transform(area_transform,geom).area
            values.append(weighted/total if total else np.nan)
            support.append(total/expected if expected else 0.)
    return np.array(values),np.array(support)
