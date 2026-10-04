import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
from shapely.geometry import Point
from agrocebada import modeling as m
from agrocebada.inference import validate_contract
from agrocebada.common import ID,CUTOFF,code_hash,dependencies


def test_baselines_never_see_validation_labels():
    p=m.baseline_predictions([2.,4.],["A","A"],["A","B"])
    np.testing.assert_array_equal(p["regional_mean"],[3.,3.])
    np.testing.assert_array_equal(p["global_mean"],[3.,3.])


def test_outer_label_contamination_does_not_change_fitted_pipeline(monkeypatch):
    rng=np.random.default_rng(2026);n=40
    X=pd.DataFrame(rng.normal(size=(n,6)),columns=list("abcdef"))
    X.iloc[0,0]=np.nan
    y=np.arange(n)/10+2.;changed=y.copy();changed[30:]=100000.
    indices=np.arange(30);groups=np.repeat(np.arange(4),10);states=np.repeat("A",n)
    tables={"monthly":X};location=pd.DataFrame({"region__A":np.ones(n)},index=X.index)
    monkeypatch.setattr(m,"candidate_grid",lambda keys:[m.Candidate("monthly","elastic",.05),m.Candidate("monthly","bayesian",0)])
    a=m.select(indices,y,groups,states,tables,{},location,False)
    b=m.select(indices,changed,groups,states,tables,{},location,False)
    assert a["candidates"]==b["candidates"]
    np.testing.assert_array_equal(a["weights"],b["weights"])
    fa=m.fit_selection(a,indices,y,tables,{},location);fb=m.fit_selection(b,indices,changed,tables,{},location)
    np.testing.assert_array_equal(m.predict_selection(fa,a,np.arange(n),tables,{},location),m.predict_selection(fb,b,np.arange(n),tables,{},location))
    assert all((a["weights"]>=0)) and np.isclose(a["weights"].sum(),1)


def test_geographic_groups_use_all_points_and_minimum_sizes():
    d=gpd.GeoDataFrame(geometry=[Point(-98.6+(i%23)*.01,19.5+(i//23)*.01) for i in range(138)],crs=4326)
    groups,xy=m.spatial_groups(d)
    assert len(groups)==138 and len(np.unique(groups))==5
    assert min(np.bincount(groups))>=15 and 138-max(np.bincount(groups))>=80


def test_incompatible_contract_rejected():
    master=pd.DataFrame({ID:[str(i) for i in range(197)]})
    table=pd.DataFrame({"a":np.zeros(197)},index=pd.Index(master[ID]))
    c={"cutoff":CUTOFF,"code_hash":code_hash(),"dependencies":dependencies(),"sources":[],"tables":{"x":{"columns":["a"]}}}
    validate_contract(c,master,{"x":table},{},pd.DataFrame(),False)
    with pytest.raises(ValueError,match="columnas"):
        validate_contract(c,master,{"x":table.rename(columns={"a":"b"})},{},pd.DataFrame(),False)
    c["sources"]=["nasa"]
    with pytest.raises(ValueError,match="fuente"):
        validate_contract(c,master,{"x":table},{},pd.DataFrame(),False)
    c["code_hash"]="incompatible"
    with pytest.raises(ValueError,match="versión"):
        validate_contract(c,master,{"x":table},{},pd.DataFrame(),False)


def test_regional_reference_uses_only_train_and_unseen_state_uses_global():
    X=pd.DataFrame({"region__A":[1,1,0,0],"region__B":[0,0,1,0],"region__C":[0,0,0,1]})
    model=m.make_pipeline(m.Candidate("x","regional_mean",0))
    model.fit(X.iloc[:3],[2.,4.,9.])
    np.testing.assert_allclose(model.predict(X),[3.,3.,9.,5.])
    state_model=model.named_steps["model"]
    np.testing.assert_allclose(state_model.intercept_+X.to_numpy()@state_model.coef_,model.predict(X))


def test_selection_can_keep_regional_reference_when_models_are_noise(monkeypatch):
    n=60;indices=np.arange(n);groups=np.repeat(np.arange(3),20)
    states=np.tile(np.repeat(["A","B"],10),3);y=np.where(states=="A",2.,5.)
    X=pd.DataFrame({"noise":np.random.default_rng(1).normal(size=n)})
    location=pd.get_dummies(pd.Series(states),prefix="region",prefix_sep="__",dtype=float)
    monkeypatch.setattr(m,"candidate_grid",lambda keys:[m.Candidate("x","bayesian",0)])
    s=m.select(indices,y,groups,states,{"x":X},{},location,False)
    assert [c.family for c in s["candidates"]]==["regional_mean"]
    model=m.fit_selection(s,indices,y,{"x":X},{},location)
    np.testing.assert_allclose(m.predict_selection(model,s,indices,{"x":X},{},location),y)


def test_improvement_requires_stable_folds_and_protects_regions():
    y=np.zeros(30);reference=np.ones(30);fold=np.repeat(np.arange(3),10)
    states=np.repeat(["A","B","C"],10)
    assert m.improve(np.full(30,.9),reference,y,states,fold)
    concentrated=np.r_[np.zeros(10),np.ones(20)]
    assert not m.improve(concentrated,reference,y,states,fold)
    harms_region=np.r_[np.full(20,.5),np.full(10,1.2)]
    assert not m.improve(harms_region,reference,y,states,fold)


def test_sources_are_tested_across_families_and_official_route_skips_them(monkeypatch):
    n=60;groups=np.repeat(np.arange(3),20);states=np.repeat("A",n)
    location=pd.DataFrame({"region__A":np.ones(n)})
    X=pd.DataFrame({"a":np.random.default_rng(7).normal(size=n)})
    seen=[];original=m.cv_candidate
    def recorded(c,*args,**kwargs):
        seen.append(c)
        return original(c,*args,**kwargs)
    monkeypatch.setattr(m,"cv_candidate",recorded)
    monkeypatch.setattr(m,"candidate_grid",lambda keys:[m.Candidate("x","elastic",.2),m.Candidate("x","bayesian",0)])
    external={"nasa":pd.DataFrame({"nasa_a":X.a**2})}
    m.select(np.arange(n),X.a.to_numpy(),groups,states,{"x":X},external,location,True)
    assert {c.family for c in seen if c.sources}=={"elastic","bayesian"}
    seen.clear()
    m.select(np.arange(n),X.a.to_numpy(),groups,states,{"x":X},external,location,False)
    assert all(not c.sources for c in seen)


def test_compact_selector_matches_original_redundancy_rule():
    rng=np.random.default_rng(42)
    X=pd.DataFrame(rng.normal(size=(50,30)))
    X[30]=X[0]*2;X.iloc[:10,1]=np.nan;X[31]=1.;y=rng.normal(size=50)
    a=X.fillna(X.median().fillna(0));valid=(X.notna().mean()>=.5)&(a.std()>1e-8)
    rank=a.loc[:,valid].corrwith(pd.Series(y,index=a.index)).abs().fillna(0).sort_values(ascending=False)
    expected=[]
    for c in rank.index:
        if not expected or a[expected].corrwith(a[c]).abs().max()<.95:expected.append(c)
        if len(expected)>=20:break
    assert m.CompactSelector(20).fit(X,y).columns_==expected


def test_inner_validation_holds_out_exactly_one_spatial_group():
    n=60;groups=np.repeat(np.arange(5),12);states=np.tile(["A","B"],n//2)
    location=pd.get_dummies(pd.Series(states),prefix="region",prefix_sep="__",dtype=float)
    X=pd.DataFrame({"x":np.arange(n)})
    y=np.where(states=="A",2.,4.)+np.arange(n)/100
    score=m.cv_candidate(m.Candidate("x","regional_mean",0),np.arange(n),y,groups,{"x":X},{},location)
    assert len(np.unique(score["fold"]))==5
    for fold in np.unique(score["fold"]):
        va=score["fold"]==fold;tr=~va
        assert len(np.unique(groups[va]))==1
        expected=m.baseline_predictions(y[tr],states[tr],states[va])["regional_mean"]
        np.testing.assert_allclose(score["prediction"][va],expected)
