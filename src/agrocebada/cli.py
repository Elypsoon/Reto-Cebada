import argparse
import json
import time
import pandas as pd
from .common import PROCESSED,ROOT,ID,write_json,dependencies
from .data import load_master,load_satellite,provenance,audit
from .features import environmental_features,temporal_features,history_audit,dictionary


def prepare(externals=True):
    started=time.perf_counter();PROCESSED.mkdir(parents=True,exist_ok=True)
    provenance(promote=externals)
    master=load_master();sat=load_satellite();audit(master,sat)
    monthly=sat[sat.date.between("2025-04-01","2025-10-31")].copy()
    monthly["month"]=monthly.date.dt.month
    monthly[monthly.porcentaje_nubosidad.le(20)].groupby([ID,"sensor","month"])[[c for c in monthly if c.endswith("_promedio")]].median().to_parquet(PROCESSED/"monthly-satellite.parquet")
    master.to_parquet(PROCESSED/"parcels.parquet",index=False)
    sat.to_parquet(PROCESSED/"satellite.parquet",index=False)
    env=environmental_features(master);history_audit(master,sat)
    env.to_parquet(PROCESSED/"environment.parquet")
    tables={};allcurves=[]
    for cloud in [10,20,40]:
        for method,lam in [("monthly",10),("whittaker",10),("whittaker",100)]:
            name=f"{method}_{cloud}_{lam}"
            print(f"Variables: {name}",flush=True)
            t,q,c=temporal_features(master,sat,cloud,method,lam)
            t=t.join(env,validate="one_to_one")
            t.to_parquet(PROCESSED/f"features_{name}.parquet")
            q.to_parquet(PROCESSED/f"quality_{name}.parquet",index=False)
            tables[name]=(PROCESSED/f"features_{name}.parquet").relative_to(ROOT).as_posix()
            if method=="whittaker":allcurves.append(c)
            if name=="monthly_20_10":write_json(PROCESSED/"feature-dictionary.json",dictionary(t.columns))
    pd.concat(allcurves,ignore_index=True).to_parquet(PROCESSED/"curves.parquet",index=False)
    external_status={"nasa":"desactivado","siap":"desactivado"}
    if externals:
        from .external import nasa_features,siap_history
        for name,func in [("nasa",nasa_features),("siap",siap_history)]:
            try:
                t=func(master);t.to_parquet(PROCESSED/f"external_{name}.parquet")
                external_status[name]="candidato"
            except (ValueError,OSError,KeyError) as e:
                external_status[name]=f"rechazado: {e}"
    write_json(PROCESSED/"feature-configs.json",tables)
    write_json(PROCESSED/"preparation.json",{"rows":len(master),"configs":list(tables),"external_status":external_status,"dependencies":dependencies(),"seconds":time.perf_counter()-started})
    print("Preparación terminada",external_status,flush=True)


def main():
    p=argparse.ArgumentParser(description="AgroCebada: ejecución local reproducible")
    p.add_argument("command",choices=["audit","prepare","train","verify"])
    p.add_argument("--official-only",action="store_true")
    a=p.parse_args()
    if a.command=="audit":
        PROCESSED.mkdir(parents=True,exist_ok=True);provenance(promote=False);print(json.dumps(audit(load_master(),load_satellite()),ensure_ascii=False,indent=2))
    elif a.command=="prepare":prepare(not a.official_only)
    elif a.command=="train":
        from .modeling import train
        train(official_only=a.official_only)
    else:
        from .inference import verify_artifacts
        print(verify_artifacts())


if __name__=="__main__":main()
