"""Selección anidada: outer-test nunca participa en ajuste ni selección."""
import json
import time
import warnings
from dataclasses import dataclass,asdict,replace
import numpy as np
import pandas as pd
import geopandas as gpd
import joblib
import psutil
from sklearn.base import BaseEstimator,TransformerMixin,RegressorMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import ElasticNet,BayesianRidge
from sklearn.svm import SVR
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern,WhiteKernel
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from catboost import CatBoostRegressor
from threadpoolctl import threadpool_limits
from .common import ROOT,PROCESSED,ARTIFACTS,ID,TARGET,SEED,CUTOFF,write_json,sha256,dependencies,code_hash


class CompactSelector(TransformerMixin,BaseEstimator):
    def __init__(self,k=20):self.k=k
    def fit(self,X,y):
        X=X.copy();self.medians_=X.median().fillna(0)
        a=X.fillna(self.medians_)
        valid=(X.notna().mean()>=.5)&(a.std()>1e-8)
        cols=a.columns[valid].tolist()
        if not cols:raise ValueError("Sin predictores con información en train")
        rank=a[cols].corrwith(pd.Series(np.asarray(y),index=a.index)).abs().fillna(0).sort_values(ascending=False)
        correlations=a[cols].corr().abs()
        self.columns_=[]
        for c in rank.index:
            if not self.columns_ or correlations.loc[self.columns_,c].max()<.95:
                self.columns_.append(c)
            if len(self.columns_)>=self.k:break
        return self
    def transform(self,X):return X[self.columns_].fillna(self.medians_[self.columns_])
    def get_feature_names_out(self,input_features=None):return np.asarray(self.columns_,dtype=object)


class RegionalSelector(TransformerMixin,BaseEstimator):
    """Indicadores oficiales de estado; no seleccionados usando las etiquetas."""
    def fit(self,X,y=None):
        self.columns_=[c for c in X if c.startswith("region__")]
        if not self.columns_:raise ValueError("Faltan indicadores oficiales de estado")
        self.medians_=pd.Series(0.,index=X.columns)
        return self
    def transform(self,X):return X[self.columns_]


class MeanRegressor(RegressorMixin,BaseEstimator):
    def __init__(self,regional=True):self.regional=regional
    def fit(self,X,y):
        a=np.asarray(X);y=np.asarray(y)
        self.intercept_=float(y.mean());self.coef_=np.zeros(a.shape[1])
        if self.regional:
            for j in range(a.shape[1]):
                mask=a[:,j]>0
                if mask.any():self.coef_[j]=y[mask].mean()-self.intercept_
        return self
    def predict(self,X):return self.intercept_+np.asarray(X)@self.coef_


@dataclass(frozen=True)
class Candidate:
    features:str
    family:str
    setting:float
    sources:tuple=()
    geo:bool=False
    kind:str='direct'
    alpha:float=1.
    mask:str='all'
    noise:float=.15
    optimize:bool=False
    support:str='none'
    centered:bool=False


class Blend:
    def __init__(self,models,weights):self.models=models;self.weights=np.asarray(weights)
    def predict(self,X):return np.column_stack([m.predict(X) for m in self.models])@self.weights


def spatial_groups(master,n=5):
    pts=master.to_crs(32614).geometry.representative_point()
    xy=np.column_stack([pts.x,pts.y]);blocks=[np.arange(len(master))]
    # Balanced axis-aligned geographic partitions; no target information.
    while len(blocks)<n:
        i=max(range(len(blocks)),key=lambda i:len(blocks[i]))
        b=blocks.pop(i);axis=int(np.ptp(xy[b],axis=0).argmax());order=b[np.argsort(xy[b,axis],kind="stable")]
        mid=len(order)//2;blocks.extend([order[:mid],order[mid:]])
    groups=np.empty(len(master),dtype=int)
    for i,b in enumerate(blocks):groups[b]=i
    if min(map(len,blocks))<15 or len(master)-max(map(len,blocks))<80:
        if n==5:return spatial_groups(master,4)
        raise ValueError("Particiones espaciales sin tamaño mínimo")
    return groups,xy


def metric(y,p):
    return {"rmse":float(np.sqrt(mean_squared_error(y,p))),"mae":float(mean_absolute_error(y,p)),"r2":float(r2_score(y,p)) if len(y)>1 else None}


def direct_pipeline(c):
    if c.family in ["regional_mean","global_mean"]:
        return Pipeline([("select",RegionalSelector()),("scale",StandardScaler(with_mean=False,with_std=False)),("model",MeanRegressor(c.family=="regional_mean"))])
    if c.family=="elastic":model=ElasticNet(alpha=c.setting,l1_ratio=.25,max_iter=10000)
    elif c.family=="bayesian":model=BayesianRidge()
    elif c.family=="svr":model=SVR(C=c.setting,epsilon=.1,gamma="scale")
    elif c.family=="catboost":model=CatBoostRegressor(depth=int(c.setting),iterations=220,learning_rate=.03,l2_leaf_reg=10,loss_function="RMSE",random_seed=SEED,thread_count=2,verbose=False,allow_writing_files=False)
    elif c.family=="gpr":
        kernel=(Matern(length_scale=c.setting,length_scale_bounds=(.3,30),nu=2.5)+WhiteKernel(c.noise,noise_level_bounds=(.01,1))) if c.optimize else Matern(length_scale=c.setting,nu=2.5)+WhiteKernel(c.noise)
        model=GaussianProcessRegressor(kernel=kernel,optimizer='fmin_l_bfgs_b' if c.optimize else None,n_restarts_optimizer=0,normalize_y=True,random_state=SEED)
    else:raise ValueError(c.family)
    return Pipeline([("select",CompactSelector(10 if c.family=="gpr" else 20)),("scale",StandardScaler()),("model",model)])


class RegionalCorrection(RegressorMixin,BaseEstimator):
    """Referencia y corrección compartida, aprendidas exclusivamente en fit."""
    def __init__(self,candidate):self.candidate=candidate
    def _states(self,X):
        cols=[c for c in X if c.startswith('region__')]
        if not cols:raise ValueError('Faltan indicadores oficiales de estado')
        a=X[cols].to_numpy();known=a.sum(axis=1)>0
        return np.where(known,np.asarray(cols)[a.argmax(axis=1)],'__unseen__')
    def fit(self,X,y):
        y=np.asarray(y);states=self._states(X)
        self.global_mean_=float(y.mean())
        self.state_means_=pd.Series(y).groupby(states).mean().to_dict()
        self.feature_columns_=[c for c in X if not c.startswith('region__')]
        self.training_n_=len(y)
        base=np.array([self.state_means_.get(s,self.global_mean_) for s in states])
        self.correction_=direct_pipeline(replace(self.candidate,kind='direct'))
        self.correction_.fit(X[self.feature_columns_],y-base)
        self.columns_=self.correction_.named_steps['select'].columns_
        return self
    def decompose(self,X):
        states=self._states(X);seen=np.array([s in self.state_means_ for s in states])
        base=np.array([self.state_means_.get(s,self.global_mean_) for s in states])
        raw=self.correction_.predict(X[self.feature_columns_])
        correction=np.where(seen,self.candidate.alpha*raw,0.)
        return base,correction,~seen
    def predict(self,X):
        base,correction,_=self.decompose(X);return base+correction


def make_pipeline(c):
    if c.support!='none' or c.centered:
        from .variants import variant_pipeline
        return variant_pipeline(c)
    return RegionalCorrection(c) if c.kind=='regional_correction' else direct_pipeline(c)


def component_pipeline(model):
    if hasattr(model,'inner_'):return component_pipeline(model.inner_)
    return model.correction_ if isinstance(model,RegionalCorrection) else model


def component_columns(model):return component_pipeline(model).named_steps['select'].columns_


def candidate_grid(keys):
    from .variants import experiment_grid
    custom=experiment_grid(keys)
    if custom is not None:return custom
    keys=[k for k in ['monthly_20_10','whittaker_20_10'] if k in keys]
    if len(keys)!=2:raise ValueError('La política requiere las dos representaciones congeladas')
    direct=[Candidate(key,f,v) for key in keys for f,values in {'gpr':[1,5],'catboost':[2,3]}.items() for v in values]
    return direct+[replace(c,kind='regional_correction',alpha=a) for c in direct for a in [.5,1.]]+[Candidate(keys[0],f,0) for f in ['global_mean','regional_mean']]


def table_for(c,tables,external,location):
    t=tables[c.features].copy()
    if c.family in ["regional_mean","global_mean"]:
        return t.iloc[:,:0].join(location.filter(regex="^region__"),validate="one_to_one")
    for source in c.sources:t=t.join(external[source],validate="one_to_one")
    if c.mask!='all':
        from .variants import mask_table
        t=mask_table(t,c.mask)
    if c.geo:t=t.join(location[["location_x","location_y"]],validate="one_to_one")
    if c.kind=='regional_correction' or c.support!='none' or c.centered:t=t.join(location.filter(regex='^region__'),validate='one_to_one')
    return t


def cv_candidate(c,indices,y,groups,tables,external,location):
    X=table_for(c,tables,external,location).iloc[indices]
    target=np.asarray(y)[indices];g=np.asarray(groups)[indices]
    # Match outer evaluation: hold out one geographic block, never merge distant blocks.
    splitter=GroupKFold(n_splits=len(np.unique(g)))
    pred=np.zeros(len(indices));fold=np.empty(len(indices),int);fits=[]
    for k,(tr,va) in enumerate(splitter.split(X,target,g)):
        model=make_pipeline(c);model.fit(X.iloc[tr],target[tr]);pred[va]=model.predict(X.iloc[va]);fold[va]=k
        fits.append(component_statistics(model))
    return {"candidate":c,"prediction":pred,"fold":fold,"rmse":metric(target,pred)["rmse"],"fits":fits}


def component_statistics(model):
    if hasattr(model,'inner_'):
        result=component_statistics(model.inner_)
        result.update(support=model.candidate.support,state_counts=model.state_counts_,state_means=model.state_means_,global_mean=model.global_mean_)
        return result
    pipe=component_pipeline(model);selector=pipe.named_steps['select'];scale=pipe.named_steps['scale']
    result={'columns':list(selector.columns_),'medians':selector.medians_.to_dict(),'scale_mean':None if scale.mean_ is None else scale.mean_.tolist(),'scale_std':None if scale.scale_ is None else scale.scale_.tolist()}
    fitted=pipe.named_steps['model']
    result['model_parameters']={k:str(value) if hasattr(value,'get_params') else value for k,value in fitted.get_params().items()}
    if hasattr(fitted,'kernel_'):result['kernel_effective']=str(fitted.kernel_);result['kernel_parameters']={k:str(v) if hasattr(v,'get_params') else v for k,v in fitted.kernel_.get_params().items()}
    if hasattr(model,'centers_'):result.update(feature_centers=model.centers_.to_dict(orient='index'),global_feature_center=model.global_center_.to_dict(),raw_medians=model.raw_medians_.to_dict())
    if hasattr(fitted,'intercept_'):result['intercept']=float(fitted.intercept_)
    if hasattr(fitted,'coef_'):result['coefficients']=np.asarray(fitted.coef_).tolist()
    if hasattr(fitted,'_y_train_mean'):result['target_normalization']={'mean':float(fitted._y_train_mean),'std':float(fitted._y_train_std)}
    if isinstance(model,RegionalCorrection):result.update(global_mean=model.global_mean_,state_means=model.state_means_,alpha=model.candidate.alpha,training_n=model.training_n_)
    return result


def passes(candidate,reference,y,states):
    if metric(y,candidate)["rmse"]>metric(y,reference)["rmse"]*.98:return False
    # Caller supplies the inner-fold assignments, independent of y.
    return all(mean_absolute_error(y[states==s],candidate[states==s])<=1.1*mean_absolute_error(y[states==s],reference[states==s])+1e-12 for s in np.unique(states) if (states==s).sum()>=10)


def improve(candidate,reference,target,states,fold):
    good=sum(metric(target[fold==f],candidate[fold==f])["rmse"]<metric(target[fold==f],reference[fold==f])["rmse"] for f in np.unique(fold))
    return good>=2 and passes(candidate,reference,target,states)


def baseline_predictions(train_y,train_states,test_states):
    train_y=np.asarray(train_y);means=pd.DataFrame({"state":train_states,"y":train_y}).groupby("state").y.mean()
    return {"global_mean":np.full(len(test_states),train_y.mean()),"global_median":np.full(len(test_states),np.median(train_y)),"regional_mean":np.array([means.get(s,train_y.mean()) for s in test_states])}


def score_order(s):
    c=s['candidate'];reference=c.family in ['regional_mean','global_mean']
    return (round(s['rmse']/1e-12),not reference,len(c.sources),c.kind!='direct',c.features,c.family,c.setting,c.alpha,c.sources)


def pick_score(scores):
    minimum=min(s['rmse'] for s in scores)
    tied=[s for s in scores if s['rmse']<=minimum+1e-12]
    return min(tied,key=lambda s:score_order(s)[1:])


def admission(p,ref,target,states,fold):
    rmse=metric(target,p)['rmse'];reference=metric(target,ref)['rmse']
    good=sum(metric(target[fold==f],p[fold==f])['rmse']<metric(target[fold==f],ref[fold==f])['rmse'] for f in np.unique(fold))
    regions={s:{'n':int((states==s).sum()),'candidate_mae':float(mean_absolute_error(target[states==s],p[states==s])),'reference_mae':float(mean_absolute_error(target[states==s],ref[states==s]))} for s in np.unique(states)}
    checks={'rmse_2pct':bool(np.isfinite(reference) and reference>0 and rmse<=.98*reference+1e-12),'two_folds':bool(good>=2),'regional_protection':all(v['n']<10 or v['candidate_mae']<=1.1*v['reference_mae']+1e-12 for v in regions.values())}
    return {'admitted':all(checks.values()),'checks':checks,'candidate_rmse':rmse,'reference_rmse':reference,'better_folds':int(good),'by_state':regions,'by_fold':{str(f):{'candidate':metric(target[fold==f],p[fold==f]),'reference':metric(target[fold==f],ref[fold==f])} for f in np.unique(fold)}}


def select(indices,y,groups,states,tables,external,location,allow_external=True,geo=False,base_scores=None):
    target=np.asarray(y)[indices];state=np.asarray(states)[indices]
    scores=list(base_scores) if base_scores is not None else [cv_candidate(replace(c,geo=geo),indices,y,groups,tables,external,location) for c in candidate_grid(tables)]
    references=[s for s in scores if s['candidate'].family in ['regional_mean','global_mean']]
    if not references:references=[cv_candidate(Candidate(next(iter(tables)),f,0),indices,y,groups,tables,external,location) for f in ['global_mean','regional_mean']]
    reference=pick_score(references);regional=next(s for s in references if s['candidate'].family=='regional_mean');fold=reference['fold']
    families=list(dict.fromkeys(s['candidate'].family for s in scores if s['candidate'].family not in ['regional_mean','global_mean']))
    representatives={f:pick_score([s for s in scores if s['candidate'].family==f]) for f in families}
    decisions=[]
    eligible=[]
    for s in representatives.values():
        result=admission(s['prediction'],reference['prediction'],target,state,fold)
        decisions.append({'candidate':asdict(s['candidate']),'against':'best_reference',**result})
        if result['admitted']:eligible.append(s)
    best=pick_score(eligible) if eligible else reference
    if allow_external:
        # Every source variant starts from the identical source-free family winner.
        combinations=[('nasa',),('siap',),('nasa','siap')]
        for f,official in list(representatives.items()):
            admitted=[]
            for sources in combinations:
                if not all(s in external for s in sources):continue
                c=replace(official['candidate'],sources=sources)
                s=cv_candidate(c,indices,y,groups,tables,external,location)
                paired=admission(s['prediction'],official['prediction'],target,state,fold)
                gate=admission(s['prediction'],reference['prediction'],target,state,fold)
                accept=paired['admitted'] and gate['admitted']
                decisions.append({'source':'+'.join(sources),'family':f,'candidate':asdict(c),'admitted':bool(accept),'reference_rmse':official['rmse'],'candidate_rmse':s['rmse'],'paired_without_sources':paired,'against_reference':gate})
                scores.append(s)
                if accept:admitted.append(s)
            if admitted:representatives[f]=pick_score(admitted)
        replacements=[s for s in representatives.values() if admission(s['prediction'],best['prediction'],target,state,fold)['admitted'] and admission(s['prediction'],reference['prediction'],target,state,fold)['admitted']]
        if replacements:best=pick_score(replacements)
    components=[best];weights=np.array([1.]);inner=best['prediction'];strategy='individual'
    combos=[['gpr','catboost'],['regional_mean','gpr'],['regional_mean','catboost'],['regional_mean','gpr','catboost']]
    options=[]
    pool={**representatives,'regional_mean':regional}
    for names in combos:
        if not all(f in pool for f in names):continue
        parts=[pool[f] for f in names];p=np.column_stack([s['prediction'] for s in parts]).mean(axis=1)
        against_current=admission(p,inner,target,state,fold);against_ref=admission(p,reference['prediction'],target,state,fold)
        accept=against_current['admitted'] and against_ref['admitted']
        decisions.append({'ensemble':'+'.join(names),'components':[asdict(s['candidate']) for s in parts],'weights':[1/len(parts)]*len(parts),'admitted':bool(accept),'against_current':against_current,'against_reference':against_ref})
        if accept:options.append((metric(target,p)['rmse'],len(parts),sum(len(s['candidate'].sources) for s in parts),names,parts,p))
    if options:
        minimum=min(o[0] for o in options)
        _,_,_,names,components,inner=min([o for o in options if o[0]<=minimum+1e-12],key=lambda o:(o[1],o[2],o[3]))
        weights=np.full(len(components),1/len(components));strategy='+'.join(names)
    serialized=[]
    for s in scores:
        serialized.append({'candidate':asdict(s['candidate']),'rmse':s['rmse'],'fold':s['fold'].tolist(),'prediction':s['prediction'].tolist(),'fits':s.get('fits',[])})
    return {'candidates':[s['candidate'] for s in components],'weights':weights,'decisions':decisions,'strategy':strategy,'inner_rmse':metric(target,inner)['rmse'],'scores':serialized,'training_indices':np.asarray(indices).tolist(),'_raw_scores':[s for s in scores if not s['candidate'].sources]}


def fit_selection(selection,indices,y,tables,external,location):
    models=[]
    for c in selection["candidates"]:
        model=make_pipeline(c);X=table_for(c,tables,external,location);model.fit(X.iloc[indices],np.asarray(y)[indices]);models.append(model)
    return Blend(models,selection["weights"])


def predict_selection(model,selection,indices,tables,external,location):
    # Both components use identical source/geo contracts but may choose temporal variants.
    return sum(w*m.predict(table_for(c,tables,external,location).iloc[indices]) for w,m,c in zip(model.weights,model.models,selection["candidates"]))


def calibrate(indices,y,groups,states,tables,external,location):
    options=[g for g in np.unique(groups[indices]) if (groups[indices]==g).sum()>=25]
    if not options:return None
    group=min(options,key=lambda g:int((groups[indices]==g).sum()))
    cal=indices[groups[indices]==group];fit=indices[groups[indices]!=group]
    if len(fit)<45 or len(np.unique(groups[fit]))<2:return None
    selection=select(fit,y,groups,states,tables,external,location)
    model=fit_selection(selection,fit,y,tables,external,location)
    residual=np.abs(np.asarray(y)[cal]-predict_selection(model,selection,cal,tables,external,location))
    level=min(1,np.ceil((len(cal)+1)*.9)/len(cal));radius=float(np.quantile(residual,level,method="higher"))
    return {"model":model,"selection":selection,"radius":radius,"calibration_n":len(cal),"calibration_ids":cal.tolist()}


def _serial_selection(s):
    return {"candidates":[asdict(c) for c in s["candidates"]],"weights":s["weights"].tolist(),"decisions":s["decisions"],"strategy":s["strategy"],"inner_rmse":s["inner_rmse"],"scores":s["scores"]}


def load_tables(master):
    configs=json.loads((PROCESSED/"feature-configs.json").read_text(encoding="utf-8"))
    tables={k:pd.read_parquet(ROOT/p).reindex(master[ID]) for k,p in configs.items()}
    prep=json.loads((PROCESSED/"preparation.json").read_text(encoding="utf-8"))
    external={s:pd.read_parquet(PROCESSED/f"external_{s}.parquet").reindex(master[ID]) for s,status in prep["external_status"].items() if status=="candidato"}
    pts=master.to_crs(32614).geometry.representative_point()
    location=pd.DataFrame({"location_x":pts.x.to_numpy(),"location_y":pts.y.to_numpy()},index=master[ID])
    regions=pd.get_dummies(master.Estado,prefix="region",prefix_sep="__",dtype=float)
    regions.index=location.index
    location=location.join(regions)
    return tables,external,location


def train(official_only=False):
    from .robust import run
    return run(official_only=official_only)
