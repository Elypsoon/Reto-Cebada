import json
import numpy as np
import pandas as pd
from .common import EXTERNAL,PROCESSED,ID,write_json
from .features import WINDOWS


def read_nasa():
    frames={};reports=[]
    required={"T2M":"C","T2M_MIN":"C","T2M_MAX":"C","T2MDEW":"C","RH2M":"%","ALLSKY_SFC_SW_DWN":"MJ/m^2/day","WS2M":"m/s","PS":"kPa","PRECTOTCORR":"mm/day"}
    for p in sorted(EXTERNAL.glob("nasa*.json")):
        d=json.loads(p.read_text(encoding="utf-8"))
        f=pd.DataFrame(d["properties"]["parameter"]).replace(d["header"]["fill_value"],np.nan)
        f.index=pd.to_datetime(f.index,format="%Y%m%d")
        if d["header"]["time_standard"]!="LST" or any(d["parameters"].get(c,{}).get("units")!=u for c,u in required.items()):
            raise ValueError("Unidades o tiempo NASA incompatibles")
        expected=pd.date_range("2025-04-01","2025-10-31")
        if not f.index.equals(expected):raise ValueError("Fechas NASA incompletas o duplicadas")
        physical=(f.T2M_MIN<=f.T2M_MAX)&f.T2M.between(-60,60)&f.T2M_MIN.between(-80,60)&f.T2M_MAX.between(-60,70)&f.T2MDEW.between(-80,50)&f.RH2M.between(0,100)&f.PS.between(40,110)&f.WS2M.between(0,100)&f.PRECTOTCORR.between(0,2000)&f.ALLSKY_SFC_SW_DWN.between(0,50)
        coverage=f.notna().mean().min()
        if coverage<.95 or not physical.all():raise ValueError("NASA no supera integridad física/cobertura")
        lon,lat,*_=d["geometry"]["coordinates"]
        frames[(lon,lat)]=f
        reports.append({"file":p.name,"days":len(f),"minimum_coverage":float(coverage),"status":"candidato regional","time":"LST","units":required})
    if len(frames)!=4:raise ValueError("Se esperan cuatro respuestas NASA verificadas")
    return frames,reports


def nasa_features(master):
    frames,reports=read_nasa();points=master.to_crs(32614).geometry.representative_point().to_crs(4326)
    keys=list(frames);assign=[];rows=[];comparison=[]
    climate=pd.read_parquet(PROCESSED/"monthly-climate.parquet")
    for pid,p in zip(master[ID],points):
        # Nearest grid node on the documented regular native coordinate grid.
        key=min(keys,key=lambda k:(p.x-k[0])**2+(p.y-k[1])**2);assign.append({ID:pid,"longitude":key[0],"latitude":key[1]})
        f=frames[key];es=lambda t:.6108*np.exp(17.27*t/(t+237.3))
        vpd=((es(f.T2M_MIN)+es(f.T2M_MAX))/2-es(f.T2MDEW)).clip(lower=0)
        r={ID:pid}
        for window,(lo,hi) in WINDOWS.items():
            ix=f.index.month.to_series(index=f.index).between(lo,hi)
            r[f"nasa_vpd_{window}"]=vpd.loc[ix].mean()
            r[f"nasa_solar_{window}"]=f.loc[ix,"ALLSKY_SFC_SW_DWN"].sum()
        r["nasa_gdd_base0_cap26"]=((f.T2M_MIN.clip(0,26)+f.T2M_MAX.clip(0,26))/2).sum()
        rows.append(r)
        for variable,param in [("Tmax","T2M_MAX"),("Tmin","T2M_MIN")]:
            official=climate[(climate[ID]==pid)&(climate.variable==variable)]
            for q in official.itertuples():
                comparison.append({ID:pid,"variable":variable,"month":q.month,"delta":float(f.loc[f.index.month==q.month,param].mean()-q.value)})
    comparison=pd.DataFrame(comparison)
    assignment=pd.DataFrame(assign);assignment.to_csv(PROCESSED/"nasa-cells.csv",index=False)
    report={"files":reports,"method":"punto representativo; nodo nativo meteorológico más cercano; escala regional","cells_used":assignment.groupby(["longitude","latitude"]).size().reset_index(name="parcels").to_dict(orient="records"),"comparison":comparison.groupby("variable").delta.agg(["mean",lambda x:x.abs().mean(),"min","max"]).rename(columns={"<lambda_0>":"mean_absolute"}).to_dict(),"excluded_variables":{"frost_heat_alerts":"sin evidencia local","ET0":"términos FAO-56 incompletos","direct_temperature_predictors":"conservar CHIRTS; discrepancias de resolución/altitud"}}
    write_json(PROCESSED/"nasa-quality.json",report)
    return pd.DataFrame(rows).set_index(ID)


def siap_history(master):
    selected=[];reports=[]
    pairs=master[["Estado","Municipio"]].drop_duplicates().rename(columns={"Estado":"Nomestado","Municipio":"Nommunicipio"})
    for p in sorted(EXTERNAL.glob("siap_municipal*.csv")):
        d=pd.read_csv(p,encoding="cp1252",low_memory=False)
        col="Nomcultivo Sin Um" if "Nomcultivo Sin Um" in d else "Nomcultivo"
        d=d.rename(columns={col:"crop_name"})
        d=d[d.Idcultivo.eq(5920000)&d.Nommodalidad.eq("Temporal")&d.Nomcicloproductivo.eq("Primavera-Verano")&d.Anio.between(2018,2024)]
        d=d.merge(pairs,on=["Nomestado","Nommunicipio"],validate="many_to_one")
        for c in ["Cosechada","Volumenproduccion"]:d[c]=pd.to_numeric(d[c],errors="raise")
        if not d.Nomunidad.eq("Tonelada").all():raise ValueError("Unidad DGSIAP incompatible")
        selected.append(d);reports.append({"file":p.name,"rows":len(d),"encoding":"CP1252"})
    d=pd.concat(selected,ignore_index=True)
    keys=["Anio","Nomestado","Nommunicipio"]
    agg=d.groupby(keys,as_index=False).agg(area=("Cosechada","sum"),production=("Volumenproduccion","sum"))
    agg["yield"]=agg.production/agg.area.where(agg.area>0)
    if len(agg)!=63 or agg["yield"].isna().any() or agg.groupby(["Nomestado","Nommunicipio"]).Anio.nunique().ne(7).any():raise ValueError("DGSIAP requiere nueve municipios × siete años completos")
    rows=[]
    for (state,municipality),g in agg.groupby(["Nomestado","Nommunicipio"]):
        rows.append({"Estado":state,"Municipio":municipality,"siap_median":g["yield"].median(),"siap_std":g["yield"].std(),"siap_trend":np.polyfit(g.Anio-2018,g["yield"],1)[0]})
    features=master[[ID,"Estado","Municipio"]].merge(pd.DataFrame(rows),on=["Estado","Municipio"],validate="many_to_one").set_index(ID)
    write_json(PROCESSED/"siap-quality.json",{"rows":len(agg),"files":reports,"decision":"candidato histórico municipal; cebada grano, no exclusivamente maltera","years":"2018–2024","keys":"estado + municipio verificado","units":"toneladas/hectáreas cosechadas","excluded":"cierres 2025 y municipio homónimo de Tlaxcala"})
    agg.to_csv(PROCESSED/"siap-history.csv",index=False)
    return features.filter(like="siap_")
