import json
import pandas as pd
import geopandas as gpd
import plotly.express as px
from agrocebada.common import ROOT,DATASET,PROCESSED,ARTIFACTS,ID,TARGET,sha256,write_json
from agrocebada.data import load_master,load_satellite,audit,provenance
from agrocebada.features import reconstruct,SENSORS
from agrocebada.spatial import zonal_mean
from agrocebada.modeling import spatial_groups

before=json.loads((PROCESSED/"audit.json").read_text(encoding="utf-8"))
manifest=json.loads((PROCESSED/"source-manifest.json").read_text(encoding="utf-8"))
assert all(sha256(ROOT/e["path"])==e["sha256"] for e in manifest)
m=load_master();sat=load_satellite();audit(m,sat)
after=json.loads((PROCESSED/"audit.json").read_text(encoding="utf-8"))
assert before==after
provenance()
assert manifest==json.loads((PROCESSED/"source-manifest.json").read_text(encoding="utf-8"))
tables=json.loads((PROCESSED/"feature-configs.json").read_text(encoding="utf-8"))
for key,p in tables.items():
    t=pd.read_parquet(ROOT/p)
    assert t.shape[0]==197 and 35<=t.shape[1]<=60 and t.index.is_unique and set(t.index)==set(m[ID])
    assert set([ID,TARGET,"CONJUNTO"]).isdisjoint(t.columns)
    assert not any("landsat_ndvi" in c for c in t)
coverage=[]
for kind,pattern in [("elevación","Elevacion*.tif"),("pendiente","Pendiente*.tif")]:
    _,support=zonal_mean(next(DATASET.rglob(pattern)),m)
    coverage.extend({ID:pid,"variable":kind,"coverage":float(v)} for pid,v in zip(m[ID],support))
pd.DataFrame(coverage).to_parquet(PROCESSED/"parcel-raster-coverage.parquet",index=False)
examples=[]
season=sat[sat.date.between("2025-04-01","2025-10-31")]
for (pid,sensor),g in season.groupby([ID,"sensor"]):
    col=SENSORS[sensor][1][0]+"_promedio"
    clean=g[g.porcentaje_nubosidad.le(20)]
    _,status=reconstruct(clean,col)
    examples.append({ID:pid,"sensor":sensor,"status":status,"usable":int(clean[col].count())})
pd.DataFrame(examples).to_csv(ARTIFACTS/"curve-quality.csv",index=False)
train=m[m[TARGET].notna()].copy();groups,xy=spatial_groups(train)
points=train.geometry.representative_point();train["longitud"]=points.x;train["latitud"]=points.y;train["grupo"]=groups.astype(str)
f=px.scatter(train,x="longitud",y="latitud",color="grupo",hover_name=ID,title="Cinco grupos geográficos sin usar rendimientos")
f.update_yaxes(scaleanchor="x")
f.write_html(str(ARTIFACTS/"spatial-folds.html"),include_plotlyjs=True)
write_json(ARTIFACTS/"preparation-check.json",{"official_tables":len(tables),"rows":197,"predictors_by_config":{k:pd.read_parquet(ROOT/p).shape[1] for k,p in tables.items()},"original_hashes_verified":len(manifest),"audit_identical":True,"official_independent_of_external_sources":True,"group_counts":pd.Series(groups).value_counts().sort_index().to_dict(),"curve_examples":pd.DataFrame(examples).groupby("status").first().reset_index().to_dict(orient="records"),"topography_partial_lt95":pd.DataFrame(coverage).query("coverage<.95").groupby("variable").size().to_dict()})
print("Preparación y originales verificados; grupos",pd.Series(groups).value_counts().sort_index().to_dict(),flush=True)
