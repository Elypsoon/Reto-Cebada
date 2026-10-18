"""Integrales únicamente dentro de segmentos observados; no une lagunas."""
import numpy as np
import pandas as pd
from scipy.linalg import solve
from .common import ID,START,CUTOFF,PROCESSED,write_json

def reconstruct_segments(g,column,lam=10):
    clean=g[np.isfinite(g[column])].sort_values('date').groupby('date',as_index=False).agg({column:'median','porcentaje_nubosidad':'mean'})
    group=clean.date.diff().dt.days.gt(21).cumsum()
    pieces=[];rows=[];summary=[]
    for sid,part in clean.groupby(group):
        usable=len(part)>=4
        info={'segment':int(sid),'observations':len(part),'start':part.date.min().isoformat(),'end':part.date.max().isoformat(),'usable':usable}
        if usable:
            # Include endpoints exactly; never extrapolate to the global weekly grid.
            dates=pd.DatetimeIndex(sorted(set(pd.date_range(part.date.min(),part.date.max(),freq='7D').tolist()+[part.date.max()])))
            origin=part.date.min();grid=(dates-origin).days.to_numpy();t=(part.date-origin).dt.days.to_numpy()
            observed=np.abs(t[:,None]-grid[None,:]).argmin(axis=1)
            weights=np.zeros(len(grid));sums=np.zeros(len(grid))
            for i,value,cloud in zip(observed,part[column],part.porcentaje_nubosidad):
                w=max(.01,1-cloud/100);weights[i]+=w;sums[i]+=w*value
            diff=np.diff(np.eye(len(grid)),n=2,axis=0)
            z=solve(np.diag(weights)+lam*diff.T@diff,sums,assume_a='pos')
            curve=pd.DataFrame({'date':dates,'value':z,'observed_bin':weights>0,'segment':int(sid)})
            pieces.append((part,curve))
            info.update(supported_days=int(grid[-1]-grid[0]),auc=float(np.trapezoid(z,grid)),observed_bins=int((weights>0).sum()),interpolated_bins=int((weights==0).sum()),max_original_gap_days=int(part.date.diff().dt.days.max()),method='Whittaker local semanal lambda=10',original_dates=part.date.dt.strftime('%Y-%m-%d').tolist())
            rows.extend(curve.to_dict('records'))
        else:info.update(supported_days=0,auc=None,reason='menos de cuatro observaciones distintas')
        summary.append(info)
    return pieces,pd.DataFrame(rows),summary

def segment_features(g,column):
    pieces,curves,report=reconstruct_segments(g,column)
    days=sum(r['supported_days'] for r in report);auc=sum(r['auc'] for r in report if r['auc'] is not None)
    result={'supported_days':days,'supported_auc':auc if days else np.nan,'auc_per_supported_day':auc/days if days else np.nan,'usable_segments':len(pieces)}
    result.update({c:np.nan for c in ['peak_doy','amplitude','duration','auc_postpeak','senescence','local_peak','local_peak_doy']})
    supported=[]
    for original,curve in pieces:
        peak=curve.loc[curve.value.idxmax()]
        before=(original.date<peak.date).sum();after=(original.date>peak.date).sum()
        if before>=2 and after>=2:supported.append((peak,curve))
    if supported:
        peak,curve=max(supported,key=lambda item:item[0].value)
        result['local_peak']=float(peak.value);result['local_peak_doy']=int(peak.date.dayofyear)
        # Seasonal descriptors require one continuous observed support, >=8 samples.
        if len(report)==1 and len(pieces)==1 and len(pieces[0][0])>=8:
            result['peak_doy']=int(peak.date.dayofyear);result['amplitude']=float(curve.value.max()-curve.value.min())
            active=curve[curve.value>=curve.value.min()+.5*result['amplitude']]
            result['duration']=int((active.date.max()-active.date.min()).days)
            post=curve[curve.date>=peak.date];t=(post.date-post.date.min()).dt.days
            result['auc_postpeak']=float(np.trapezoid(post.value,t))
            result['senescence']=float((post.value.iloc[-1]-post.value.iloc[0])/max(1,t.iloc[-1]))
    return result,curves,report

def prepare_segment_tables(master,satellite):
    base=pd.read_parquet(PROCESSED/'features_whittaker_20_10.parquet').copy()
    sensor_indices={'Sentinel-2':('s2','ndvi'),'Planet':('planet','ndvi'),'Landsat':('landsat','vi6t')}
    seasonal=['auc','peak','peak_doy','amplitude','duration','auc_postpeak','senescence']
    base=base.drop(columns=[f'{prefix}_{name}' for prefix,_ in sensor_indices.values() for name in seasonal if f'{prefix}_{name}' in base])
    extra=pd.DataFrame(index=base.index);quality=[];allcurves=[]
    clean=satellite[satellite.date.between(START,CUTOFF)&satellite.porcentaje_nubosidad.le(20)]
    branches={(pid,sensor):g for (pid,sensor),g in clean.groupby([ID,'sensor'])}
    for pid in master[ID]:
        for sensor,(prefix,index) in sensor_indices.items():
            g=branches.get((pid,sensor),clean.iloc[:0]);values,curves,report=segment_features(g,f'{index}_promedio')
            for name,value in values.items():base.loc[pid,f'{prefix}_{name}']=value
            quality.append({ID:pid,'state':master.set_index(ID).loc[pid,'Estado'],'sensor':sensor,'index':index,'segments':report,'missing_seasonal_peak':bool(pd.isna(values['peak_doy'])),'seasonal_peak_absence_reason':'sin soporte continuo y máximo interior acreditado' if pd.isna(values['peak_doy']) else None,'accepted_observations':len(g),'missing_cloud_original':int(satellite.loc[satellite[ID].eq(pid)&satellite.sensor.eq(sensor),'porcentaje_nubosidad'].isna().sum()),'supported_days':values['supported_days']})
            if len(curves):
                curves[ID]=pid;curves['sensor']=sensor;curves['index']=index;allcurves.append(curves)
            for ix in ['evi']+(['msavi'] if sensor=='Planet' else []) if sensor!='Landsat' else []:
                vals,index_curves,index_report=segment_features(g,f'{ix}_promedio')
                quality.append({ID:pid,'state':master.set_index(ID).loc[pid,'Estado'],'sensor':sensor,'index':ix,'segments':index_report,'supported_days':vals['supported_days'],'units':'índice × días respaldados; media en unidades del índice'})
                if len(index_curves):
                    index_curves[ID]=pid;index_curves['sensor']=sensor;index_curves['index']=ix;allcurves.append(index_curves)
                for name in ['supported_auc','auc_per_supported_day']:extra.loc[pid,f'{prefix}_{ix}_{name}']=vals[name]
    base.to_parquet(PROCESSED/'features_segmented_20_10.parquet')
    base.join(extra,validate='one_to_one').to_parquet(PROCESSED/'features_segmented_evi_20_10.parquet')
    pd.concat(allcurves,ignore_index=True).to_parquet(PROCESSED/'segmented-curves.parquet',index=False)
    write_json(PROCESSED/'segmented-quality.json',quality)
    write_json(PROCESSED/'segmented-dictionary.json',{'cutoff':CUTOFF,'cloud':20,'lambda':10,'gap_days':21,'minimum_segment_observations':4,'units':{'supported_auc':'índice × días respaldados','auc_per_supported_day':'índice','supported_days':'días','local_peak_doy':'día del año del máximo local respaldado'},'interpretation':'Integrales de soporte observado; no integral de toda la campaña ni antesis confirmada'})
    configs=__import__('json').loads((PROCESSED/'feature-configs.json').read_text(encoding='utf-8'))
    for key in ['segmented_20_10','segmented_evi_20_10']:configs[key]=f'data/processed/features_{key}.parquet'
    write_json(PROCESSED/'feature-configs.json',configs)
    return base
