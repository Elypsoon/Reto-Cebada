import json
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
import joblib
from agrocebada import modeling as m,variants as v
from agrocebada.segments import segment_features,reconstruct_segments
from agrocebada.tracking import Registry,compare_frames,read,atomic_json
from agrocebada.common import ID,TARGET,PROCESSED

@pytest.fixture(autouse=True)
def restore_experiment():
    v.configure('E00');yield;v.configure('E00')

def sample():
    rng=np.random.default_rng(2026);n=60
    states=np.repeat(['region__A','region__B','region__C'],20)
    X=pd.DataFrame(rng.normal(size=(n,5)),columns=list('abcde'))
    for state in np.unique(states):X[state]=(states==state).astype(float)
    y=3+X.a.to_numpy()*.2+np.repeat([-.5,.5,0],20)
    return X,y

@pytest.mark.parametrize('experiment,count',[('E00',26),('E01a',26),('E01b',26),('E02',26),('E03',26),('E04a',26),('E04b',26),('E05',122),('E06',62),('E08',26)])
def test_declared_grid(experiment,count):
    v.configure(experiment);grid=m.candidate_grid(v.keys_for(experiment))
    assert len(grid)==count and len(set(grid))==count
    if experiment=='E08':assert all(c.support in ['none','hard'] and not c.optimize and c.mask=='all' and c.noise==.15 for c in grid)

def test_support_counts_and_unknown(tmp_path):
    X,y=sample();train=[0,20,21,22,23,24,25,26,27,28,29]
    c=m.Candidate('x','gpr',1,support='hard')
    model=m.make_pipeline(c).fit(X.iloc[train],y[train])
    assert model.state_counts_['region__A']==1 and model.state_counts_['region__B']==10
    assert model.predict(X.iloc[[1]])[0]==y[0]
    assert np.allclose(model.predict(X.iloc[[30]]),model.original(X.iloc[[30]]))
    assert model.support_details(X.iloc[[40]])[0]['transfer']
    composite=m.make_pipeline(replace(c,kind='regional_correction')).fit(X.iloc[train],y[train])
    assert composite.predict(X.iloc[[40]])[0]==np.mean(y[train])
    for n in [1,9,10]:
        tr=list(range(n))+list(range(20,40));fit=m.make_pipeline(c).fit(X.iloc[tr],y[tr])
        expected=np.mean(y[:n]) if n<10 else fit.original(X.iloc[[15]])[0]
        assert np.isclose(fit.predict(X.iloc[[15]])[0],expected)
    soft=m.make_pipeline(replace(c,support='soft')).fit(X.iloc[train],y[train])
    assert np.isclose(soft.predict(X.iloc[[1]])[0],y[0]+(soft.original(X.iloc[[1]])[0]-y[0])/11)
    joblib.dump(model,tmp_path/'m.joblib');np.testing.assert_array_equal(model.predict(X),joblib.load(tmp_path/'m.joblib').predict(X))

def test_centering_query_batch_and_leakage(tmp_path):
    X,y=sample();indices=np.r_[0:15,20:35,40:55]
    c=m.Candidate('x','gpr',1,kind='regional_correction',centered=True)
    a=m.make_pipeline(c).fit(X.iloc[indices],y[indices]);changed=y.copy();changed[np.setdiff1d(np.arange(60),indices)]=99999
    b=m.make_pipeline(c).fit(X.iloc[indices],changed[indices]);assert m.component_statistics(a)==m.component_statistics(b)
    assert np.isclose(a.predict(X.iloc[[16]])[0],a.predict(X.iloc[[16,36,56]])[0])
    assert np.allclose(a.transform_features(X.iloc[indices]).groupby(v.state_names(X.iloc[indices])).mean(),0)
    joblib.dump(a,tmp_path/'m.joblib');np.testing.assert_allclose(a.predict(X),joblib.load(tmp_path/'m.joblib').predict(X),atol=1e-10)

def test_complete_selection_ignores_outer_labels(monkeypatch):
    X,y=sample();loc=X.filter(regex='^region__');tables={'x':X.drop(columns=loc.columns)};groups=np.tile(np.repeat(np.arange(3),5),4);states=v.state_names(X);tr=np.arange(45)
    grid=[m.Candidate('x','gpr',1,support='hard'),m.Candidate('x','catboost',2,kind='regional_correction',centered=True,support='hard')]
    monkeypatch.setattr(m,'candidate_grid',lambda _:grid)
    changed=y.copy();changed[45:]=100000
    a=m.select(tr,y,groups,states,tables,{},loc,False);b=m.select(tr,changed,groups,states,tables,{},loc,False)
    assert a['candidates']==b['candidates'] and a['scores']==b['scores'] and a['decisions']==b['decisions']

def test_segments_do_not_bridge_gap():
    dates=pd.to_datetime(['2025-04-01','2025-04-08','2025-04-15','2025-04-22','2025-06-01','2025-06-08','2025-06-15','2025-06-22'])
    g=pd.DataFrame({'date':dates,'ndvi_promedio':2.,'porcentaje_nubosidad':0})
    values,curve,report=segment_features(g,'ndvi_promedio')
    assert values['supported_days']==42 and np.isclose(values['supported_auc'],84)
    assert np.isnan(values['peak_doy']) and len(report)==2
    assert not curve.date.between('2025-04-23','2025-05-31').any()

def test_small_and_unbacked_peak():
    dates=pd.date_range('2025-04-01',periods=4,freq='7D');g=pd.DataFrame({'date':dates,'ndvi_promedio':[1,4,2,1],'porcentaje_nubosidad':0})
    values,_,_=segment_features(g,'ndvi_promedio');assert np.isnan(values['local_peak_doy'])
    g=g.iloc[:3];values,curve,report=segment_features(g,'ndvi_promedio');assert curve.empty and values['supported_days']==0 and report[0]['usable']==False

def test_masks_keep_environment_and_spatial_std():
    X=pd.DataFrame({'s2_ndvi_early':[1],'planet_evi_early':[2],'landsat_vi6t_late':[3],'s2_coverage':[9],'s2_spatial_std':[.1],'climate_PREC_early':[100],'log_area':[1]})
    assert list(v.mask_table(X,'s2').columns)==['s2_ndvi_early','s2_coverage','s2_spatial_std','climate_PREC_early','log_area']
    assert 's2_coverage' not in v.mask_table(X,'no_quality') and 's2_spatial_std' in v.mask_table(X,'no_quality')
    pd.testing.assert_frame_equal(v.mask_table(X,'all'),X)

def test_registry_negative_collision_integrity_retry(tmp_path):
    reg=Registry(tmp_path);f=reg.create('E1',{'hypothesis':'prueba'},run_id='run')
    assert read(f/'run.json')['metrics'] is None
    with pytest.raises(FileExistsError):reg.create('E1',{},run_id='run')
    reg.transition('run','running');(f/'artifacts/a.txt').write_text('evidencia')
    reg.finish('run',{'official':{'principal-5':{'rmse':1.,'mae':.8,'bias':.1}}},{'passed':True},{'model_absent':False},{'eligible':False,'activated':False,'reason':'negativo'})
    assert 'negativo' in (reg.folder/'events.jsonl').read_text(encoding='utf-8')
    assert read(f/'run.json')['status']=='completed'
    (f/'artifacts/a.txt').write_text('alterado');reg.publish();assert 'integrity_error' in (reg.folder/'summary.csv').read_text()
    with pytest.raises(ValueError):reg.transition('run','running')
    retry=reg.create('E1',{},retry_of='run');assert read(retry/'run.json')['retry_of']=='run'
    first=reg.revise_interpretation('run','Primera interpretación');second=reg.revise_interpretation('run','Corrección',first)
    assert read(f/'interpretations'/f'{second}.json')['supersedes']==first and (f/'interpretations'/f'{first}.json').exists()

def test_registry_interruption_and_failed_closure(tmp_path):
    reg=Registry(tmp_path);f=reg.create('E1',{},run_id='a');reg.transition('a','running')
    with pytest.raises(ValueError):reg.finish('a',{}, {'passed':False},{},{})
    assert read(f/'run.json')['status']=='running'
    with pytest.raises(ValueError):reg.recover('a',{'different':True})
    reg.transition('a','interrupted','proceso terminado');assert 'interrupted' in (reg.folder/'summary.csv').read_text()
    reg.transition('a','failed','sin checkpoint');assert read(f/'run.json')['status']=='failed'

def test_registry_partial_closure_and_valid_recovery(tmp_path,monkeypatch):
    from agrocebada import tracking
    reg=Registry(tmp_path);folder=reg.create('E1',{},run_id='a');reg.transition('a','running')
    (folder/'artifacts/a.txt').write_text('checkpoint')
    atomic_json(folder/'artifacts/checkpoint.json',{'manifest':{'a.txt':tracking.sha256(folder/'artifacts/a.txt')},'protocol_hash':tracking.sha256(folder/'protocol.json')})
    real=tracking.atomic_json
    def interrupted(path,value):
        if Path(path).name=='artifact-manifest.json':raise OSError('cierre interrumpido después de métricas')
        return real(path,value)
    monkeypatch.setattr(tracking,'atomic_json',interrupted)
    with pytest.raises(OSError):reg.finish('a',{'official':{}},{'passed':True},{},{})
    assert read(folder/'run.json')['status']=='running' and read(folder/'run.json')['metrics'] is None
    monkeypatch.setattr(tracking,'atomic_json',real);reg.recover('a',{})
    assert read(folder/'run.json')['status']=='running'

def test_pair_rejects_wrong_labels_folds():
    a=pd.DataFrame({ID:[str(i) for i in range(138)],TARGET:3.,'Estado':'A','spatial_group':np.arange(138)%3,'selected':3.1})
    assert len(compare_frames(a,a))==138
    for field in [TARGET,'spatial_group']:
        b=a.copy();b.loc[0,field]=999
        with pytest.raises(ValueError):compare_frames(a,b)

def test_gpr_effective_kernel_is_serializable():
    X,y=sample();c=m.Candidate('x','gpr',1,noise=.05,optimize=True)
    model=m.make_pipeline(c).fit(X.drop(columns=X.filter(regex='^region__').columns),y)
    stats=m.component_statistics(model);json.dumps(stats)
    assert 'kernel_effective' in stats

def test_variant_explanation_composition():
    from agrocebada.inference import explain_components
    X,y=sample();c=m.Candidate('x','catboost',2,kind='regional_correction',centered=True,support='hard')
    model=m.make_pipeline(c).fit(X,y);blend=m.Blend([model],[1.])
    _,details=explain_components(blend,{'candidates':[c]},[X.iloc[[1]]])
    assert np.isclose(details['reference_total']+details['correction_total'],model.predict(X.iloc[[1]])[0]) and not details['exact_additive']

def test_intra_state_geometry_is_target_independent():
    from agrocebada.robust import canonical_groups
    master=gpd.read_parquet(PROCESSED/'parcels.parquet');labeled=master[master[TARGET].notna()]
    for state,part in labeled.groupby('Estado'):
        changed=part.copy();changed[TARGET]=999
        np.testing.assert_array_equal(canonical_groups(part,3),canonical_groups(changed,3))
        assert np.ptp(np.bincount(canonical_groups(part,3)))<=1

@pytest.mark.parametrize('experiment',['E05','E06','E08'])
def test_full_variant_selection_does_not_use_outer_data(experiment):
    v.configure(experiment);X,y=sample();location=X.filter(regex='^region__');numeric=X.drop(columns=location.columns).rename(columns={'a':'s2_ndvi_early','b':'planet_ndvi_early','c':'landsat_vi6t_early','d':'climate_PREC','e':'log_area'})
    tables={key:numeric.copy() for key in v.keys_for(experiment)};groups=np.arange(60)//10;states=v.state_names(X);tr=np.arange(50)
    external={'nasa':numeric[['climate_PREC']].rename(columns={'climate_PREC':'nasa_PREC'}),'siap':numeric[['log_area']].rename(columns={'log_area':'siap_history'})} if experiment=='E08' else {}
    a=m.select(tr,y,groups,states,tables,external,location,bool(external));changed=y.copy();changed[50:]=99999
    changed_tables={k:t.copy() for k,t in tables.items()}
    for t in changed_tables.values():t.iloc[50:]=999999
    b=m.select(tr,changed,groups,states,changed_tables,external,location,bool(external))
    assert a['candidates']==b['candidates'] and a['scores']==b['scores'] and a['decisions']==b['decisions']
    np.testing.assert_array_equal(a['weights'],b['weights'])
