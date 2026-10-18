import sys
from pathlib import Path
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.common import ROOT,PROJECT,ID,TARGET,SCHEMES,read,save,digest,now
import pandas as pd
import geopandas as gpd
import numpy as np

master=gpd.read_parquet(ROOT/'data/processed/parcels.parquet')
if sys.argv[1]=='population':
    assert len(master)==197 and master[ID].is_unique and master.crs is not None
    assert master.geometry.is_valid.all() and not master.geometry.is_empty.any()
    labeled=master[master[TARGET].notna()]
    assert len(labeled)==138 and len(master)-len(labeled)==59
    assert np.isfinite(labeled[TARGET]).all()
    schemes=pd.read_csv(ROOT/'registry/schemes.csv')
    original=read(ROOT/'registry/scheme-validation.json')
    assert digest(ROOT/'registry/schemes.csv')==original['scheme_hash']
    results={}
    for s in SCHEMES:
        f=schemes[schemes.scheme.eq(s)]
        assert len(f)==138 and f[ID].is_unique and set(f[ID])==set(labeled[ID])
        counts=f.fold.value_counts().sort_index()
        assert {str(k):int(v) for k,v in counts.items()}==original['schemes'][s]['counts']
        assert counts.min()>=15 and 138-counts.max()>=80
        results[s]={'n':len(f),'counts':{str(k):int(v) for k,v in counts.items()},'same_assignments':True}
    save(ROOT/'registry/population-check.json',{'passed':True,'n':197,'labeled':138,'hidden':59,
        'cutoff':'2025-10-31','scheme_hash':original['scheme_hash'],'schemes':results,'at':now()})
    print('Población y particiones verificadas')
elif sys.argv[1]=='protect':
    from importlib.metadata import version
    import joblib
    historical=read(PROJECT/'experiments/ampliacion-cimmyt-20261008/registry/protected-files.json')
    sources={Path(p) for p in historical if Path(p).exists() and Path(p).suffix not in ['.log','.err','.jpg','.html']}
    for p in (PROJECT/'experiments/ampliacion-cimmyt-20261008').rglob('*'):
        if p.is_file() and p.suffix in ['.py','.json','.csv','.joblib','.parquet','.lock','.md','.xml'] and not any(x in p.parts for x in ['.venv','env','tmp','__pycache__','vendor']):
            sources.add(p)
    protected={str(p.resolve()):digest(p) for p in sorted(sources)}
    save(ROOT/'registry/protected-files.json',protected)
    sys.path.insert(0,str(ROOT/'controls/C-activa/src'))
    from agrocebada.common import code_hash
    assert code_hash()==read(ROOT/'controls/C-activa/provenance/procedure.json')['code_hash']
    active=joblib.load(PROJECT/'artifacts/model_selected.joblib')
    columns=[m.named_steps['select'].columns_ for m in active['model'].models]
    expected=['climate_Trange_early','climate_PREC_early','nasa_vpd_middle','landsat_coverage','s2_evi_early','planet_evi_early','s2_ndvi_early','climate_PREC_middle','planet_senescence','climate_Tmean_middle']
    assert columns==[expected]
    runtime={p:version(p) for p in ['numpy','pandas','scipy','scikit-learn','geopandas','rasterio','joblib','pyproj','pyarrow','psutil']}
    save(ROOT/'registry/preparation-receipt.json',{'at':now(),'protected_files':len(protected),'runtime':runtime,
      'control_code_hash':code_hash(),'control_dependency_lock':digest(ROOT/'controls/C-activa/requirements.lock'),
      'active_selected_columns':columns,'available_official_columns':pq_columns if (pq_columns:=list(pd.read_parquet(ROOT/'data/processed/features_monthly_20_10.parquet').columns)) else [],
      'training_started':False,'passed':True})
    print('Entradas protegidas:',len(protected),'columnas activas verificadas:',len(expected))
else:
    raise ValueError('Comprobación desconocida')
