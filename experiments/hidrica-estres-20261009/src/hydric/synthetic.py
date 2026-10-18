import sys,socket,time
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
from threadpoolctl import threadpool_info
from .common import ROOT,save
from .modeling import Recipe,fit,table

if sys.argv[1]=='wait':time.sleep(10)
elif sys.argv[1]=='fit':
    try:socket.create_connection(('127.0.0.1',9),timeout=.1)
    except RuntimeError:blocked=True
    else:raise AssertionError('El proceso no bloquea conexiones IP')
    X=pd.DataFrame({'x':np.linspace(0,1,48),'Estado':['a']*24+['b']*24},index=[f'synthetic-{i}' for i in range(48)])
    y=np.sin(X.x.to_numpy()*5)+4;base={'enriched':X,'official':X};models=[];expected=[]
    with threadpool_limits(limits=2):
        for family,setting in [('ridge',1),('gpr',5)]:
            r=Recipe(family,setting);m=fit(r,np.arange(32),y,base,{},None,False)
            models.append(m);expected.append(m.predict(X.iloc[32:]))
        assert all(x['num_threads']<=2 for x in threadpool_info())
    export=ROOT/'registry/synthetic/predictions.csv'
    pd.DataFrame({'prediction':expected[0]}).to_csv(export,index=False,float_format='%.17g')
    np.testing.assert_allclose(pd.read_csv(export,float_precision='round_trip').prediction,expected[0],atol=1e-10,rtol=0)
    joblib.dump({'models':models,'X':X.iloc[32:],'expected':expected},ROOT/'registry/synthetic/model.joblib')
    save(ROOT/'registry/synthetic/offline.json',{'ip_connections_blocked':blocked,'synthetic':True,'finite':bool(np.isfinite(expected).all()),'threads_verified':True,'float64_export_verified':True})
elif sys.argv[1]=='verify':
    b=joblib.load(ROOT/'registry/synthetic/model.joblib')
    with threadpool_limits(limits=2):
        for model,expected in zip(b['models'],b['expected']):np.testing.assert_allclose(model.predict(b['X']),expected,atol=1e-10,rtol=0)
    save(ROOT/'registry/synthetic/recovery.json',{'passed':True,'atol':1e-10,'rtol':0,'offline':True})
else:raise ValueError('Preflight desconocido')
