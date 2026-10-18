"""Recorrido completo con población sintética; ninguna etiqueta real se ajusta aquí."""
from types import SimpleNamespace
import numpy as np
import pandas as pd
from cimmyt.common import ID,TARGET,SCHEMES
from cimmyt.selection import SelectionEngine
from cimmyt.weighted import COLUMNS
from cimmyt.spatial import keys_hash,support


def test_comparisons_curves_and_serialized_recovery(tmp_path,monkeypatch):
    from cimmyt import run,selection
    rng=np.random.default_rng(2026);ids=[f'SYNTHETIC_{i}' for i in range(197)]
    aid=[f'cimmyt:synthetic_{i}' for i in range(40)]
    def features(index):
        x=rng.normal(size=(len(index),14));x[:,10:]=0.;x[np.arange(len(index)),10+np.arange(len(index))%3]=1.
        return pd.DataFrame(x,index=index,columns=COLUMNS)
    x=features(ids);ax=features(aid)
    aux=pd.DataFrame({'yield_t_ha':4.+ax.log_area*.2,'dependence_group':[f'g{i%10}' for i in range(40)],
        'year':[2014,2015]*20},index=aid)
    class Guard:
        def admit(self,cohort,retained_ids=()):
            f=aux if cohort=='C-mexico' else aux.iloc[:20]
            f=f.reset_index().rename(columns={'index':'auxiliary_id'})
            return f,{'keys':f.auxiliary_id.tolist(),'keys_sha256':keys_hash(f.auxiliary_id),
                'support':support(f),'retained_ids':list(retained_ids)}
    engine=SelectionEngine(x,ax,aux,Guard())
    master=pd.DataFrame({'Estado':['PUEBLA','HIDALGO','TLAXCALA']*65+['PUEBLA','HIDALGO'],
        'AREA_HA':np.arange(197)+1.,TARGET:4.+x.log_area*.2+rng.normal(scale=.05,size=197)},index=ids)
    master.index.name=ID;master.loc[ids[138:],TARGET]=np.nan
    schemes={s:pd.Series(np.arange(138)%n,index=ids[:138]) for s,n in zip(SCHEMES,[5,4,5])}
    monkeypatch.setattr(run,'ROOT',tmp_path)
    monkeypatch.setattr(run,'load_inputs',lambda:(master,engine,schemes))
    monkeypatch.setattr(run,'Registry',lambda:SimpleNamespace(protocol=lambda:{}))
    # Forzar solamente la rama de donantes en datos sintéticos para probar A03.
    monkeypatch.setattr(selection,'gate',lambda *args:{'admitted':True,'synthetic_branch_exercise':True})
    for name in ['A01','A02','A03']:(tmp_path/f'runs/{name}/artifacts').mkdir(parents=True)
    run.execute_comparison('A01');run.recover('A01')
    run.execute_comparison('A02');run.recover('A02')
    run.execute_curve();run.recover('A03')
    from cimmyt.common import read
    status=read(tmp_path/'runs/A03/artifacts/curve-status.json')
    assert status['applicable_outer_fits']==14
    assert all(r['status']=='non_viable' for r in status['records'] if r['fraction']<1.)
    assert all(r['status']=='completed' and r['reused_A02'] for r in status['records'] if r['fraction']==1.)
    for name in ['A01','A02','A03']:
        assert read(tmp_path/f'runs/{name}/artifacts/fresh-process-check.json')['passed']
