"""Catálogo fijo, transformaciones dentro de train y selección anidada."""
from dataclasses import dataclass,asdict
from itertools import combinations
from functools import cmp_to_key
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator,TransformerMixin,RegressorMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern,WhiteKernel
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from .stress import StressFeatures

@dataclass(frozen=True)
class Recipe:
    family:str
    setting:float=0
    blocks:tuple=()
    source:str='enriched'
    @property
    def id(self): return f'{self.source}:'+('+'.join(self.blocks) or 'base')+f':{self.family}:{self.setting:g}'

class NumericState(TransformerMixin,BaseEstimator):
    def fit(self,X,y=None):
        numeric=X.drop(columns=['Estado'])
        numeric=numeric.replace([np.inf,-np.inf],np.nan)
        medians=numeric.median()
        valid=numeric.notna().mean().ge(.5)&numeric.fillna(medians).std(ddof=0).gt(1e-8)
        self.columns_=list(numeric.columns[valid]);self.medians_=medians.loc[self.columns_]
        self.states_=sorted(X.Estado.unique())
        return self
    def transform(self,X):
        a=X[self.columns_].replace([np.inf,-np.inf],np.nan).fillna(self.medians_).to_numpy(dtype=float)
        states=np.column_stack([X.Estado.eq(s).to_numpy(dtype=float) for s in self.states_])
        return np.column_stack([a,states])

class Reference(RegressorMixin,BaseEstimator):
    def __init__(self,regional=True): self.regional=regional
    def fit(self,X,y):
        y=np.asarray(y,dtype=float)
        self.global_=float(y.mean())
        self.regions_={s:float(y[X.Estado.eq(s).to_numpy()].mean()) for s in X.Estado.unique()}
        return self
    def predict(self,X):
        return np.array([self.regions_.get(s,self.global_) if self.regional else self.global_ for s in X.Estado])

def metric(y,p):
    y,p=np.asarray(y),np.asarray(p)
    return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),
            'r2':float(r2_score(y,p)) if len(y)>1 else None,'bias':float(np.mean(p-y))}

def candidate_grid(blocks=(),source='enriched'):
    return [Recipe('global',source=source),Recipe('regional',source=source)]+[
      Recipe(f,v,tuple(blocks),source) for f,settings in [('ridge',[.1,1.,10.]),('gpr',[1.,5.])] for v in settings]

def catalog(available):
    variants={'W01-O':candidate_grid(source='official'),'W01-E':candidate_grid()}
    declared={'W02':('G',),'W03-M':('M',),'W03-I':('S',),'W04':('R',)}
    omitted={}
    for run,blocks in declared.items():
        needed='S' if blocks==('M',) else blocks[0]
        if needed not in available: omitted[run]=f'Bloque {needed} no admitido por auditoría previa'
        else: variants[run]=candidate_grid(blocks)
    full=[tuple(s) for n in range(4) for s in combinations(['G','S','R'],n)]
    effective=[]
    for blocks in full:
        b=tuple(x for x in blocks if x in available)
        if b not in effective: effective.append(b)
    variants['W05']=[Recipe('global'),Recipe('regional')]+[r for blocks in effective for r in candidate_grid(blocks)[2:]]
    assert len(variants['W05'])<=42 and sum(len(v) for v in variants.values())<=84
    return variants,omitted,[{'blocks':list(b),'effective':list(x for x in b if x in available)} for b in full]

def table(recipe,base,blocks):
    X=base[recipe.source].copy()
    for block in recipe.blocks:
        if block in ['G','R']: X=X.join(blocks[block],validate='one_to_one')
    return X

def pipeline(recipe,weekly,semantic):
    if recipe.family in ['global','regional']: return Reference(recipe.family=='regional')
    mode='interaction' if 'S' in recipe.blocks else 'main' if 'M' in recipe.blocks else 'none'
    model=Ridge(alpha=recipe.setting) if recipe.family=='ridge' else GaussianProcessRegressor(
      kernel=Matern(length_scale=recipe.setting,nu=2.5)+WhiteKernel(.15),optimizer=None,normalize_y=True,random_state=2026)
    return Pipeline([('stress',StressFeatures(weekly,mode,semantic)),('numeric',NumericState()),('scale',StandardScaler()),('model',model)])

def fit(recipe,indices,y,base,blocks,weekly,semantic):
    X=table(recipe,base,blocks).iloc[indices]
    model=pipeline(recipe,weekly,semantic)
    model.fit(X,np.asarray(y)[indices])
    if recipe.family not in ['global','regional']:
        columns=model.named_steps['numeric'].columns_
        for b in recipe.blocks:
            prefixes={'G':['AWC_'],'R':['nasa_solar_'],'S':['interaction_','stress_joint_'],'M':['stress_']}[b]
            if not any(c.startswith(tuple(prefixes)) for c in columns): raise ValueError(f'Bloque {b} sin columnas nuevas informativas en train')
    return model

def cv(recipe,indices,y,groups,base,blocks,weekly,semantic):
    target=np.asarray(y)[indices];g=np.asarray(groups)[indices]
    prediction=np.full(len(indices),np.nan)
    try:
        for fold in np.unique(g):
            train=indices[g!=fold];valid=indices[g==fold]
            model=fit(recipe,train,y,base,blocks,weekly,semantic)
            prediction[g==fold]=model.predict(table(recipe,base,blocks).iloc[valid])
        if not np.isfinite(prediction).all(): raise ValueError('Predicción interna no finita')
        return {'recipe':recipe,'prediction':prediction,'metrics':metric(target,prediction),'valid':True}
    except ValueError as error:
        return {'recipe':recipe,'valid':False,'reason':str(error)}

def improves(candidate,reference,target,states,fold):
    checks={'rmse_2pct':metric(target,candidate)['rmse']<=.98*metric(target,reference)['rmse']+1e-12,
      'two_folds':sum(metric(target[fold==f],candidate[fold==f])['rmse']<metric(target[fold==f],reference[fold==f])['rmse'] for f in np.unique(fold))>=2,
      'state_protection':all(mean_absolute_error(target[states==s],candidate[states==s])<=1.1*mean_absolute_error(target[states==s],reference[states==s])+1e-12 for s in np.unique(states) if (states==s).sum()>=10)}
    return {'passed':bool(all(checks.values())),'checks':{k:bool(v) for k,v in checks.items()}}

def ordered(scores):
    def compare(a,b):
        difference=a['metrics']['rmse']-b['metrics']['rmse']
        if abs(difference)>1e-10: return -1 if difference<0 else 1
        complexity=lambda s:(len(s['recipe'].blocks)+(s['recipe'].family not in ['global','regional']),s['recipe'].id)
        return (complexity(a)>complexity(b))-(complexity(a)<complexity(b))
    return sorted([s for s in scores if s['valid']],key=cmp_to_key(compare))

def select(run,recipes,indices,y,groups,states,base,blocks,weekly,semantic):
    target=np.asarray(y)[indices];state=np.asarray(states)[indices];fold=np.asarray(groups)[indices]
    scores=[cv(r,indices,y,groups,base,blocks,weekly,semantic) for r in recipes]
    refs=ordered([s for s in scores if s['recipe'].family in ['global','regional']])
    if not refs: raise ValueError('Sin referencias internas completas')
    reference=refs[0]
    base_source='official' if run=='W01-O' else 'enriched'
    base_scores=scores if run in ['W01-O','W01-E'] else [cv(r,indices,y,groups,base,blocks,weekly,semantic) for r in candidate_grid(source=base_source)]
    baseline_ref=ordered([s for s in base_scores if s['recipe'].family in ['global','regional']])[0]
    baseline=baseline_ref
    for s in ordered(base_scores):
        if s['recipe'].family not in ['global','regional'] and improves(s['prediction'],baseline_ref['prediction'],target,state,fold)['passed']:
            baseline=s;break
    decisions=[]
    winner=baseline if run=='W05' else reference
    winner_chosen=False
    for score in ordered(scores):
        if score['recipe'].family in ['global','regional']: continue
        regional_check=improves(score['prediction'],reference['prediction'],target,state,fold)
        control_check=improves(score['prediction'],baseline['prediction'],target,state,fold) if run=='W05' and score['recipe'].blocks else {'passed':True,'checks':{}}
        accepted=regional_check['passed'] and control_check['passed']
        decisions.append({'recipe':asdict(score['recipe']),'vs_reference':regional_check,'vs_common_control':control_check,'admitted':accepted})
        if accepted and not winner_chosen:
            winner=score;winner_chosen=True
    summaries=[{'recipe':asdict(s['recipe']),'valid':s['valid'],**({'metrics':s['metrics']} if s['valid'] else {'reason':s['reason']})} for s in scores]
    return winner['recipe'],{'winner':asdict(winner['recipe']),'inner_metrics':winner['metrics'],'reference':asdict(reference['recipe']),
      'common_control':asdict(baseline['recipe']),'decisions':decisions,'scores':summaries,'new_block_admitted':bool(winner['recipe'].blocks) and run=='W05'}
