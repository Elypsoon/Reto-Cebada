import numpy as np
import pandas as pd
from .common import ID,START,CUTOFF,read,digest


def local_nasa(folder,assignments):
    required={'T2M':'C','T2M_MIN':'C','T2M_MAX':'C','T2MDEW':'C','RH2M':'%','ALLSKY_SFC_SW_DWN':'MJ/m^2/day','WS2M':'m/s','PS':'kPa','PRECTOTCORR':'mm/day'}
    frames={};reports=[];expected=pd.date_range(START,CUTOFF)
    for path in sorted(folder.glob('nasa*.json')):
        d=read(path);f=pd.DataFrame(d['properties']['parameter']).replace(d['header']['fill_value'],np.nan)
        f.index=pd.to_datetime(f.index,format='%Y%m%d')
        if d['header']['time_standard']!='LST' or not f.index.equals(expected):raise ValueError('Calendario NASA incompatible')
        if any(d['parameters'].get(c,{}).get('units')!=u for c,u in required.items()):raise ValueError('Unidades NASA incompatibles')
        physical=(f.T2M_MIN<=f.T2M_MAX)&f.T2M.between(-60,60)&f.T2M_MIN.between(-80,60)&f.T2M_MAX.between(-60,70)&f.T2MDEW.between(-80,50)&f.RH2M.between(0,100)&f.PS.between(40,110)&f.WS2M.between(0,100)&f.PRECTOTCORR.between(0,2000)&f.ALLSKY_SFC_SW_DWN.between(0,50)
        if f.notna().mean().min()<.95 or not physical.all():raise ValueError('Integridad NASA insuficiente')
        lon,lat,*_=d['geometry']['coordinates']
        es=lambda t:.6108*np.exp(17.27*t/(t+237.3))
        frames[(lon,lat)]=pd.DataFrame({'date':f.index,'vpd':((es(f.T2M_MIN)+es(f.T2M_MAX))/2-es(f.T2MDEW)).clip(lower=0).to_numpy(),
                                      'tmean':f.T2M.to_numpy(),'tmax':f.T2M_MAX.to_numpy(),'cell':f'nasa:{lon}:{lat}'})
        reports.append({'file':str(path),'sha256':digest(path),'days':len(f),'units':required,'time':'LST','scale':'regional'})
    if len(frames)!=4 or assignments[ID].duplicated().any():raise ValueError('Fuentes o asignaciones NASA incompatibles')
    rows=[]
    for q in assignments.itertuples(index=False):
        key=(q.longitude,q.latitude)
        if key not in frames:raise ValueError('Celda NASA no recuperada')
        a=frames[key].copy();a[ID]=getattr(q,ID);rows.append(a)
    result=pd.concat(rows,ignore_index=True)
    if result.duplicated([ID,'date']).any():raise ValueError('Clima duplicado')
    return result,reports
