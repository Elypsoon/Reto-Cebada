import argparse
import json
import time
import os
import sys
import subprocess
from pathlib import Path
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
            tables[name]=str((PROCESSED/f"features_{name}.parquet").relative_to(ROOT))
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
    p.add_argument("command",choices=["audit","prepare","train","verify","freeze","robust"])
    p.add_argument("--official-only",action="store_true")
    p.add_argument("--artifact-dir",help="Destino de esta ejecución dentro del paquete experimental")
    a=p.parse_args()
    if a.artifact_dir:
        destination=Path(a.artifact_dir).resolve()
        if not destination.is_relative_to(ROOT):p.error('Destino fuera del paquete experimental')
        if os.environ.get('AGROCEBADA_ARTIFACTS')!=str(destination):
            child=subprocess.run([sys.executable,'-m','agrocebada.cli',*sys.argv[1:]],env=dict(os.environ,AGROCEBADA_ARTIFACTS=str(destination)),check=False)
            raise SystemExit(child.returncode)
    if a.command in ['freeze','robust','train']:
        from .robust import freeze,run
        if a.command=='freeze':freeze()
        else:run(official_only=a.official_only)
        return
    if a.command=="audit":
        PROCESSED.mkdir(parents=True,exist_ok=True);provenance(promote=False);print(json.dumps(audit(load_master(),load_satellite()),ensure_ascii=False,indent=2))
    elif a.command=="prepare":prepare(not a.official_only)
    else:
        from .inference import verify_artifacts
        print(verify_artifacts())


if __name__=="__main__":main()
