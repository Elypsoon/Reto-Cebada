"""Interacciones aprendidas en train; las semanas no observadas quedan ausentes."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator,TransformerMixin
from .common import ID,START,CUTOFF,WINDOWS

def calendar():
    rows=[]
    end=pd.Timestamp(CUTOFF)
    for week,start in enumerate(pd.date_range(START,CUTOFF,freq='7D')):
        stop=min(start+pd.Timedelta(days=6),end)
        center=start+(stop-start)/2
        window=next(k for k,(a,b) in WINDOWS.items() if a<=center.month<=b)
        rows.append({'week':week,'start':start,'stop':stop,'window':window})
    return pd.DataFrame(rows)

def weekly_observations(satellite,weather):
    """Weather ya vinculado por ID, celda, semana; no recibe etiquetas."""
    d=satellite[satellite.date.between(START,CUTOFF)&satellite.sensor.eq('Sentinel-2')&satellite.porcentaje_nubosidad.le(20)].copy()
    d=d[np.isfinite(d.ndwi_promedio)]
    d['week']=((d.date-pd.Timestamp(START)).dt.days//7).astype(int)
    d=d.groupby([ID,'week','date'],as_index=False).ndwi_promedio.median()
    grouped=d.groupby([ID,'week']).agg(ndwi=('ndwi_promedio','median'),observations=('date','nunique')).reset_index()
    grouped.loc[grouped.observations.lt(2),'ndwi']=np.nan
    result=weather.merge(grouped,on=[ID,'week'],how='left',validate='one_to_one')
    result['observations']=result.observations.fillna(0).astype(int)
    return result.merge(calendar()[['week','window']],on='week',validate='many_to_one')

def weighted_quantile(values,weights,q):
    v,w=np.asarray(values),np.asarray(weights)
    valid=np.isfinite(v)&np.isfinite(w)&(w>0)
    if not valid.any(): return np.nan
    v,w=v[valid],w[valid];order=np.argsort(v,kind='stable');v,w=v[order],w[order]
    return float(np.interp(q,(np.cumsum(w)-.5*w)/w.sum(),v,left=v[0],right=v[-1]))

class StressFeatures(TransformerMixin,BaseEstimator):
    def __init__(self,weekly=None,mode='none',semantic_verified=False):
        self.weekly=weekly
        self.mode=mode
        self.semantic_verified=semantic_verified

    def fit(self,X,y=None):
        if self.mode not in ['none','main','interaction']: raise ValueError('Modo de estrés no registrado')
        if self.mode!='none' and not self.semantic_verified: raise ValueError('NDWI vegetal no comprobado')
        self.original_=list(X.columns);self.normalization_={};self.thresholds_={}
        if self.mode=='none': return self
        for window in WINDOWS:
            for column in [f'nasa_vpd_{window}',f's2_ndwi_{window}',f'climate_Tmean_{window}']:
                values=X[column].to_numpy(dtype=float);finite=values[np.isfinite(values)]
                mean=float(finite.mean()) if len(finite) else np.nan
                sd=float(finite.std()) if len(finite) else np.nan
                self.normalization_[column]=(mean,sd)
            training=self.weekly[self.weekly[ID].isin(X.index)&self.weekly.window.eq(window)]
            native=training.drop_duplicates(['cell','week'])
            high=float(native.vpd.quantile(.75)) if native.vpd.notna().any() else np.nan
            measured=training[training.ndwi.notna()].copy()
            counts=measured.groupby(ID).ndwi.transform('count')
            low=weighted_quantile(measured.ndwi,1/counts,.25)
            self.thresholds_[window]=(high,low)
        return self

    def transform(self,X):
        if list(X.columns)!=self.original_: raise ValueError('Esquema de efectos principales incompatible')
        out=X.copy()
        if self.mode=='none': return out
        for window in WINDOWS:
            high,low=self.thresholds_[window]
            for suffix in ['vpd_high','ndwi_low','support']:
                out[f'stress_{suffix}_{window}']=np.nan
            if self.mode=='interaction':
                for left in [f'nasa_vpd_{window}',f'climate_Tmean_{window}']:
                    right=f's2_ndwi_{window}'
                    def z(col):
                        mean,sd=self.normalization_[col]
                        return (X[col]-mean)/sd if np.isfinite(sd) and sd>1e-8 else pd.Series(np.nan,index=X.index)
                    out[f'interaction_{left}_ndwi']=z(left)*z(right)
                out[f'stress_joint_{window}']=np.nan
            for pid in X.index:
                allrows=self.weekly[self.weekly[ID].eq(pid)&self.weekly.window.eq(window)]
                valid=allrows[np.isfinite(allrows.ndwi)&np.isfinite(allrows.vpd)]
                fraction=len(valid)/len(allrows) if len(allrows) else 0.
                out.loc[pid,f'stress_support_{window}']=fraction
                if len(valid)<4 or fraction<.5 or not np.isfinite([high,low]).all(): continue
                a=valid.vpd.gt(high);b=valid.ndwi.lt(low)
                out.loc[pid,f'stress_vpd_high_{window}']=a.mean()
                out.loc[pid,f'stress_ndwi_low_{window}']=b.mean()
                if self.mode=='interaction': out.loc[pid,f'stress_joint_{window}']=(a&b).mean()
        return out
