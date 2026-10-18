import numpy as np
import pandas as pd
import pytest
from hydric.common import ID,WINDOWS
from hydric.stress import calendar,weekly_observations,StressFeatures,weighted_quantile

def inputs():
    X=pd.DataFrame(index=['a','b','c'])
    for w in WINDOWS:
        X[f'nasa_vpd_{w}']=[1.,2.,3.]
        X[f's2_ndwi_{w}']=[.1,.3,.5]
        X[f'climate_Tmean_{w}']=[10.,12.,14.]
    rows=[]
    for pid in X.index:
        for i,w in enumerate(WINDOWS):
            for week in range(i*8,i*8+8): rows.append({ID:pid,'cell':'same' if pid in ['a','b'] else 'other','week':week,'window':w,'vpd':float(week),'ndwi':float(week)/30})
    return X,pd.DataFrame(rows)

def test_cutoff_duplicates_and_unsupported_week():
    d=pd.DataFrame({ID:['a']*4,'date':pd.to_datetime(['2025-04-01','2025-04-01','2025-04-05','2025-11-01']),
       'sensor':['Sentinel-2']*4,'porcentaje_nubosidad':[0]*4,'ndwi_promedio':[.1,.3,.5,.8]})
    weather=pd.DataFrame({ID:['a','a'],'week':[0,1],'cell':['x','x'],'vpd':[1.,2.]})
    result=weekly_observations(d,weather)
    assert result.observations.tolist()==[2,0]
    assert result.ndwi.iloc[0]==pytest.approx(.35) and np.isnan(result.ndwi.iloc[1])
    assert calendar().stop.max()==pd.Timestamp('2025-10-31')
    assert calendar().start.iloc[0]==pd.Timestamp('2025-04-01')

def test_semantic_gate_and_train_only_statistics():
    X,weekly=inputs()
    with pytest.raises(ValueError,match='no comprobado'): StressFeatures(weekly,'interaction',False).fit(X)
    a=StressFeatures(weekly,'interaction',True).fit(X.iloc[:2],np.array([1,2]))
    changed=X.copy();changed.loc['c']=999
    b=StressFeatures(weekly,'interaction',True).fit(changed.iloc[:2],np.array([1,2]))
    assert a.normalization_==b.normalization_ and a.thresholds_==b.thresholds_
    assert a.thresholds_['early'][0]==pytest.approx(5.25)
    assert len(a.transform(X).filter(like='interaction_').columns)==6
    assert len(a.transform(X).filter(like='stress_joint_').columns)==3
    np.testing.assert_allclose(a.transform(X.iloc[:2]),b.transform(X.iloc[:2]),equal_nan=True)

def test_no_observation_is_missing_not_no_stress():
    X,weekly=inputs();weekly.loc[weekly[ID].eq('c'),'ndwi']=np.nan
    model=StressFeatures(weekly,'interaction',True).fit(X.iloc[:2])
    out=model.transform(X)
    assert np.isnan(out.loc['c','stress_joint_early']) and out.loc['c','stress_support_early']==0
    assert weighted_quantile([1,100],[1,1],.25)==1
    unchanged=StressFeatures(weekly,'none',False).fit(X).transform(X)
    pd.testing.assert_frame_equal(unchanged,X)
