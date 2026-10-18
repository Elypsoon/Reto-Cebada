import sys
import socket
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits,threadpool_info
from cimmyt.common import ROOT,save
from cimmyt.weighted import COLUMNS,fit_weighted

folder=ROOT/'registry/synthetic';folder.mkdir(exist_ok=True)
with threadpool_limits(limits=2):
    if sys.argv[1]=='fit':
        rng=np.random.default_rng(2026)
        def x(n):
            values=rng.normal(size=(n,14));values[:,10:]=0.
            values[np.arange(n),10+np.arange(n)%4]=1.
            return pd.DataFrame(values,columns=COLUMNS)
        official=x(138);aux=x(256);query=x(59)
        groups=[f'synthetic_group_{i%16}' for i in range(256)]
        model,contract=fit_weighted(official,4.+official.log_area*.2,aux,4.+aux.log_area*.2,groups,.5,10.)
        prediction=model.predict(query)
        joblib.dump({'model':model,'contract':contract,'query':query,'prediction':prediction},folder/'context.joblib')
        assert max(p['num_threads'] for p in threadpool_info())<=2
        try:socket.create_connection(('127.0.0.1',9),timeout=.1)
        except RuntimeError:network_blocked=True
        else:raise ValueError('El trabajador permitió conexión IP')
        save(folder/'synthetic-fit.json',{'synthetic_only':True,'official_context':138,'auxiliary_context':256,
            'max_context_rows':394,'columns':14,'ip_socket_block_proven':network_blocked,
            'threadpools':threadpool_info(),'new_official_training':False})
    else:
        bundle=joblib.load(folder/'context.joblib')
        np.testing.assert_allclose(bundle['model'].predict(bundle['query']),bundle['prediction'],atol=1e-10,rtol=0)
        save(folder/'synthetic-recovery.json',{'passed':True,'offline':True,'atol':1e-10,'rtol':0,'query_rows':59})
print('Preflight sintético',sys.argv[1],'verificado',flush=True)
