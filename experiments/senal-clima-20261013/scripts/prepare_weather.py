from pathlib import Path
import sys
PHASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PHASE/'src'))
from signalclima.common import ROOT,save
from signalclima.weather import local_nasa
import pandas as pd
weather,reports=local_nasa(ROOT/'data/external',pd.read_csv(ROOT/'data/processed/nasa-cells.csv'))
weather.to_parquet(ROOT/'data/processed/weather-daily.parquet',index=False)
save(ROOT/'registry/nasa-audit.json',{'passed':True,'reports':reports,'rows':len(weather),'labels_used':False,'local_frost_claim':False})
print('NASA local verificado:',len(weather),'filas ID/fecha; contexto regional')
