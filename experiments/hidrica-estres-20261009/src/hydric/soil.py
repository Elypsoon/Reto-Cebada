"""Retención cartográfica, espesores y máscara común; datos locales solamente."""
from contextlib import ExitStack
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window,from_bounds
from pyproj import Transformer
from shapely.geometry import box
from shapely.ops import transform
from .common import ID

DEPTHS=[('0-5cm',.05),('5-15cm',.10),('15-30cm',.15),('30-60cm',.30)]

def validate_metadata(metadata):
    required=['provider','version','license','published_at','resolution_m','crs','units','volume_reference','source_sha256']
    missing=[k for k in required if not metadata.get(k)]
    if metadata.get('provider')!='ISRIC': missing.append('proveedor ISRIC')
    if metadata.get('units')!='0.001 m3/m3': missing.append('unidades volumétricas verificadas')
    if metadata.get('pressures_kpa')!=[33,1500]: missing.append('presiones')
    if metadata.get('depths')!=[d for d,_ in DEPTHS]: missing.append('profundidades')
    if metadata.get('statistics')!=['mean','Q05','Q95']: missing.append('incertidumbre')
    if not metadata.get('nodata_verified'): missing.append('NoData comprobado')
    return {'admitted':not missing,'missing':missing}

def awc(theta33,theta1500,thickness):
    a,b=np.asarray(theta33,dtype=float),np.asarray(theta1500,dtype=float)
    valid=np.isfinite(a)&np.isfinite(b)&(b>=0)&(a<=1)&(b<=a)
    return np.where(valid,1000*(a-b)*thickness,np.nan)

def admitted_table(table,coverage):
    out=table.copy()
    out.loc[coverage.lt(.95),'AWC_0_30_mm']=np.nan
    out.loc[coverage.lt(.95),'AWC_30_60_mm']=np.nan
    rate=float(out.notna().all(axis=1).mean())
    return out,{'G_admitted':rate>=.9,'complete_fraction':rate,'surface_minimum':.95,'parcel_minimum':.9,
               'n':len(out),'n_complete':int(out.notna().all(axis=1).sum()),'measured':False}

def extract(paths,parcels):
    if parcels.crs is None or not parcels[ID].is_unique or not parcels.geometry.is_valid.all():
        raise ValueError('Geometría o identidad no válida')
    keys=[(depth,pressure,stat) for depth,_ in DEPTHS for pressure in [33,1500] for stat in ['mean','Q05','Q95']]
    if set(paths)!=set(keys): raise ValueError('Faltan capas obligatorias de suelo')
    values=[];bounds=[];supports=[]
    with ExitStack() as stack:
        datasets=[]
        for key in keys:
            p=Path(paths[key])
            if not p.is_file() or p.suffix.lower() not in ['.tif','.tiff']:
                raise ValueError('La extracción exige GeoTIFF local verificado')
            datasets.append(stack.enter_context(rasterio.open(p)))
        reference=datasets[0]
        if reference.crs is None or reference.transform.b or reference.transform.d:
            raise ValueError('CRS ausente o rejilla rotada no admitida')
        for src in datasets[1:]:
            if (src.crs,src.transform,src.width,src.height)!=(reference.crs,reference.transform,reference.width,reference.height):
                raise ValueError('Las capas no comparten rejilla nativa; no se remuestrean')
        geometries=parcels.to_crs(reference.crs).geometry
        to_area=Transformer.from_crs(reference.crs,32614,always_xy=True).transform
        positions={key:i for i,key in enumerate(keys)}
        for geom in geometries:
            w=from_bounds(*geom.bounds,reference.transform)
            c0,r0=max(0,int(np.floor(w.col_off))),max(0,int(np.floor(w.row_off)))
            c1,r1=min(reference.width,int(np.ceil(w.col_off+w.width))),min(reference.height,int(np.ceil(w.row_off+w.height)))
            total=0.;sums=np.zeros(6)
            if c1>c0 and r1>r0:
                arrays=np.ma.stack([s.read(1,window=Window(c0,r0,c1-c0,r1-r0),masked=True) for s in datasets])
                matrix=np.asarray(arrays.astype(float).filled(np.nan),dtype=float)/1000
                valid=np.isfinite(matrix).all(axis=0)&(~np.ma.getmaskarray(arrays)).all(axis=0)
                valid&=((matrix>=0)&(matrix<=1)).all(axis=0)
                results=np.zeros((6,r1-r0,c1-c0))
                for j,(depth,thickness) in enumerate(DEPTHS):
                    a=matrix[positions[(depth,33,'mean')]];b=matrix[positions[(depth,1500,'mean')]]
                    valid&=b<=a
                    qlo=matrix[positions[(depth,33,'Q05')]]-matrix[positions[(depth,1500,'Q95')]]
                    qhi=matrix[positions[(depth,33,'Q95')]]-matrix[positions[(depth,1500,'Q05')]]
                    for pressure in [33,1500]: valid&=matrix[positions[(depth,pressure,'Q05')]]<=matrix[positions[(depth,pressure,'Q95')]]
                    target=0 if j<3 else 1
                    results[target]+=1000*(a-b)*thickness
                    results[2+target]+=1000*qlo*thickness
                    results[4+target]+=1000*qhi*thickness
                for rr,cc in np.argwhere(valid):
                    x0,y0=reference.transform*(c0+int(cc),r0+int(rr))
                    x1,y1=reference.transform*(c0+int(cc)+1,r0+int(rr)+1)
                    inter=geom.intersection(box(min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)))
                    if not inter.is_empty:
                        area=transform(to_area,inter).area
                        sums+=results[:,rr,cc]*area;total+=area
            expected=transform(to_area,geom).area
            support=total/expected if expected>0 else 0.
            values.append((sums[:2]/total).tolist() if total else [np.nan,np.nan])
            bounds.append((sums[2:]/total).tolist() if total else [np.nan]*4)
            supports.append(support)
    ix=pd.Index(parcels[ID],name=ID)
    table=pd.DataFrame(values,index=ix,columns=['AWC_0_30_mm','AWC_30_60_mm'])
    coverage=pd.Series(supports,index=ix,name='common_area_fraction')
    table,decision=admitted_table(table,coverage)
    envelopes=pd.DataFrame(bounds,index=ix,columns=['lower_0_30','lower_30_60','upper_0_30','upper_30_60'])
    envelopes.loc[coverage.lt(.95)]=np.nan
    return table,coverage,envelopes,decision
