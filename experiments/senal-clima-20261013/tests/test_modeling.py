import numpy as np
import pandas as pd
import pytest
from threadpoolctl import threadpool_limits
from signalclima.modeling import Recipe,catalog,select,fit,table
from signalclima.validation import eligibility
from signalclima.common import ID,TARGET,SCHEMES


def synthetic():
    rng=np.random.default_rng(2026);ids=pd.Index([f'a{i}' for i in range(60)],name=ID)
    X=pd.DataFrame(rng.normal(size=(60,4)),index=ids,columns=['x1','x2','x3','x4'])
    signal=np.linspace(-2,2,60)
    return dict(tables={'monthly_40_10':X,'whittaker_40_10':X.copy()},nasa=pd.DataFrame({'nasa_vpd':rng.normal(size=60)},index=ids),
                blocks={'D':pd.DataFrame({'D_precip_early':signal},index=ids)},quality=pd.DataFrame(index=ids),
                regions=pd.DataFrame({'region__A':1.},index=ids),context=pd.DataFrame(),semantic=False),signal+3


def test_catalog_and_outer_labels_cannot_select_model():
    variants,omitted=catalog(['D','H','M','I']);assert len(variants['F05'])==82 and not omitted
    inputs,y=synthetic();groups=np.arange(60)%3;indices=np.arange(45);states=np.array(['A']*60)
    recipes=[Recipe('monthly_40_10','elastic',.05,False,p) for p in ['','D']]+[Recipe('monthly_40_10',f) for f in ['global_mean','regional_mean']]
    other=y.copy();other[45:]=999
    with threadpool_limits(limits=2):
        a,da=select('F01',recipes,indices,y,groups,states,inputs)
        b,db=select('F01',recipes,indices,other,groups,states,inputs)
        assert a==b and da==db
        first=fit(a,indices,y,**inputs);second=fit(b,indices,other,**inputs)
        X=table(a,**{k:inputs[k] for k in ['tables','nasa','blocks','quality','regions']})
        np.testing.assert_allclose(first.predict(X.iloc[45:]),second.predict(X.iloc[45:]),atol=1e-10,rtol=0)


def test_eligibility_requires_real_new_information_and_all_schemes():
    n=138;y=np.arange(n,dtype=float)/100
    frame=pd.DataFrame({ID:[f'a{i}' for i in range(n)],TARGET:y,'Estado':['A']*n,'spatial_group':np.arange(n)%5,'prediction':y+.1,'regional_mean':y+1})
    active=frame.copy();active['selected']=y+.5
    frames={s:frame.copy() for s in SCHEMES};controls={s:active.copy() for s in SCHEMES}
    assert eligibility(frames,controls,True,True,True)['eligible']
    assert not eligibility(frames,controls,False,True,True)['eligible']
    incomplete=frames.copy();incomplete.pop(SCHEMES[1])
    assert not eligibility(incomplete,controls,True,True,True)['eligible']
    harmed=frame.copy();harmed.loc[:19,'Estado']='B';harmed.loc[:19,'prediction']=harmed.loc[:19,TARGET]+2
    assert not eligibility({s:harmed for s in SCHEMES},controls,True,True,True)['eligible']


def test_state_history_cannot_overwrite_completed(tmp_path,monkeypatch):
    import signalclima.common as common
    import signalclima.registry as registry
    monkeypatch.setattr(common,'ROOT',tmp_path);monkeypatch.setattr(registry,'ROOT',tmp_path)
    registry.transition('F00','running');registry.transition('F00','fitted');registry.transition('F00','completed')
    with pytest.raises(ValueError,match='sobrescritura'):registry.transition('F00','running')


def test_internal_admission_rejects_state_harm(monkeypatch):
    import signalclima.modeling as modeling
    n=60;indices=np.arange(n);y=np.zeros(n);states=np.array(['A']*20+['B']*40);groups=np.arange(n)%3
    recipe=Recipe('monthly_40_10','elastic',.05,False,'D')
    recipes=[recipe]+[Recipe('monthly_40_10',f) for f in ['global_mean','regional_mean']]
    def fake_cv(r,*args):
        pred=np.r_[np.full(20,1.2),np.full(40,.1)] if r.profile else np.ones(n)
        return {'valid':True,'recipe':r,'prediction':pred,'fold':groups,'rmse':modeling.original.metric(y,pred)['rmse']}
    monkeypatch.setattr(modeling,'cv',fake_cv)
    winner,decision=select('F01',recipes,indices,y,groups,states,{})
    assert not winner.profile and not decision['new_profile_admitted']


def test_paired_comparisons_align_ids_and_reject_changed_folds():
    from signalclima.comparison import paired
    n=138;y=np.arange(n)/100
    frame=pd.DataFrame({ID:[f'a{i}' for i in range(n)],TARGET:y,'Estado':['A']*n,'spatial_group':np.arange(n)%5,'prediction':y+.1})
    control=frame.iloc[::-1].copy();control['prediction']=control[TARGET]+.5
    rows,report=paired(frame,control)
    assert len(rows)==138 and report['overall']['difference']['rmse']==pytest.approx(-.4)
    assert (rows.absolute_error_difference<0).all()
    control.iloc[0,control.columns.get_loc('spatial_group')]=99
    with pytest.raises(ValueError,match='incompatible'):paired(frame,control)
