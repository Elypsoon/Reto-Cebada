import re
import numpy as np
import pandas as pd
from scipy.linalg import solve
from .common import START,CUTOFF,ID,DATASET,PROCESSED,write_json
from .spatial import zonal_mean

SENSORS={"Sentinel-2":("s2",["ndvi","evi","ndwi"]),"Planet":("planet",["ndvi","evi","msavi"]),"Landsat":("landsat",["vi6t"])}
WINDOWS={"early":(4,5),"middle":(6,7),"late":(8,10)}


def season(d,year=2025):
    return d[d.date.between(f"{year}-04-01",f"{year}-10-31")].copy()


def integral(dates,values):
    x=(pd.DatetimeIndex(dates)-pd.Timestamp(START)).total_seconds()/86400
    return float(np.trapezoid(np.asarray(values),x)) if len(values)>=2 else np.nan


def reconstruct(g,col,lam=10.):
    g=g.dropna(subset=[col]).sort_values("date").groupby("date",as_index=False).agg({col:"median","porcentaje_nubosidad":"mean"})
    if len(g)<8:
        return pd.DataFrame(),"menos de ocho observaciones"
    if g.date.diff().dt.days.max()>21:
        return pd.DataFrame(),"laguna mayor de 21 días"
    dates=pd.date_range(START,CUTOFF,freq="7D")
    origin=pd.Timestamp(START)
    t=(g.date-origin).dt.total_seconds().to_numpy()/86400
    grid=(dates-origin).days.to_numpy()
    observed=np.rint(t/7).astype(int).clip(0,len(grid)-1)
    weights=np.zeros(len(grid)); sums=np.zeros(len(grid))
    for i,v,c in zip(observed,g[col],g.porcentaje_nubosidad):
        w=max(.01,1-c/100); weights[i]+=w; sums[i]+=w*v
    y=np.divide(sums,weights,out=np.zeros_like(sums),where=weights>0)
    diff=np.diff(np.eye(len(grid)),n=2,axis=0)
    z=solve(np.diag(weights)+lam*diff.T@diff,weights*y,assume_a="pos")
    # Outside observation support is never reported as measured phenology.
    z[(grid<t.min())|(grid>t.max())]=np.nan
    return pd.DataFrame({"date":dates,"value":z,"observed_bin":weights>0}),"válida"


def temporal_features(master,sat,cloud=20,method="monthly",lam=10.):
    out=pd.DataFrame(index=master[ID]);quality=[];curves=[]
    d=season(sat)
    branches={(pid,s):g for (pid,s),g in d.groupby([ID,"sensor"])}
    for sensor,(prefix,indices) in SENSORS.items():
        for pid in master[ID]:
            allrows=branches.get((pid,sensor),d.iloc[:0])
            clean=allrows[allrows.porcentaje_nubosidad.le(cloud)].sort_values("date")
            quality.append({ID:pid,"sensor":sensor,"cloud_threshold":cloud,"observations":len(allrows),"usable":int(clean[f"{indices[0]}_promedio"].count()),"missing_cloud":int(allrows.porcentaje_nubosidad.isna().sum())})
            for ix in indices:
                col=f"{ix}_promedio"
                g=clean.dropna(subset=[col])
                for window,(lo,hi) in WINDOWS.items():
                    out.loc[pid,f"{prefix}_{ix}_{window}"]=g.loc[g.date.dt.month.between(lo,hi),col].median()
                if ix!=indices[0]:
                    continue
                out.loc[pid,f"{prefix}_coverage"]=len(g)
                out.loc[pid,f"{prefix}_spatial_std"]=g[f"{ix}_std"].median()
                curve,status=reconstruct(g,col,lam)
                for r in curve.itertuples():
                    curves.append({ID:pid,"sensor":sensor,"date":r.date,"value":r.value,"observed_bin":r.observed_bin,"cloud_threshold":cloud,"lambda":lam})
                series=g[["date",col]].rename(columns={col:"value"}) if method=="monthly" else curve[["date","value"]] if len(curve) else pd.DataFrame(columns=["date","value"])
                series=series.dropna()
                if len(series)>=2:
                    out.loc[pid,f"{prefix}_auc"]=integral(series.date,series.value)
                    out.loc[pid,f"{prefix}_peak"]=series.value.max()
                    peak=series.loc[series.value.idxmax()]
                    # Reliable phases require independent samples on both sides.
                    support=len(g)>=8 and status=="válida" and series.date.min()<peak.date<series.date.max()
                    if support:
                        out.loc[pid,f"{prefix}_peak_doy"]=peak.date.dayofyear
                        amplitude=series.value.max()-series.value.min()
                        out.loc[pid,f"{prefix}_amplitude"]=amplitude
                        active=series[series.value>=series.value.min()+.5*amplitude]
                        out.loc[pid,f"{prefix}_duration"]=(active.date.max()-active.date.min()).days
                        post=series[series.date>=peak.date]
                        out.loc[pid,f"{prefix}_auc_postpeak"]=integral(post.date,post.value)
                        out.loc[pid,f"{prefix}_senescence"]=(post.value.iloc[-1]-post.value.iloc[0])/max(1,(post.date.iloc[-1]-post.date.iloc[0]).days)
                    else:
                        for name in ["peak_doy","amplitude","duration","auc_postpeak","senescence"]:
                            out.loc[pid,f"{prefix}_{name}"]=np.nan
    return out,pd.DataFrame(quality),pd.DataFrame(curves)


def environmental_features(master):
    out=pd.DataFrame(index=master[ID]);report=[];monthly=[]
    for kind in ["PREC","Tmin","Tmax"]:
        by_month={}
        for p in sorted(DATASET.rglob(f"{kind}_2025_*.tif")):
            month=int(re.search(r'2025_(\d\d)',p.name)[1])
            if not 4<=month<=10:continue
            vals,support=zonal_mean(p,master)
            by_month[month]=vals
            report.append({"file":p.name,"missing":int(np.isnan(vals).sum()),"min_support":float(support.min()),"method":"intersección de celdas ponderada por área UTM14N; sin remuestreo"})
            monthly.extend([{ID:pid,"variable":kind,"month":month,"value":v} for pid,v in zip(master[ID],vals)])
        if len(by_month)!=7:raise ValueError(f"Clima incompleto: {kind}")
        for window,(lo,hi) in WINDOWS.items():
            a=np.stack([v for m,v in by_month.items() if lo<=m<=hi])
            out[f"climate_{kind}_{window}"]=a.sum(axis=0) if kind=="PREC" else a.mean(axis=0)
    for window in WINDOWS:
        lo=out.pop(f"climate_Tmin_{window}");hi=out.pop(f"climate_Tmax_{window}")
        out[f"climate_Tmean_{window}"]=(hi+lo)/2
        out[f"climate_Trange_{window}"]=hi-lo
    for kind,pattern in [("elevation","Elevacion*.tif"),("slope","Pendiente*.tif")]:
        vals,support=zonal_mean(next(DATASET.rglob(pattern)),master)
        out[kind]=vals;report.append({"variable":kind,"missing":int(np.isnan(vals).sum()),"min_support":float(support.min()),"resolution_m":120})
    out["log_area"]=np.log1p(master.AREA_HA.to_numpy())
    write_json(PROCESSED/"raster-extraction.json",report)
    pd.DataFrame(monthly).to_parquet(PROCESSED/"monthly-climate.parquet",index=False)
    return out


def history_audit(master,sat):
    # Crop identity and rotation have not been supplied for previous campaigns.
    rows=[]
    for year in [2022,2023,2024]:
        d=season(sat,year);d=d[d.sensor.eq("Sentinel-2")&d.porcentaje_nubosidad.le(20)]
        counts=d.groupby(ID).ndvi_promedio.count().reindex(master[ID],fill_value=0)
        rows.append({"year":year,"median_valid_observations":float(counts.median()),"minimum":int(counts.min()),"decision":"Contexto disponible; excluido del modelo inicial: cultivo/rotación sin confirmar"})
    write_json(PROCESSED/"history-comparability.json",rows)


def dictionary(columns):
    result=[]
    for c in columns:
        units="índice adimensional"
        if c.startswith("climate_PREC"):units="mm acumulados en ventana"
        elif c.startswith("climate_T"):units="°C; media de promedios mensuales"
        elif c=="elevation":units="m"
        elif c=="slope":units="grados"
        elif c=="log_area":units="log(1 + área en ha)"
        elif "coverage" in c:units="observaciones utilizables"
        elif "doy" in c:units="día del año; pico aproximado"
        elif "duration" in c:units="días sobre media amplitud; aproximación"
        elif "auc" in c:units="índice × días"
        elif "senescence" in c:units="índice/día"
        result.append({"name":c,"units":units,"cutoff":CUTOFF,"role":"predictor","window":"abril–octubre 2025; early=abril/mayo, middle=junio/julio, late=agosto/octubre"})
    return result
