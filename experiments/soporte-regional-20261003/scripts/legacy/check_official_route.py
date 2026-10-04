"""Reejecuta la preparación sin externos en otra carpeta; preserva artefactos."""
import json
import pandas as pd
from agrocebada import cli,data,features
from agrocebada.common import ROOT,PROCESSED,ARTIFACTS,write_json

output=ROOT/"verification/official-route/data/processed"
for module in [cli,data,features]:module.PROCESSED=output
cli.prepare(externals=False)
configs=json.loads((PROCESSED/"feature-configs.json").read_text(encoding="utf-8"))
for key,path in configs.items():
    expected=pd.read_parquet(ROOT/path)
    actual=pd.read_parquet(output/f"features_{key}.parquet")
    pd.testing.assert_frame_equal(expected,actual)
report=json.loads((output/"preparation.json").read_text(encoding="utf-8"))
assert all(v=="desactivado" for v in report["external_status"].values())
write_json(ARTIFACTS/"official-route-check.json",{"external_sources_disabled":True,"tables_identical":len(configs),"rows":report["rows"],"seconds":report["seconds"]})
print("Ruta oficial independiente reproducida: nueve tablas idénticas",flush=True)
