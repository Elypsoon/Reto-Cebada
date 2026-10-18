"""Selección espacial anidada con efectos principales e interacciones pareadas."""
import sys
from dataclasses import dataclass,asdict
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from .common import ROOT,ID
from .features import Interactions

sys.path.insert(0,str(ROOT/'controls/C-activa/src'))
from agrocebada import modeling as original


@dataclass(frozen=True)
class Recipe:
    features:str
    family:str
    setting:float=0
    nasa:bool=False
    profile:str=''
    @property
    def key(self):return f'{self.features}:{self.family}:{self.setting:g}:{int(self.nasa)}:{self.profile or "base"}'


def catalog(available):
    profiles=['']+[p for p in ['D','H','M','I'] if p in available]
    keys=['monthly_40_10','whittaker_40_10']
    allrecipes=[Recipe(key,f,value,nasa,p) for p in profiles for key in keys for f,values in [('gpr',[1.,5.]),('elastic',[.05,.2])] for value in values for nasa in [False,True]]
    references=[Recipe(keys[0],'global_mean'),Recipe(keys[0],'regional_mean')]
    variants={'F00':[r for r in allrecipes if r.profile=='']+references}
    requested={'F01':['','D'],'F02':['','H'],'F03':['','M'],'F04':['','M','I']}
    omitted={}
    for run,selected in requested.items():
        needed=selected[-1]
        if needed not in available:omitted[run]=f'Perfil {needed} no viable según auditoría previa'
        else:variants[run]=[r for r in allrecipes if r.profile in selected]+references
    variants['F05']=allrecipes+references
    assert len(variants['F05'])<=82
    return variants,omitted


def table(recipe,tables,nasa,blocks,quality,regions):
    if recipe.family in ['regional_mean','global_mean']:return regions.copy()
    X=tables[recipe.features].copy()
    if len(quality.columns):X=X.join(quality,validate='one_to_one')
    if recipe.nasa:X=X.join(nasa,validate='one_to_one')
    if recipe.profile:
        group='M' if recipe.profile=='I' else recipe.profile
        X=X.join(blocks[group],validate='one_to_one')
    return X


def fit(recipe,indices,y,tables,nasa,blocks,quality,regions,context,semantic):
    X=table(recipe,tables,nasa,blocks,quality,regions)
    historical=original.make_pipeline(original.Candidate(recipe.features,recipe.family,recipe.setting))
    model=Pipeline([('interactions',Interactions(context,recipe.profile=='I',semantic)),*historical.steps])
    model.fit(X.iloc[indices],np.asarray(y)[indices])
    if recipe.profile and recipe.family not in ['regional_mean','global_mean']:
        columns=model.named_steps['select'].columns_
        prefixes={'D':('D_',),'H':('H_',),'M':('D_','H_','M_'),'I':('I_',)}[recipe.profile]
        if not any(c.startswith(prefixes) for c in columns):raise ValueError('Perfil sin variables nuevas utilizadas en train')
    return model


def cv(recipe,indices,y,groups,inputs):
    prediction=np.full(len(indices),np.nan);fold=np.empty(len(indices),dtype=int)
    g=np.asarray(groups)[indices]
    if len(np.unique(g))<2:return {'valid':False,'recipe':recipe,'reason':'Grupos internos insuficientes'}
    try:
        for number,value in enumerate(sorted(np.unique(g))):
            tr=indices[g!=value];va=indices[g==value]
            model=fit(recipe,tr,y,**inputs)
            X=table(recipe,**{k:inputs[k] for k in ['tables','nasa','blocks','quality','regions']})
            prediction[g==value]=model.predict(X.iloc[va]);fold[g==value]=number
        if not np.isfinite(prediction).all():raise ValueError('Predicción interna no finita')
        return {'valid':True,'recipe':recipe,'prediction':prediction,'fold':fold,'rmse':original.metric(np.asarray(y)[indices],prediction)['rmse']}
    except ValueError as error:return {'valid':False,'recipe':recipe,'reason':str(error)}


def select(run,recipes,indices,y,groups,states,inputs):
    scores=[cv(r,indices,y,groups,inputs) for r in recipes]
    valid=[s for s in scores if s['valid']]
    target=np.asarray(y)[indices];state=np.asarray(states)[indices]
    refs=[s for s in valid if s['recipe'].family in ['regional_mean','global_mean']]
    if len(refs)!=2:raise ValueError('Referencias internas incompletas')
    reference=min(refs,key=lambda s:(s['rmse'],s['recipe'].key))
    def improves(a,b):return original.improve(a['prediction'],b['prediction'],target,state,b['fold'])
    eligible=[];decisions=[]
    # Each source choice and each added profile must improve its comparable control.
    for profile in ['', 'D', 'H', 'M', 'I']:
        options=[s for s in valid if s['recipe'].profile==profile and s['recipe'].family not in ['regional_mean','global_mean']]
        official=[s for s in options if not s['recipe'].nasa]
        official_best=min(official,key=lambda s:(s['rmse'],s['recipe'].key)) if official else None
        accepted=[]
        for s in options:
            okay=improves(s,reference)
            if s['recipe'].nasa:
                okay=okay and official_best is not None and improves(s,official_best)
            if profile:
                base=[a for a in eligible if a['recipe'].profile=='']
                control=min(base,key=lambda a:(a['rmse'],a['recipe'].key)) if base else reference
                okay=okay and improves(s,control)
            if profile=='I':
                main=[a for a in eligible if a['recipe'].profile=='M']
                main_control=min(main,key=lambda a:(a['rmse'],a['recipe'].key)) if main else reference
                okay=okay and bool(main) and improves(s,main_control)
            if okay:accepted.append(s)
        eligible.extend(accepted)
        if options:decisions.append({'profile':profile or 'base','accepted_candidates':[s['recipe'].key for s in accepted],'considered':len(options)})
    winner=min(eligible,key=lambda s:(s['rmse'],s['recipe'].key)) if eligible else reference
    # Only the permitted profile set reaches this function; external results never choose it.
    decision={'run':run,'recipe':asdict(winner['recipe']),'winner':winner['recipe'].key,'inner_rmse':float(winner['rmse']),
              'new_profile_admitted':bool(winner['recipe'].profile),'decisions':decisions,
              'rejected':[{ 'recipe':s['recipe'].key,'reason':s.get('reason','No supera admisión interna')} for s in scores if s['recipe'].key not in {a['recipe'].key for a in eligible+refs}],
              'unique_candidates':len(recipes),'internal_only':True}
    return winner['recipe'],decision
