from pathlib import Path
import sys,numpy as np,pandas as pd
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from agrocebada.optional import estimator
from agrocebada.common import PROCESSED,ID,TARGET
folder=root/'runs/E07-v2-monthly_20_10/artifacts'
context=np.load(folder/'training-context.npz')
master=pd.read_parquet(PROCESSED/'parcels.parquet');hidden=master[master[TARGET].isna()]
table=pd.read_parquet(PROCESSED/'features_monthly_20_10.parquet').reindex(hidden[ID])
pred=estimator().fit(context['X'],context['y']).predict(table.to_numpy(dtype=float))
saved=pd.read_csv(folder/'predictions_official_only_59.csv').set_index(ID).reindex(hidden[ID])[TARGET].to_numpy()
print({'dtype':str(pred.dtype),'max_absolute_delta':float(np.max(abs(pred-saved))), 'same_float32':bool(np.array_equal(pred,saved.astype(np.float32))), 'examples':list(zip(pred[:3].astype(float).tolist(),saved[:3].tolist()))},flush=True)
