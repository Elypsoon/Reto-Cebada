import numpy as np
import pandas as pd
import pytest
from cimmyt.selection import (SelectionEngine, Configuration, NonViable, group_fraction,
    balanced_context, gate, public)
from cimmyt.spatial import support, keys_hash
from cimmyt.weighted import COLUMNS


class Guard:
    def __init__(self,auxiliary,fail_retained=None): self.aux=auxiliary; self.fail=fail_retained
    def admit(self,cohort,retained_ids=()):
        f=self.aux if cohort=='C-mexico' else self.aux.iloc[:20]
        if self.fail in retained_ids: f=f.iloc[:29]
        f=f.reset_index().rename(columns={'index':'auxiliary_id'})
        return f,{'keys':f.auxiliary_id.tolist(),'keys_sha256':keys_hash(f.auxiliary_id),
            'support':support(f),'retained_ids':list(retained_ids)}


def setup_engine(fail=None):
    rng=np.random.default_rng(2026)
    def features(n,index):
        x=pd.DataFrame(rng.normal(size=(n,14)),columns=COLUMNS,index=index)
        state=np.zeros((n,4));state[np.arange(n),np.arange(n)%3]=1.
        x.iloc[:,10:]=state
        return x
    ids=[f'O{i}' for i in range(90)]; aid=[f'cimmyt:{i}' for i in range(40)]
    x=features(90,ids); ax=features(40,aid)
    aux=pd.DataFrame({'yield_t_ha':4.+.4*ax.iloc[:,0], 'dependence_group':[f'g{i%10}' for i in range(40)],
        'year':[2014,2015]*20},index=aid)
    y=pd.Series(4.+.4*x.iloc[:,0]+rng.normal(scale=.1,size=90),index=ids)
    folds=pd.Series(np.arange(90)%3,index=ids)
    states=pd.Series(['PUEBLA','HIDALGO','TLAXCALA']*30,index=ids)
    return SelectionEngine(x,ax,aux,Guard(aux,fail)),y,folds,states


def test_catalog_and_all_fold_inviability():
    engine,y,folds,states=setup_engine('O0')
    assert len(engine.catalog())+2==16
    with pytest.raises(NonViable): engine.cross_validate(Configuration(1.,.25,'C-mexico'),y.index,y,folds)
    result=engine.select(y.index,y,folds,states,augmented=True)
    assert result['augmented_candidates_viable']==0 and not result['used_donors']
    assert len(result['failures'])==12
    assert not any(f['partial_folds_averaged'] for f in result['failures'])


def test_retained_outer_labels_do_not_change_selection_or_predictions():
    engine,y,folds,states=setup_engine()
    tr=y.index[:60]; held=y.index[60:].tolist()
    changed=y.copy();changed.loc[held]=10000.
    a=engine.select(tr,y,folds,states,held,augmented=True)
    b=engine.select(tr,changed,folds,states,held,augmented=True)
    assert public(a)==public(b)
    ma,ca=engine.fit(a['chosen'],tr,y,held)
    mb,cb=engine.fit(b['chosen'],tr,changed,held)
    assert ca==cb
    np.testing.assert_allclose(ma.predict(engine.X.loc[held]),mb.predict(engine.X.loc[held]),atol=0,rtol=0)


def test_retained_inner_labels_do_not_change_that_candidate_fit():
    engine,y,folds,states=setup_engine()
    tr=y.index[folds.ne(0)];held=y.index[folds.eq(0)].tolist()
    changed=y.copy();changed.loc[held]=-999.
    config=Configuration(10.,.5,'C-mexico')
    a,ac=engine.fit(config,tr,y,held);b,bc=engine.fit(config,tr,changed,held)
    assert ac==bc
    np.testing.assert_array_equal(a.predict(engine.X.loc[held]),b.predict(engine.X.loc[held]))
    assert not set(ac['official_train_ids']).intersection(held)
    with pytest.raises(ValueError,match='retenida'): engine.fit(config,y.index,y,held)


def test_official_control_tie_prefers_larger_alpha():
    engine,y,folds,states=setup_engine()
    result=engine.select(y.index,y*0+4.,folds,states)
    assert result['chosen'].alpha==10. and result['chosen'].influence==0.


def test_sampling_preserves_whole_groups_and_no_artificial_repeats():
    engine,*_=setup_engine();frame=engine.aux
    a=group_fraction(frame,.25);b=group_fraction(frame.sample(frac=1,random_state=1),.25)
    assert set(a.index)==set(b.index) and a.dependence_group.nunique()==3
    assert len(a)==12 and set(group_fraction(frame,1.).index)==set(frame.index)
    context=balanced_context(frame)
    assert len(context)==len(frame) and context.index.is_unique
    assert len(set(context.dependence_group.iloc[:10]))==10
    assert set(context.index)==set(balanced_context(frame.sample(frac=1,random_state=5)).index)
    with pytest.raises(NonViable): engine.fit(Configuration(1.,.25,'C-mexico'),engine.X.index,
        pd.Series(4.,index=engine.X.index),donor_override=a)


def test_gate_requires_gain_two_folds_and_state_guard():
    y=np.tile([1.,2.,3.],30);states=np.array(['PUEBLA']*30+['HIDALGO']*30+['TLAXCALA']*30)
    folds=np.arange(90)%3;control=y+1.
    assert gate(y+.5,control,y,states,folds)['admitted']
    assert not gate(y+.99,control,y,states,folds)['admitted']
    bad=y+.2;bad[:30]=y[:30]+1.2
    assert not gate(bad,control,y,states,folds)['admitted']


def test_two_optional_contexts_are_fixed_and_unweighted():
    from cimmyt.optional import context_pair
    engine,y,*_=setup_engine()
    with pytest.raises(NonViable): context_pair(engine,y.index,y)
    original=engine.guard.admit
    engine.guard.admit=lambda cohort,retained_ids=():original('C-mexico',retained_ids)
    pair=context_pair(engine,y.index,y)
    assert set(pair)=={'official_common','official_common_plus_local_cap256'}
    assert len(pair['official_common']['X'])==90
    assert len(pair['official_common_plus_local_cap256']['X'])==130
    assert len(set(pair['official_common_plus_local_cap256']['donor_keys']))==40
    assert list(pair['official_common']['X'].columns)==list(pair['official_common_plus_local_cap256']['X'].columns)
