import json
from pathlib import Path
from dataclasses import replace,asdict
import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
import joblib
import shutil
from agrocebada import modeling as m
from agrocebada import robust as r
from agrocebada.common import ROOT,PROCESSED,ARTIFACTS,ID,TARGET,sha256
from agrocebada.inference import explain_components,validate_contract

def sample():
    rng=np.random.default_rng(14);n=72
    states=np.tile(np.repeat(['A','B'],6),6);groups=np.repeat(np.arange(6),12)
    X=pd.DataFrame(rng.normal(size=(n,5)),columns=list('abcde'));X.iloc[0,0]=np.nan
    location=pd.get_dummies(pd.Series(states),prefix='region',prefix_sep='__',dtype=float)
    y=np.where(states=='A',2.,5.)+X.b.to_numpy()*.4+rng.normal(0,.05,n)
    return X,location,y,states,groups

def small_grid(keys):return [m.Candidate('x','gpr',1),m.Candidate('x','catboost',2,kind='regional_correction',alpha=.5)]

def test_active_version_and_explicit_destination():
    assert r.active_intact()
    assert ARTIFACTS.is_relative_to(ROOT) and PROCESSED.is_relative_to(ROOT)
    assert 'AGROCEBADA_ARTIFACTS' in (ROOT/'src/agrocebada/common.py').read_text(encoding='utf-8')

def test_policy_26_six_ablations_four_ensembles_and_hash():
    policy=json.loads((ARTIFACTS/'selection-policy.json').read_text(encoding='utf-8'))
    grid=m.candidate_grid(['monthly_20_10','whittaker_20_10'])
    assert len(grid)==26 and len(set(grid))==26
    assert sum(c.kind=='regional_correction' for c in grid)==16
    assert len(policy['external_ablations'])==6 and len(policy['ensembles'])==4
    receipt=json.loads((ARTIFACTS/'freeze-receipt.json').read_text(encoding='utf-8'))
    assert receipt['policy_hash']==sha256(ARTIFACTS/'selection-policy.json')
    assert receipt['scheme_hash']==sha256(ARTIFACTS/'schemes.csv')

def test_schemes_geometry_only_deterministic_and_principal_exact():
    master=gpd.read_parquet(PROCESSED/'parcels.parquet');master=master[master[TARGET].notna()]
    changed=master.copy();changed[TARGET]=np.arange(len(master))*1000
    for n,angle in [(4,0),(5,45)]:
        a=r.canonical_groups(master,n,angle);b=r.canonical_groups(changed,n,angle)
        np.testing.assert_array_equal(a,b);assert min(np.bincount(a))>=15 and 138-max(np.bincount(a))>=80
        perm=master.sample(frac=1,random_state=5);c=r.canonical_groups(perm,n,angle)
        pd.testing.assert_series_equal(pd.Series(a,index=master[ID]).sort_index(),pd.Series(c,index=perm[ID]).sort_index())
    saved=pd.read_csv(ARTIFACTS/'schemes.csv');old=pd.read_csv(r.Path(r.WORKSPACE['snapshot'])/'artifacts/folds.csv')
    p=saved[saved.scheme.eq('principal-5')].set_index(ID).fold
    np.testing.assert_array_equal(p.reindex(old[ID]),old.spatial_group)
    assert saved.groupby('scheme')[ID].nunique().eq(138).all()

def test_regional_correction_zero_unseen_and_serialization(tmp_path):
    X,location,y,states,groups=sample();raw=X.join(location);raw['region__C']=0.
    c=m.Candidate('x','gpr',1,kind='regional_correction',alpha=0)
    model=m.make_pipeline(c).fit(raw,y);base,correction,unseen=model.decompose(raw)
    np.testing.assert_array_equal(model.predict(raw),base);np.testing.assert_array_equal(correction,0)
    assert all(not column.startswith('region__') for column in model.columns_)
    query=raw.iloc[[0]].copy();query[['region__A','region__B']]=0.;query['region__C']=1.
    assert model.predict(query)[0]==np.mean(y)
    model=m.make_pipeline(replace(c,alpha=.5)).fit(raw,y);path=tmp_path/'component.joblib';joblib.dump(model,path)
    np.testing.assert_allclose(joblib.load(path).predict(raw),model.predict(raw),rtol=0,atol=1e-10)
    assert joblib.load(path).state_means_==model.state_means_
    assert m.make_pipeline(replace(c,alpha=1)).fit(raw,y).predict(query)[0]==np.mean(y)

def test_outer_covariates_and_labels_cannot_change_training_statistics(monkeypatch):
    X,location,y,states,groups=sample();indices=np.arange(48);changed_y=y.copy();changed_y[48:]=99999;changed_X=X.copy();changed_X.iloc[48:]=999999.
    monkeypatch.setattr(m,'candidate_grid',small_grid)
    a=m.select(indices,y,groups,states,{'x':X},{},location,False);b=m.select(indices,changed_y,groups,states,{'x':changed_X},{},location,False)
    assert a['candidates']==b['candidates'] and a['decisions']==b['decisions'] and a['scores']==b['scores']
    np.testing.assert_array_equal(a['weights'],b['weights'])
    fa=m.fit_selection(a,indices,y,{'x':X},{},location);fb=m.fit_selection(b,indices,changed_y,{'x':changed_X},{},location)
    for ma,mb in zip(fa.models,fb.models):assert m.component_statistics(ma)==m.component_statistics(mb)
    query=np.arange(48,72)
    np.testing.assert_array_equal(m.predict_selection(fa,a,query,{'x':X},{},location),m.predict_selection(fb,b,query,{'x':X},{},location))

@pytest.mark.parametrize('family',['gpr','catboost'])
def test_composite_explanation_and_uniform_blend(family):
    X,location,y,states,groups=sample();raw=X.join(location)
    c=m.Candidate('x',family,1 if family=='gpr' else 2,kind='regional_correction',alpha=.5)
    ref=m.Candidate('x','regional_mean',0);models=[m.make_pipeline(c).fit(raw,y),m.make_pipeline(ref).fit(location,y)]
    blend=m.Blend(models,[.5,.5]);selection={'candidates':[c,ref],'weights':np.array([.5,.5])}
    effects,info=explain_components(blend,selection,[raw.iloc[[2]],location.iloc[[2]]])
    expected=.5*models[0].predict(raw.iloc[[2]])[0]+.5*models[1].predict(location.iloc[[2]])[0]
    assert np.isclose(info['prediction'],expected) and np.isclose(info['reference_total']+info['correction_total'],expected)
    assert info['exact_additive']==(family=='catboost')
    assert info['components'][0]['alpha']==.5 and info['components'][0]['weight']==.5
    if family=='gpr':assert 'no aditivas' in info['interpretation']

def mock_reports(ratios=(.97,.97,1.),harm=False):
    return {name:{'valid':True,'metrics':{'regional_mean':{'rmse':1.},'selected':{'rmse':ratio}},'by_state':{'Hidalgo':{'n':36,'selected':{'mae':1.11 if harm else 1.},'regional_mean':{'mae':1.}}}} for name,ratio in zip(r.SCHEMES,ratios)}

def test_promotion_all_conditions_and_invalid_references():
    assert r.promotion(mock_reports(),True)['promote']
    assert not r.promotion(mock_reports(),False)['promote']
    assert not r.promotion(mock_reports((.95,1.,1.)),True)['promote']
    assert not r.promotion(mock_reports((.97,.97,1.),True),True)['promote']
    assert not r.promotion(mock_reports((.9,.9,1.06)),True)['promote']
    reports=mock_reports();reports[r.SCHEMES[1]]['valid']=False;assert not r.promotion(reports,True)['promote']
    for value in [0.,float('nan')]:
        reports=mock_reports();reports[r.SCHEMES[0]]['metrics']['regional_mean']['rmse']=value
        assert not r.promotion(reports,True)['promote'] and r.promotion(reports,True)['invalid']

def test_correction_registry_rejects_residual_exclusion_and_invalid_population():
    master=gpd.read_parquet(PROCESSED/'parcels.parquet');assert r.validate_corrections([],master)
    with pytest.raises(ValueError,match='evidencia'):r.validate_corrections([{'reason':'high_residual'}],master)
    bad=master.copy();bad.loc[bad[TARGET].first_valid_index(),TARGET]=np.nan
    with pytest.raises(ValueError,match='138'):r.validate_corrections([],bad)
    source=PROCESSED/'parcels.parquet'
    row=dict(id=master[ID].iloc[0],field=TARGET,old=2,new=2,source=str(source),reason='verified_original',date='2026-10-03',original_hash=sha256(source),derived_hash=sha256(source),evidence='comparison of original field',version='v1',action='drop_parcel')
    with pytest.raises(ValueError,match='Retirar'):r.validate_corrections([row],master)

def test_hidalgo_audit_and_diagnostic_counts():
    d=pd.read_csv(ARTIFACTS/'diagnostic-historic-parcels.csv')
    assert len(d)==138 and d[ID].is_unique
    assert np.isclose(d.loc[d.Estado.eq('Hidalgo'),'squared_error_share'].sum(),.5420524569626229)
    municipalities=pd.read_csv(ARTIFACTS/'diagnostic-historic-Municipio.csv');assert municipalities.n.sum()==138
    assert (municipalities.small_sample==municipalities.n.lt(10)).all()
    audit=json.loads((ARTIFACTS/'hidalgo-original-review.json').read_text(encoding='utf-8'))
    assert len(audit)==10 and all(not case['discrepancies'] for case in audit)
    for case in audit:
        assert sha256(case['source'])==case['source_hash']
        assert sha256(case['geometry_source'])==case['geometry_source_hash']
        assert all(v['processed']==v['original'] for v in case['fields'].values())

def test_source_combinations_paired_and_order_independent(monkeypatch):
    X,location,y,states,groups=sample();monkeypatch.setattr(m,'candidate_grid',small_grid)
    external={'nasa':pd.DataFrame({'nasa_x':X.a}),'siap':pd.DataFrame({'siap_x':X.b})}
    a=m.select(np.arange(48),y,groups,states,{'x':X},external,location,True)
    b=m.select(np.arange(48),y,groups,states,{'x':X},dict(reversed(list(external.items()))),location,True)
    assert a['candidates']==b['candidates'] and a['decisions']==b['decisions']
    decisions=[d for d in a['decisions'] if 'source' in d];assert len(decisions)==6
    assert {d['source'] for d in decisions}=={'nasa','siap','nasa+siap'}
    assert all('paired_without_sources' in d and 'against_reference' in d for d in decisions)
    official=m.select(np.arange(48),y,groups,states,{'x':X},external,location,False)
    assert all(not c.sources for c in official['candidates']) and all(not s['candidate']['sources'] for s in official['scores'])

def test_calibration_labels_not_in_selection(monkeypatch):
    X,location,y,states,groups=sample();groups=np.repeat(np.arange(3),24);groups[:26]=0;groups[26:49]=1;groups[49:]=2
    monkeypatch.setattr(m,'candidate_grid',small_grid)
    a=m.calibrate(np.arange(72),y,groups,states,{'x':X},{},location);assert a and a['calibration_n']>=25
    changed=y.copy();changed[a['calibration_ids']]+=1000
    b=m.calibrate(np.arange(72),changed,groups,states,{'x':X},{},location)
    assert a['selection']['candidates']==b['selection']['candidates'] and a['selection']['scores']==b['selection']['scores']
    for ma,mb in zip(a['model'].models,b['model'].models):assert m.component_statistics(ma)==m.component_statistics(mb)
    assert b['radius']>a['radius']

def test_tie_prefers_reference_and_source_free_individual():
    scores=[{'candidate':m.Candidate('x','gpr',1,sources=('nasa',)),'rmse':1.},{'candidate':m.Candidate('x','gpr',1),'rmse':1.},{'candidate':m.Candidate('x','regional_mean',0),'rmse':1.+1e-14}]
    assert m.pick_score(scores)['candidate'].family=='regional_mean'
    assert m.pick_score(scores[:2])['candidate'].sources==()
    scores[0]['rmse']=1.-4e-13;scores[-1]['rmse']=1.+4e-13
    assert m.pick_score(scores)['candidate'].family=='regional_mean'


def test_interval_disabled_when_principal_coverage_below_85(monkeypatch,tmp_path):
    """Ejecuta el flujo de exportación con evaluación controlada, conservando fit real."""
    real_artifacts=ARTIFACTS
    # Este caso ejercita r.run histórico: su mock usa el recibo de H01.
    receipt=json.loads((Path(r.WORKSPACE['legacy_root'])/'artifacts/freeze-receipt.json').read_text(encoding='utf-8'))
    for name in ['oof-principal-5.csv','selected-features-principal-5.csv','schemes.csv']:shutil.copy2(real_artifacts/name,tmp_path/name)
    monkeypatch.setattr(r,'ARTIFACTS',tmp_path);monkeypatch.setattr(r,'freeze',lambda:receipt)
    monkeypatch.setattr(r,'active_intact',lambda:True);monkeypatch.setattr(r,'diagnostics',lambda *args:None);monkeypatch.setattr(r,'audit_originals',lambda *args:None)
    controlled=mock_reports()
    for report in controlled.values():report.update(interval={'nominal':.9,'n':138,'valid_n':138,'coverage':.84,'mean_width':2.,'by_state':{}},folds=[],by_area={})
    monkeypatch.setattr(r,'evaluate',lambda name,*args:controlled[name]);monkeypatch.setattr(r,'stress',lambda *args:[])
    selection={'candidates':[m.Candidate('monthly_20_10','regional_mean',0)],'weights':np.ones(1),'decisions':[],'strategy':'individual','inner_rmse':1.,'scores':[],'_raw_scores':[]}
    monkeypatch.setattr(m,'select',lambda *args,**kwargs:selection)
    monkeypatch.setattr(m,'calibrate',lambda *args:{'calibration_n':25,'radius':1.,'selection':selection})
    saved=[];monkeypatch.setattr(r,'save_bundle',lambda name,s,model,interval,*args:saved.append((name,interval)))
    r.run();assert saved==[('selected',None),('official',None)]
    assert not json.loads((tmp_path/'validation.json').read_text(encoding='utf-8'))['interval']['available']


def test_actual_three_oofs_contract_components_and_stress():
    from agrocebada.inference import Predictor
    master=gpd.read_parquet(PROCESSED/'parcels.parquet');expected=set(master.loc[master[TARGET].notna(),ID]);hashes=set()
    for name in r.SCHEMES:
        frame=pd.read_csv(ARTIFACTS/f'oof-{name}.csv');report=json.loads((ARTIFACTS/f'validation-{name}.json').read_text(encoding='utf-8'));hashes.add(report['data_hash'])
        assert len(frame)==138 and frame[ID].is_unique and set(frame[ID])==expected
        for procedure,values in report['metrics'].items():
            assert np.isfinite(frame[procedure]).all()
            for key,value in m.metric(frame[TARGET],frame[procedure]).items():assert np.isclose(value,values[key])
        assert all(f['calibration_n']>=25 for f in report['folds'])
    assert len(hashes)==1
    for name in ['selected','official']:
        p=Predictor(name);candidates=p.bundle['selection']['candidates'];contract=p.contract
        assert contract['prediction_sources']==sorted({s for c in candidates for s in c.sources})
        if name=='official':assert not contract['sources']
        for i,c in enumerate(candidates):
            info=contract['tables'][f'{c.features}__component_{i}']
            assert info['sources']==list(c.sources) and info['kind']==c.kind and info['alpha']==c.alpha
            assert list(m.table_for(c,p.tables,p.external,p.location).columns)==info['columns']
            assert contract['component_statistics'][i]==m.component_statistics(p.bundle['model'].models[i])
    stress=json.loads((ARTIFACTS/'stress.json').read_text(encoding='utf-8'));by_id=master.set_index(ID);projected=master.to_crs(32614).set_index(ID)
    for row in stress:
        if row['kind']=='leave-one-state-out':assert not by_id.loc[row['train_ids'],'Estado'].eq(row['held_out']).any()
        else:
            distances=projected.loc[row['train_ids']].geometry.distance(projected.loc[row['validation_ids']].geometry.union_all())
            assert distances.ge(1000).all()
        if row['status']=='no viable':assert row['reason'] and row['train_n']<80

def test_missing_calibration_support_disables_interval():
    X,location,y,states,groups=sample()
    assert m.calibrate(np.arange(72),y,np.repeat(np.arange(3),24),states,{'x':X},{},location) is None
