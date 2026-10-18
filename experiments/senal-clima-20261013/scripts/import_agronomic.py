from pathlib import Path
import sys
PHASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PHASE/'src'))
from signalclima.common import ROOT,ID,save
from signalclima.agronomic import import_records
import pandas as pd
ids=pd.read_parquet(ROOT/'data/processed/parcels.parquet',columns=[ID])[ID]
result=import_records(sys.argv[1] if len(sys.argv)>1 else None,ids,ROOT/'data/descriptive/agronomic')
save(ROOT/'registry/agronomic-status.json',result)
print('Metadatos descriptivos:',result['status'],'predictores sin cambios')
