"""Calendario y variables sin etiquetas; interacciones ajustadas dentro de train."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator,TransformerMixin
from .common import ID,START,CUTOFF,WINDOWS


def calendar(days=14):
    if days not in [7,14]: raise ValueError('Duración no predeclarada')
    rows=[];end=pd.Timestamp(CUTOFF)
    for number,start in enumerate(pd.date_range(START,CUTOFF,freq=f'{days}D')):
        stop=min(start+pd.Timedelta(days=days-1),end)
        middle=start+(stop-start)/2
        window=next(k for k,(a,b) in WINDOWS.items() if a<=middle.month<=b)
        rows.append({'interval':number,'start':start,'stop':stop,'days':(stop-start).days+1,'window':window})
    return pd.DataFrame(rows)


def max_dry_run(values):
    best=current=0
    for v in values:
        current=current+1 if np.isfinite(v) and 0<=v<1 else 0
        best=max(best,current)
    return best


def daily_features(ids,precipitation,weather):
    expected=pd.date_range(START,CUTOFF)
    if not precipitation.index.is_unique or not precipitation.columns.is_unique:
        raise ValueError('Claves/fechas de lluvia duplicadas')
    rain=precipitation.reindex(index=expected,columns=ids)
    out=pd.DataFrame(index=pd.Index(ids,name=ID));support=pd.DataFrame(index=out.index)
    for window,(a,b) in WINDOWS.items():
        dates=expected[(expected.month>=a)&(expected.month<=b)]
        for pid in ids:
            p=rain.loc[dates,pid].astype(float).where(lambda s:s.ge(0))
            w=weather[weather[ID].eq(pid)].set_index('date').reindex(dates)
            if not w.index.is_unique:raise ValueError('Fechas meteorológicas duplicadas')
            fraction=float(p.notna().mean())
            support.loc[pid,window]=fraction
            valid=fraction>=.95 and float(w.tmax.notna().mean())>=.95
            out.loc[pid,f'D_precip_{window}']=float(p.sum(min_count=1)) if valid else np.nan
            out.loc[pid,f'D_dry_run_estimated_{window}']=max_dry_run(p.to_numpy()) if valid else np.nan
            out.loc[pid,f'D_tmax_p95_{window}']=float(w.tmax.quantile(.95)) if valid else np.nan
    return out,support


def signal_intervals(ids,observations,days=14,minimum_area=.8,minimum_intervals=2):
    required={ID,'date','value','coverage'}
    if not required.issubset(observations.columns):raise ValueError('Faltan campos de señal')
    obs=observations.copy();obs['date']=pd.to_datetime(obs.date)
    for column in ['value','coverage']:obs[column]=pd.to_numeric(obs[column],errors='raise')
    obs=obs[obs.date.between(START,CUTOFF)&obs.coverage.ge(minimum_area)&np.isfinite(obs.value)].copy()
    obs=obs.groupby([ID,'date'],as_index=False).agg(value=('value','median'),coverage=('coverage','max'))
    obs['interval']=((obs.date-pd.Timestamp(START)).dt.days//days).astype(int)
    grouped=obs.groupby([ID,'interval']).agg(signal=('value','median'),dates=('date','nunique'),area=('coverage','mean')).reset_index()
    grouped.loc[grouped.dates.lt(2),'signal']=np.nan
    cal=calendar(days)
    grid=pd.MultiIndex.from_product([ids,cal.interval],names=[ID,'interval']).to_frame(index=False)
    pairs=grid.merge(grouped,on=[ID,'interval'],how='left',validate='one_to_one').merge(cal,on='interval',validate='many_to_one')
    pairs['dates']=pairs.dates.fillna(0).astype(int)
    output=pd.DataFrame(index=pd.Index(ids,name=ID));quality=pd.DataFrame(index=output.index);supported=pd.DataFrame(index=output.index)
    for window in WINDOWS:
        frame=pairs[pairs.window.eq(window)]
        for pid in ids:
            allrows=frame[frame[ID].eq(pid)]
            valid=allrows[np.isfinite(allrows.signal)]
            fraction=len(valid)/len(allrows)
            enough=len(valid)>=minimum_intervals and fraction>=.5
            output.loc[pid,f'H_signal_{window}']=np.average(valid.signal,weights=valid.days) if enough else np.nan
            quality.loc[pid,f'Q_signal_support_{window}']=fraction
            quality.loc[pid,f'Q_signal_dates_{window}']=int(allrows.dates.sum())
            quality.loc[pid,f'Q_signal_area_{window}']=float(valid.area.mean()) if len(valid) else np.nan
            supported.loc[pid,window]=enough
    return output,quality,pairs,supported.astype(bool)


def paired_weather(pairs,weather):
    if weather.duplicated([ID,'date']).any():raise ValueError('Clima duplicado por ID y fecha')
    rows=[]
    for q in pairs.itertuples(index=False):
        pid=getattr(q,ID)
        w=weather[weather[ID].eq(pid)&weather.date.between(q.start,q.stop)]
        complete=len(w)==q.days and np.isfinite(w[['vpd','tmean']]).all().all()
        cells=w.cell.drop_duplicates().tolist()
        if len(cells)!=1:raise ValueError('Celda cambiante dentro del intervalo')
        rows.append({ID:pid,'interval':q.interval,'window':q.window,'days':q.days,'signal':q.signal,
                     'vpd':float(w.vpd.mean()) if complete else np.nan,'tmean':float(w.tmean.mean()) if complete else np.nan,'cell':cells[0]})
    context=pd.DataFrame(rows);main=pd.DataFrame(index=pd.Index(pairs[ID].drop_duplicates(),name=ID))
    for window in WINDOWS:
        for pid in main.index:
            allrows=context[context[ID].eq(pid)&context.window.eq(window)]
            valid=allrows[np.isfinite(allrows[['signal','vpd','tmean']]).all(axis=1)]
            enough=len(valid)>=2 and len(valid)>=.5*len(allrows)
            for name in ['vpd','tmean']:
                main.loc[pid,f'M_{name}_{window}']=np.average(valid[name],weights=valid.days) if enough else np.nan
    return main,context


def weighted_quantile(values,weights,q):
    v,w=np.asarray(values,dtype=float),np.asarray(weights,dtype=float)
    valid=np.isfinite(v)&np.isfinite(w)&(w>0)
    if not valid.any():return np.nan
    v,w=v[valid],w[valid];order=np.argsort(v,kind='stable');v,w=v[order],w[order]
    return float(np.interp(q,(np.cumsum(w)-.5*w)/w.sum(),v,left=v[0],right=v[-1]))


class Interactions(TransformerMixin,BaseEstimator):
    def __init__(self,context=None,enabled=False,semantic_verified=False):
        self.context=context;self.enabled=enabled;self.semantic_verified=semantic_verified
    def fit(self,X,y=None):
        self.columns_=list(X.columns);self.normalization_={};self.thresholds_={}
        if not self.enabled:return self
        if not self.semantic_verified:raise ValueError('Señal vegetal no comprobada')
        for window in WINDOWS:
            for name in [f'M_vpd_{window}',f'M_tmean_{window}',f'H_signal_{window}']:
                a=X[name].to_numpy(dtype=float);a=a[np.isfinite(a)]
                self.normalization_[name]=(float(a.mean()),float(a.std())) if len(a) else (np.nan,np.nan)
            training=self.context[self.context[ID].isin(X.index)&self.context.window.eq(window)].copy()
            valid=training[np.isfinite(training[['signal','vpd','tmean']]).all(axis=1)]
            native=valid.drop_duplicates(['cell','interval'])
            counts=valid.groupby(ID).signal.transform('count')
            high=float(native.vpd.quantile(.75)) if len(native) else np.nan
            low=weighted_quantile(valid.signal,1/counts,.25)
            self.thresholds_[window]=(high,low)
        return self
    def transform(self,X):
        if list(X.columns)!=self.columns_:raise ValueError('Esquema de efectos principales diferente')
        out=X.copy()
        if not self.enabled:return out
        def z(name):
            mean,sd=self.normalization_[name]
            return (X[name]-mean)/sd if np.isfinite(sd) and sd>1e-8 else pd.Series(np.nan,index=X.index)
        for window in WINDOWS:
            for name in ['vpd','tmean']:out[f'I_{name}_signal_{window}']=z(f'M_{name}_{window}')*z(f'H_signal_{window}')
            out[f'I_joint_fraction_{window}']=np.nan
            high,low=self.thresholds_[window]
            if not np.isfinite([high,low]).all():continue
            for pid in X.index:
                allrows=self.context[self.context[ID].eq(pid)&self.context.window.eq(window)]
                valid=allrows[np.isfinite(allrows[['signal','vpd','tmean']]).all(axis=1)]
                if len(valid)>=2 and len(valid)>=.5*len(allrows):
                    out.loc[pid,f'I_joint_fraction_{window}']=float(((valid.vpd>high)&(valid.signal<low)).mean())
        return out
