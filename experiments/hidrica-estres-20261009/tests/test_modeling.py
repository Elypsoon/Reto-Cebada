import numpy as np
import pandas as pd
from hydric.modeling import Reference,NumericState,Recipe,catalog,fit,select,improves

def data():
    n=48;X=pd.DataFrame({'x':np.linspace(0,1,n),'constant':1.,'empty':np.nan,'Estado':['a']*24+['b']*24},index=[f'p{i}' for i in range(n)])
    base={'official':X.copy(),'enriched':X.copy()}
    y=np.sin(X.x.to_numpy()*5)+3;groups=np.arange(n)%4;states=X.Estado.to_numpy()
    radiation=pd.DataFrame({'nasa_solar_early':np.arange(n,dtype=float)**2},index=X.index)
    return base,y,groups,states,{'R':radiation}

def test_train_only_features_and_unseen_state():
    base,y,_,_,blocks=data();indices=np.arange(30)
    a=fit(Recipe('ridge',1),indices,y,base,blocks,None,False)
    altered=y.copy();altered[30:]=1000
    b=fit(Recipe('ridge',1),indices,altered,base,blocks,None,False)
    np.testing.assert_allclose(a.predict(base['enriched'].iloc[30:]),b.predict(base['enriched'].iloc[30:]),atol=0,rtol=0)
    assert a.named_steps['numeric'].columns_==['x']
    ref=Reference().fit(base['enriched'].iloc[:20],y[:20])
    unknown=base['enriched'].iloc[[0]].copy();unknown.Estado='unknown'
    assert ref.predict(unknown)[0]==np.mean(y[:20])

def test_catalog_count_and_prior_exclusions():
    full,omit,subsets=catalog(['G','S','R'])
    assert len(full['W05'])==42 and sum(map(len,full.values()))==84 and len(subsets)==8
    actual,omit,_=catalog(['R'])
    assert len(actual['W05'])==12 and set(omit)=={'W02','W03-M','W03-I'}
    assert all('G' not in r.blocks and 'S' not in r.blocks for r in actual['W05'])

def test_spatial_gate_and_fixed_selection():
    target=np.ones(40)*4;states=np.array(['a']*20+['b']*20);fold=np.arange(40)%4
    reference=target+1
    bad=target.copy();bad[:20]+=1.2
    assert not improves(bad,reference,target,states,fold)['passed']
    assert improves(target+.5,reference,target,states,fold)['passed']
    base,y,groups,states,blocks=data();recipes=catalog(['R'])[0]['W05'];ix=np.arange(32)
    a,receipt=select('W05',recipes,ix,y,groups,states,base,blocks,None,False)
    changed=y.copy();changed[32:]=-999
    b,receipt2=select('W05',recipes,ix,changed,groups,states,base,blocks,None,False)
    assert a==b and receipt==receipt2
