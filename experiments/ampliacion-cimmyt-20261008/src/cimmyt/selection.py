"""Catálogo cerrado y selección anidada con métricas exclusivamente oficiales."""
from dataclasses import asdict, dataclass, is_dataclass
import hashlib
import math
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from .weighted import fit_weighted
from .spatial import keys_hash, support


@dataclass(frozen=True)
class Configuration:
    alpha: float
    influence: float = 0.
    cohort: str | None = None

    @property
    def id(self):
        return f'ridge-{self.cohort or "official"}-lambda{self.influence:g}-alpha{self.alpha:g}'


class NonViable(ValueError):
    pass


def metric(y, prediction):
    y, prediction = np.asarray(y,dtype=float), np.asarray(prediction,dtype=float)
    if len(y) != len(prediction) or not np.isfinite([y,prediction]).all():
        raise ValueError('Métrica requiere vectores completos finitos')
    return {'rmse':float(np.sqrt(mean_squared_error(y,prediction))),
        'mae':float(mean_absolute_error(y,prediction)),'r2':float(r2_score(y,prediction)) if len(y)>1 else None,
        'bias':float((prediction-y).mean()),'n':len(y)}


def public(value):
    if is_dataclass(value): return asdict(value)
    if isinstance(value,dict): return {k:public(v) for k,v in value.items() if not k.startswith('_')}
    if isinstance(value,(tuple,list)): return [public(v) for v in value]
    if isinstance(value,np.ndarray): return value.tolist()
    if isinstance(value,np.generic): return value.item()
    return value


def hashed_order(keys):
    return sorted(keys,key=lambda k:(hashlib.sha256((str(k)+'|2026').encode()).hexdigest(),str(k)))


def group_fraction(frame, fraction):
    if fraction not in [.25,.5,1.]: raise ValueError('Fracción fuera del protocolo')
    groups=hashed_order(frame.dependence_group.unique())
    chosen=set(groups[:math.ceil(fraction*len(groups))])
    return frame[frame.dependence_group.isin(chosen)].copy()


def balanced_context(frame, cap=256):
    if cap != 256: raise ValueError('Límite opcional fuera del protocolo')
    order=hashed_order(frame.dependence_group.unique())
    queues={g:hashed_order(frame.loc[frame.dependence_group.eq(g)].index) for g in order}
    chosen=[]; round_index=0
    while len(chosen)<cap:
        count=0
        for group in order:
            if round_index<len(queues[group]) and len(chosen)<cap:
                chosen.append(queues[group][round_index]);count+=1
        if not count: break
        round_index+=1
    if len(set(chosen)) != len(chosen): raise ValueError('Muestreo duplicó observaciones')
    return frame.loc[chosen].copy()


def gate(prediction, control, y, states, folds):
    baseline=metric(y,control)['rmse']; score=metric(y,prediction)['rmse']
    gain=(baseline-score)/baseline if baseline>0 else 0.
    folds=np.asarray(folds); states=np.asarray(states); y=np.asarray(y)
    wins=sum(metric(y[folds==f],prediction[folds==f])['rmse'] <
        metric(y[folds==f],control[folds==f])['rmse'] for f in sorted(set(folds)))
    state_checks={}
    for state in sorted(set(states)):
        mask=states==state
        if mask.sum()<10: continue
        old=metric(y[mask],control[mask])['mae']; new=metric(y[mask],prediction[mask])['mae']
        state_checks[str(state)]={'n':int(mask.sum()),'control_mae':old,'candidate_mae':new,'passed':new<=old*1.1}
    return {'admitted':bool(gain>=.02 and wins>=2 and all(v['passed'] for v in state_checks.values())),
        'relative_rmse_gain':gain,'inner_folds_won':int(wins),'state_checks':state_checks}


class SelectionEngine:
    def __init__(self, official_X, auxiliary_X, auxiliary, guard):
        self.X=official_X; self.aux_X=auxiliary_X; self.aux=auxiliary; self.guard=guard
        if not self.aux.index.is_unique or not self.aux_X.index.equals(self.aux.index):
            raise ValueError('Contexto auxiliar no alineado')

    def catalog(self):
        result=[Configuration(a) for a in [1.,10.]]; seen=set()
        for cohort in ['C-local','C-mexico']:
            frame,_=self.guard.admit(cohort)
            key=keys_hash(frame.auxiliary_id)
            if key in seen: continue
            seen.add(key)
            result += [Configuration(a,weight,cohort) for weight in [.25,.5,1.] for a in [1.,10.]]
        assert len(result)+2 <= 16
        return result

    def donors(self, config, retained_ids):
        if not config.influence:
            return self.aux.iloc[:0], {'keys':[],'support':support(self.aux.iloc[:0]),'retained_ids':list(retained_ids)}
        rows,contract=self.guard.admit(config.cohort,retained_ids)
        keys=rows.auxiliary_id.tolist()
        if not set(keys).issubset(self.aux.index):
            raise ValueError('Admisión espacial apunta a características auxiliares ausentes')
        return self.aux.loc[keys],contract

    def fit(self, config, train_ids, target, retained_ids=(), donor_override=None):
        train_ids=list(train_ids); retained_ids=list(dict.fromkeys(retained_ids))
        if set(train_ids).intersection(retained_ids): raise ValueError('Entrenamiento incluye parcela retenida')
        donor,admission=self.donors(config,retained_ids)
        if donor_override is not None:
            if not set(donor_override.index).issubset(donor.index): raise ValueError('Muestreo ajeno a donantes admitidos')
            donor=donor_override
            admission={**admission,'sampled_keys':donor.index.tolist(),'sampled_support':support(donor)}
        if config.influence and not support(donor)['viable']:
            raise NonViable('Soporte insuficiente después de exclusión/muestreo: '+str(support(donor)))
        model,contract=fit_weighted(self.X.loc[train_ids],target.loc[train_ids],
            self.aux_X.loc[donor.index] if config.influence else None,
            donor.yield_t_ha if config.influence else None,
            donor.dependence_group.tolist() if config.influence else (),config.influence,config.alpha)
        contract.update(configuration=asdict(config),configuration_id=config.id,
            official_train_ids=train_ids,donor_keys=donor.index.tolist(),
            donor_group_keys=donor.dependence_group.tolist(),admission=admission)
        return model,contract

    def cross_validate(self, config, train_ids, target, folds, retained_ids=()):
        ids=pd.Index(train_ids); part=folds.loc[ids]
        if part.nunique()<2: raise ValueError('Menos de dos folds internos')
        prediction=pd.Series(np.nan,index=ids); fits=[]; models=[]
        for fold in sorted(part.unique()):
            tr=ids[part.ne(fold)]; va=ids[part.eq(fold)]
            held=list(dict.fromkeys([*retained_ids,*va.tolist()]))
            model,contract=self.fit(config,tr,target,held)
            prediction.loc[va]=model.predict(self.X.loc[va])
            fits.append({'fold':int(fold),'validation_ids':va.tolist(),'contract':contract})
            models.append(model)
        scores=metric(target.loc[ids],prediction)
        return {'configuration':config,'configuration_id':config.id,'rmse':scores['rmse'],
            'prediction':prediction.to_numpy(),'folds':part.to_numpy(),'fits':fits,'_models':models}

    def select(self, train_ids, target, folds, states, retained_ids=(), augmented=False):
        configs=self.catalog() if augmented else [Configuration(1.),Configuration(10.)]
        scores=[]; failures=[]
        for config in configs:
            try: scores.append(self.cross_validate(config,train_ids,target,folds,retained_ids))
            except NonViable as error:
                failures.append({'configuration_id':config.id,'reason':str(error),'partial_folds_averaged':False})
        controls=[s for s in scores if s['configuration'].influence==0]
        if len(controls)!=2: raise ValueError('Ambos controles obligatorios')
        minimum=min(s['rmse'] for s in controls)
        control=min([s for s in controls if s['rmse']<=minimum+1e-10],key=lambda s:-s['configuration'].alpha)
        selected=control; decision={'admitted':False,'reason':'No hay candidato ampliado viable'}
        donors=[s for s in scores if s['configuration'].influence>0]
        if donors:
            minimum=min(s['rmse'] for s in donors)
            best=min([s for s in donors if s['rmse']<=minimum+1e-10],key=lambda s:
                (s['configuration'].influence,s['configuration'].cohort!='C-local',-s['configuration'].alpha))
            ids=pd.Index(train_ids)
            decision=gate(best['prediction'],control['prediction'],target.loc[ids],states.loc[ids],folds.loc[ids])
            decision['candidate_id']=best['configuration_id']
            if decision['admitted']: selected=best
        return {'chosen':selected['configuration'],'chosen_id':selected['configuration_id'],
            'control_id':control['configuration_id'],'decision':decision,'scores':scores,'failures':failures,
            'train_ids':list(train_ids),'retained_ids':list(retained_ids),
            'augmented_candidates_viable':len(donors),'used_donors':bool(selected['configuration'].influence)}
