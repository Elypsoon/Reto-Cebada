"""Variantes predeclaradas; todas sus estadísticas se aprenden en fit."""
from dataclasses import replace
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from . import modeling as m

EXPERIMENT='E00'
MASKS=('s2','planet','s2+planet','all','no_quality')

def keys_for(experiment):
    return ['monthly_20_10', 'whittaker_40_10' if experiment=='E03' else 'segmented_evi_20_10' if experiment=='E04b' else 'segmented_20_10' if experiment in ['E04a','E08'] else 'whittaker_20_10']

def experiment_grid(keys):
    if EXPERIMENT=='E00':return None
    available=list(keys);keys=keys_for(EXPERIMENT)
    if any(k not in available for k in keys):raise ValueError('Tablas incompletas')
    masks=MASKS if EXPERIMENT=='E05' else ('all',)
    direct=[]
    for key in keys:
        for mask in masks:
            for family,settings in [('gpr',[1,5]),('catboost',[2,3])]:
                for setting in settings:
                    noises=[.05,.15,.5] if EXPERIMENT=='E06' and family=='gpr' else [.15]
                    direct.extend(m.Candidate(key,family,setting,mask=mask,noise=noise) for noise in noises)
                    if EXPERIMENT=='E06' and family=='gpr':direct.append(m.Candidate(key,family,setting,mask=mask,optimize=True))
    grid=direct+[replace(c,kind='regional_correction',alpha=a,centered=EXPERIMENT in ['E02','E08']) for c in direct for a in [.5,1.]]
    support='hard' if EXPERIMENT in ['E01a','E08'] else 'soft' if EXPERIMENT=='E01b' else 'none'
    grid=[replace(c,support=support) for c in grid]
    grid.extend(m.Candidate(keys[0],f,0) for f in ['global_mean','regional_mean'])
    assert len(set(grid))==len(grid) and len(grid)<=160
    return grid

def configure(experiment):
    global EXPERIMENT
    EXPERIMENT=experiment

def mask_table(table,mask):
    if mask not in MASKS:raise ValueError('Máscara no declarada')
    if mask=='all':return table
    if mask=='no_quality':return table[[c for c in table if not c.endswith('_coverage')]]
    sensors=set(mask.split('+'))
    return table[[c for c in table if not c.startswith(('s2_','planet_','landsat_')) or c.split('_')[0] in sensors]]

def state_names(X):
    cols=[c for c in X if c.startswith('region__')]
    if not cols:raise ValueError('Faltan estados oficiales para la variante')
    a=X[cols].to_numpy()
    return np.where(a.sum(axis=1)>0,np.asarray(cols)[a.argmax(axis=1)],'__unseen__')

class CenteredCorrection(m.RegionalCorrection):
    def fit(self,X,y):
        states=state_names(X);y=np.asarray(y)
        self.global_mean_=float(y.mean());self.state_means_=pd.Series(y).groupby(states).mean().to_dict();self.training_n_=len(y)
        numeric=X.drop(columns=[c for c in X if c.startswith('region__')])
        self.feature_columns_=numeric.columns[numeric.notna().mean()>=.5].tolist()
        if not self.feature_columns_:raise ValueError('Sin predictores disponibles en train')
        numeric=numeric[self.feature_columns_]
        self.raw_medians_=numeric.median().fillna(0)
        filled=numeric.fillna(self.raw_medians_)
        self.centers_=filled.groupby(states).mean();self.global_center_=filled.mean()
        z=self.transform_features(X)
        base=np.array([self.state_means_[s] for s in states])
        self.correction_=m.direct_pipeline(replace(self.candidate,kind='direct',support='none',centered=False))
        self.correction_.fit(z,y-base);self.columns_=self.correction_.named_steps['select'].columns_
        return self
    def transform_features(self,X):
        states=state_names(X)
        centers=np.array([self.centers_.loc[s].to_numpy() if s in self.centers_.index else self.global_center_.to_numpy() for s in states])
        filled=X[self.feature_columns_].fillna(self.raw_medians_)
        return pd.DataFrame(filled.to_numpy()-centers,index=X.index,columns=self.feature_columns_)
    def decompose(self,X):
        states=state_names(X);seen=np.array([s in self.state_means_ for s in states])
        base=np.array([self.state_means_.get(s,self.global_mean_) for s in states])
        correction=np.where(seen,self.candidate.alpha*self.correction_.predict(self.transform_features(X)),0.)
        return base,correction,~seen

class SupportRegressor(RegressorMixin,BaseEstimator):
    def __init__(self,candidate):self.candidate=candidate
    def fit(self,X,y):
        states=state_names(X);y=np.asarray(y)
        self.state_counts_=pd.Series(states).value_counts().to_dict();self.state_means_=pd.Series(y).groupby(states).mean().to_dict();self.global_mean_=float(y.mean())
        self.feature_columns_=[c for c in X if not c.startswith('region__')]
        c=replace(self.candidate,support='none')
        self.inner_=CenteredCorrection(c) if c.centered else m.RegionalCorrection(c) if c.kind=='regional_correction' else m.direct_pipeline(c)
        self.inner_.fit(X if c.kind=='regional_correction' else X[self.feature_columns_],y)
        return self
    def original(self,X):
        return self.inner_.predict(X if self.candidate.kind=='regional_correction' else X[self.feature_columns_])
    def decompose(self,X):
        states=state_names(X);counts=np.array([self.state_counts_.get(s,0) for s in states]);seen=counts>0
        base=np.array([self.state_means_.get(s,self.global_mean_) for s in states]);original=self.original(X)
        weight=np.where((counts>0)&(counts<10),0.,1.) if self.candidate.support=='hard' else np.divide(counts,counts+10.)
        weight=np.where(seen,weight,1.)
        correction=weight*(original-base)
        return base,correction,~seen
    def predict(self,X):
        base,correction,_=self.decompose(X);return base+correction
    def support_details(self,X):
        states=state_names(X);base,correction,unseen=self.decompose(X)
        rows=[]
        for s,b,p,r,u in zip(states,base,self.original(X),correction,unseen):
            n=self.state_counts_.get(s,0)
            w=1. if not n else float(n>=10) if self.candidate.support=='hard' else n/(n+10)
            rows.append({'state':s,'n':n,'reference':float(b),'raw':float(p),'correction':float(r),'prediction':float(b+r),'transfer':bool(u),'rule':self.candidate.support,'attenuation':w,'alpha_nominal':self.candidate.alpha if self.candidate.kind=='regional_correction' else None,'alpha_effective':0. if u else self.candidate.alpha*w if self.candidate.kind=='regional_correction' else None})
        return rows

def variant_pipeline(c):
    return SupportRegressor(c) if c.support!='none' else CenteredCorrection(c)

def explain_variants(blend,selection,raw_tables):
    composition=[];effects=[]
    for weight,model,c,raw in zip(blend.weights,blend.models,selection['candidates'],raw_tables):
        prediction=float(model.predict(raw)[0]);reference=0.;unseen=False
        if hasattr(model,'decompose'):
            base,correction,missing=model.decompose(raw);reference=float(base[0]);unseen=bool(missing[0])
        elif c.family in ['regional_mean','global_mean']:reference=prediction
        else:correction=np.array([prediction])
        composition.append({'weight':float(weight),'kind':c.kind,'alpha':c.alpha,'reference':reference,'weighted_correction':prediction-reference,'prediction':prediction,'unseen_state':unseen,'support':model.support_details(raw) if hasattr(model,'support_details') else None})
        pipe=m.component_pipeline(model);selector=pipe.named_steps['select']
        for column in m.component_columns(model):
            if column not in raw or column.startswith('region__'):continue
            changed=raw.copy();changed[column]=float(selector.medians_.get(column,0))
            effects.append({'variable':column,'contribution_t_ha':float(weight)*(prediction-float(model.predict(changed)[0]))})
    result=pd.DataFrame(effects,columns=['variable','contribution_t_ha']).groupby('variable',as_index=False).contribution_t_ha.sum()
    pred=sum(c['weight']*c['prediction'] for c in composition);base=sum(c['weight']*c['reference'] for c in composition)
    return result,{'exact_additive':False,'baseline':base,'prediction':pred,'reference_total':base,'correction_total':pred-base,'components':composition,'interpretation':'Sensibilidades no aditivas; referencia más corrección reproduce la predicción; sin causalidad'}
