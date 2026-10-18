import numpy as np
import pandas as pd
import pytest
from signalclima.features import calendar,max_dry_run,signal_intervals,Interactions,daily_features,paired_weather
from signalclima.common import ID,WINDOWS


def test_calendar_and_gaps_and_unique_dates():
    cal=calendar();assert len(cal)==16 and cal.days.sum()==214
    assert cal.iloc[-1].days==4 and cal.stop.max()==pd.Timestamp('2025-10-31')
    assert max_dry_run([0,0,np.nan,0,0,0,2,0])==3
    obs=pd.DataFrame({ID:['a']*3,'date':pd.to_datetime(['2025-04-01','2025-04-01','2025-04-02']),'value':[.1,.3,.5],'coverage':[1.,1.,1.]})
    h,q,p,s=signal_intervals(['a','b'],obs)
    assert p[p[ID].eq('a')].iloc[0].dates==2
    assert p[p[ID].eq('a')].iloc[0].signal==pytest.approx(.35)
    assert h.isna().all().all() and q.loc['b','Q_signal_support_early']==0


def test_train_only_interactions_and_semantic_gate():
    X=pd.DataFrame(index=['a','b','c'])
    rows=[]
    for window in WINDOWS:
        X[f'M_vpd_{window}']=[1.,2.,9.];X[f'M_tmean_{window}']=[10.,20.,90.];X[f'H_signal_{window}']=[.1,.2,.9]
        for pid in X.index:
            for i in range(4):rows.append({ID:pid,'window':window,'interval':i,'cell':'shared' if pid in ['a','b'] else 'external','signal':.1+i/10,'vpd':float(i),'tmean':20.})
    context=pd.DataFrame(rows)
    with pytest.raises(ValueError,match='no comprobada'):Interactions(context,True,False).fit(X)
    first=Interactions(context,True,True).fit(X.iloc[:2],[1,2])
    changed=context.copy();changed.loc[changed[ID].eq('c'),['vpd','signal']]=999
    other=Interactions(changed,True,True).fit(X.iloc[:2],[1,2])
    assert first.thresholds_==other.thresholds_ and first.normalization_==other.normalization_
    assert first.thresholds_['early'][0]==pytest.approx(2.25)
    pd.testing.assert_frame_equal(first.transform(X.iloc[:2]),other.transform(X.iloc[:2]))
    unsupported=context.copy();unsupported.loc[unsupported[ID].eq('c'),'signal']=np.nan
    out=Interactions(unsupported,True,True).fit(X.iloc[:2]).transform(X)
    assert np.isnan(out.loc['c','I_joint_fraction_early']) and len(out.filter(like='I_').columns)==9


def test_daily_units_missing_days_and_same_temporal_pairs():
    dates=pd.date_range('2025-04-01','2025-10-31')
    precipitation=pd.DataFrame({'a':np.full(len(dates),2.),'b':np.full(len(dates),2.)},index=dates)
    precipitation.loc['2025-04-01':'2025-04-04','a']=np.nan
    weather=pd.concat([pd.DataFrame({ID:pid,'date':dates,'tmax':30.,'tmean':20.,'vpd':2.,'cell':'shared'}) for pid in ['a','b']],ignore_index=True)
    daily,support=daily_features(['a','b'],precipitation,weather)
    assert daily.shape==(2,9) and daily.loc['b','D_precip_early']==122
    assert np.isnan(daily.loc['a','D_precip_early']) and support.loc['a','early']<.95
    obs=pd.DataFrame({ID:['b']*len(dates),'date':dates,'value':.2,'coverage':1.})
    h,q,p,s=signal_intervals(['a','b'],obs)
    m,context=paired_weather(p,weather)
    assert m.loc['b','M_vpd_early']==2 and np.isnan(m.loc['a','M_vpd_early'])
    assert context[context[ID].eq('b')].signal.notna().all()


def test_zero_variance_and_duration_weighting():
    dates=pd.date_range('2025-04-01','2025-10-31')
    obs=pd.DataFrame({ID:'a','date':dates,'value':np.where(dates>='2025-10-28',1.,0.),'coverage':1.})
    h,q,p,s=signal_intervals(['a'],obs)
    late=p[p.window.eq('late')]
    assert h.loc['a','H_signal_late']==pytest.approx(np.average(late.signal,weights=late.days))
    X=pd.DataFrame(index=['a','b']);context=[]
    for w in WINDOWS:
        for n in ['vpd','tmean']:X[f'M_{n}_{w}']=1.
        X[f'H_signal_{w}']=.1
        context.extend([{ID:pid,'window':w,'interval':j,'cell':'shared','signal':.1,'vpd':1.,'tmean':1.} for pid in X.index for j in [0,1]])
    out=Interactions(pd.DataFrame(context),True,True).fit(X).transform(X)
    assert out.filter(regex='I_(vpd|tmean)').isna().all().all()


def test_absent_signal_keeps_population_and_missing_values():
    h,q,p,s=signal_intervals(['a','b'],pd.DataFrame(columns=[ID,'date','value','coverage']))
    assert h.shape==(2,3) and h.isna().all().all() and not s.any().any()
    assert len(p)==32 and q.filter(like='support').eq(0).all().all()
