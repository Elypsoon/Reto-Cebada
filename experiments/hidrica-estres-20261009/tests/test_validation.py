import numpy as np
import pandas as pd
from hydric.common import ID,TARGET,SCHEMES
from hydric.validation import eligibility

def frames():
    x=pd.DataFrame({ID:[f'p{i}' for i in range(138)],TARGET:np.ones(138)*4,'Estado':['a']*69+['b']*69,'spatial_group':np.arange(138)%5,
      'prediction':np.ones(138)*4.5,'regional_mean':np.ones(138)*5})
    active=x.copy();active['selected']=5
    return {s:x.copy() for s in SCHEMES},{s:active.copy() for s in SCHEMES}

def test_eligibility_and_no_activation():
    a,b=frames();r=eligibility(a,b,True,True,True)
    assert r['eligible'] and not r['activated'] and not r['interval_available']
    assert not eligibility(a,b,False,True,True)['eligible']
    del a[SCHEMES[1]]
    assert not eligibility(a,b,True,True,True)['checks']['three_schemes']

def test_worse_scheme_and_state_protection():
    a,b=frames();a[SCHEMES[2]]['prediction']=5.2
    r=eligibility(a,b,True,True,True)
    assert not r['checks']['max_ratio_105'] and not r['checks']['max_active_ratio_105']
    assert not r['checks']['regional_protection']
    a,b=frames();a[SCHEMES[0]].loc[0,TARGET]=999
    assert not eligibility(a,b,True,True,True)['checks']['three_schemes']
