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
from scipy.optimize import minimize
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


def make_pipeline(c):
    if c.family in ["regional_mean","global_mean"]:
        return Pipeline([("select",RegionalSelector()),("scale",StandardScaler(with_mean=False,with_std=False)),("model",MeanRegressor(c.family=="regional_mean"))])
    if c.family=="elastic":model=ElasticNet(alpha=c.setting,l1_ratio=.25,max_iter=10000)
    elif c.family=="bayesian":model=BayesianRidge()
    elif c.family=="svr":model=SVR(C=c.setting,epsilon=.1,gamma="scale")
    elif c.family=="catboost":model=CatBoostRegressor(depth=int(c.setting),iterations=220,learning_rate=.03,l2_leaf_reg=10,loss_function="RMSE",random_seed=SEED,thread_count=2,verbose=False,allow_writing_files=False)
    elif c.family=="gpr":model=GaussianProcessRegressor(kernel=Matern(length_scale=c.setting,nu=2.5)+WhiteKernel(.15),optimizer=None,normalize_y=True,random_state=SEED)
    else:raise ValueError(c.family)
    return Pipeline([("select",CompactSelector(10 if c.family=="gpr" else 20)),("scale",StandardScaler()),("model",model)])


def candidate_grid(keys):
    settings={"elastic":[.05,.2],"bayesian":[0],"svr":[1,10],"catboost":[2,3],"gpr":[1,5]}
    return [Candidate(key,family,v) for key in keys for family,values in settings.items() for v in values]


def table_for(c,tables,external,location):
    t=tables[c.features].copy()
    if c.family in ["regional_mean","global_mean"]:
        return t.iloc[:,:0].join(location.filter(regex="^region__"),validate="one_to_one")
    for source in c.sources:t=t.join(external[source],validate="one_to_one")
    if c.geo:t=t.join(location[["location_x","location_y"]],validate="one_to_one")
    return t


def cv_candidate(c,indices,y,groups,tables,external,location):
    X=table_for(c,tables,external,location).iloc[indices]
    target=np.asarray(y)[indices];g=np.asarray(groups)[indices]
    # Match outer evaluation: hold out one geographic block, never merge distant blocks.
    splitter=GroupKFold(n_splits=len(np.unique(g)))
    pred=np.zeros(len(indices));fold=np.empty(len(indices),int)
    for k,(tr,va) in enumerate(splitter.split(X,target,g)):
        model=make_pipeline(c);model.fit(X.iloc[tr],target[tr]);pred[va]=model.predict(X.iloc[va]);fold[va]=k
    return {"candidate":c,"prediction":pred,"fold":fold,"rmse":metric(target,pred)["rmse"]}


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


def select(indices,y,groups,states,tables,external,location,allow_external=True,geo=False,base_scores=None):
    target=np.asarray(y)[indices];state=np.asarray(states)[indices]
    scores=list(base_scores) if base_scores is not None else [cv_candidate(replace(c,geo=geo),indices,y,groups,tables,external,location) for c in candidate_grid(tables)]
    scores.sort(key=lambda s:s["rmse"])
    # References participate in the same inner splits; outer labels never choose a fallback.
    key=next(iter(tables))
    references=[cv_candidate(Candidate(key,f,0),indices,y,groups,tables,external,location) for f in ["regional_mean","global_mean"]]
    reference=min(references,key=lambda s:s["rmse"])
    representatives=[next(s for s in scores if s["candidate"].family==f) for f in dict.fromkeys(s["candidate"].family for s in scores)]
    eligible=[s for s in representatives if improve(s["prediction"],reference["prediction"],target,state,reference["fold"])]
    best=min(eligible,key=lambda s:s["rmse"]) if eligible else reference
    decisions=[{"baseline":reference["candidate"].family,"reference_rmse":reference["rmse"],"best_model_rmse":scores[0]["rmse"],"eligible_families":[s["candidate"].family for s in eligible]}]
    if allow_external:
        for source in ["nasa","siap"]:
            if source not in external:continue
            options=[cv_candidate(replace(s["candidate"],sources=s["candidate"].sources+(source,)),indices,y,groups,tables,external,location) for s in representatives]
            admitted=[s for s in options if improve(s["prediction"],best["prediction"],target,state,best["fold"]) and improve(s["prediction"],reference["prediction"],target,state,reference["fold"])]
            option=min(admitted or options,key=lambda s:s["rmse"]);accept=bool(admitted)
            decisions.append({"source":source,"admitted":accept,"reference_rmse":best["rmse"],"candidate_rmse":option["rmse"],"tested_families":[s["candidate"].family for s in options]})
            if accept:best=option;representatives=options
    components=[best];weights=np.array([1.]);inner=best["prediction"];strategy="individual"
    # Equal family weights reduce dependence on one winner of the broad feature search.
    diverse=representatives+[reference]
    averaged=np.column_stack([s["prediction"] for s in diverse]).mean(axis=1)
    accept=improve(averaged,inner,target,state,best["fold"]) and improve(averaged,reference["prediction"],target,state,reference["fold"])
    decisions.append({"ensemble":"diverso","admitted":bool(accept),"weights":[1/len(diverse)]*len(diverse),"reference_rmse":metric(target,inner)["rmse"],"candidate_rmse":metric(target,averaged)["rmse"]})
    if accept:components=diverse;weights=np.full(len(diverse),1/len(diverse));inner=averaged;strategy="diverso"
    alternatives=[s for s in representatives+[reference] if s["candidate"]!=best["candidate"]]
    if not alternatives:
        return {"candidates":[best["candidate"]],"weights":weights,"decisions":decisions,"strategy":strategy,"inner_rmse":metric(target,inner)["rmse"],"scores":[{"candidate":asdict(s["candidate"]),"rmse":s["rmse"]} for s in scores+references],"_raw_scores":scores}
    alternative=min(alternatives,key=lambda s:s["rmse"])
    pair=np.column_stack([best["prediction"],alternative["prediction"]])
    averaged=pair.mean(axis=1)
    if improve(averaged,inner,target,state,best["fold"]) and improve(averaged,reference["prediction"],target,state,reference["fold"]):
        components=[best,alternative];weights=np.array([.5,.5]);inner=averaged;strategy="promedio"
    optimized=minimize(lambda w:np.mean((target-pair@w)**2),[.5,.5],bounds=[(0,1),(0,1)],constraints={"type":"eq","fun":lambda w:w.sum()-1},method="SLSQP")
    if optimized.success and np.all(optimized.x>=0) and np.isclose(optimized.x.sum(),1):
        p=pair@optimized.x
        decisions.append({"ensemble":"convexo","weights":optimized.x.tolist(),"candidate_rmse":metric(target,p)["rmse"],"fit":"OOF internas de train"})
        if improve(p,inner,target,state,best["fold"]) and improve(p,reference["prediction"],target,state,reference["fold"]):
            strategy="convexo";weights=optimized.x;inner=p;components=[best,alternative]
    return {"candidates":[s["candidate"] for s in components],"weights":weights,"decisions":decisions,"strategy":strategy,"inner_rmse":metric(target,inner)["rmse"],"scores":[{"candidate":asdict(s["candidate"]),"rmse":s["rmse"]} for s in scores+references],"_raw_scores":scores}


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
    warnings.filterwarnings("ignore",category=RuntimeWarning)
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter();master=gpd.read_parquet(PROCESSED/"parcels.parquet")
    tables,external,location=load_tables(master)
    if official_only:external={}
    train_indices=np.flatnonzero(master[TARGET].notna());hidden=np.flatnonzero(master[TARGET].isna())
    target=master[TARGET].to_numpy();states=master.Estado.to_numpy()
    group_train,xy=spatial_groups(master.iloc[train_indices]);groups=np.full(len(master),-1);groups[train_indices]=group_train
    master["spatial_group"]=groups
    master.to_parquet(PROCESSED/"parcels.parquet",index=False)
    write_json(ARTIFACTS/"selection-policy.json",{"seed":SEED,"sources_min_rmse_improvement":.02,"inner_folds":"un grupo espacial por partición; tantos folds como grupos de train","stable_folds":2,"regional_mae_max_degradation":.1,"baseline_gate":"modelo y ensamble: mejora estable >=2% sobre la mejor media interna global/regional","diverse_ensemble":"promedio uniforme de ganadores internos de cada familia y referencia","external_search":"ganador interno de cada familia; admisión secuencial","interval_nominal":.9,"interval_min_coverage":.85,"calibration_min_n":25,"candidate_grid":[asdict(c) for c in candidate_grid(tables)],"group_counts":pd.Series(group_train).value_counts().sort_index().to_dict(),"created_before_results":True})
    master.loc[train_indices,[ID,"Estado","Municipio","spatial_group"]].to_csv(ARTIFACTS/"folds.csv",index=False)
    predictions={name:np.full(len(master),np.nan) for name in ["selected","official","global_mean","global_median","regional_mean","with_location","elastic","bayesian","svr","catboost","gpr"]}
    lo=np.full(len(master),np.nan);hi=lo.copy();records=[];all_scores=[];selected_cols=[];peak_rss=0
    with threadpool_limits(limits=2):
        for group in np.unique(group_train):
            tr=train_indices[groups[train_indices]!=group];va=train_indices[groups[train_indices]==group]
            print(f"Validación espacial {group+1}/{len(np.unique(group_train))}: train={len(tr)} test={len(va)}",flush=True)
            official=select(tr,target,groups,states,tables,external,location,allow_external=False)
            selected=select(tr,target,groups,states,tables,external,location,base_scores=official["_raw_scores"]) if external else official
            geographic=select(tr,target,groups,states,tables,external,location,allow_external=False,geo=True)
            for name,s in [("official",official),("selected",selected),("with_location",geographic)]:
                m=fit_selection(s,tr,target,tables,external,location);predictions[name][va]=predict_selection(m,s,va,tables,external,location)
                if name=="selected":
                    selected_cols.extend({"fold":int(group),"component":j,"feature":c} for j,component in enumerate(m.models) for c in component.named_steps["select"].columns_)
            for name,p in baseline_predictions(target[tr],states[tr],states[va]).items():predictions[name][va]=p
            for family in ["elastic","bayesian","svr","catboost","gpr"]:
                best=next(s["candidate"] for s in official["_raw_scores"] if s["candidate"].family==family)
                single={"candidates":[best],"weights":np.array([1.])}
                m=fit_selection(single,tr,target,tables,external,location);predictions[family][va]=predict_selection(m,single,va,tables,external,location)
            cal=calibrate(tr,target,groups,states,tables,external,location)
            if cal:
                center=predict_selection(cal["model"],cal["selection"],va,tables,external,location);lo[va]=center-cal["radius"];hi[va]=center+cal["radius"]
            records.append({"fold":int(group),"train":len(tr),"validation":len(va),"selection":_serial_selection(selected),"metrics":metric(target[va],predictions["selected"][va]),"calibration_n":cal["calibration_n"] if cal else 0})
            all_scores.extend({"fold":int(group),**s} for s in official["scores"])
            peak_rss=max(peak_rss,psutil.Process().memory_info().rss)
            write_json(ARTIFACTS/"training-progress.json",{"completed_folds":len(records),"total_folds":len(np.unique(group_train)),"elapsed_seconds":time.perf_counter()-started})
        print("Pruebas regionales y buffer",flush=True)
        stress=[];buffer_results=[]
        for state in np.unique(states[train_indices]):
            tr=train_indices[states[train_indices]!=state];va=train_indices[states[train_indices]==state]
            s=select(tr,target,groups,states,tables,external,location,allow_external=False)
            m=fit_selection(s,tr,target,tables,external,location);p=predict_selection(m,s,va,tables,external,location)
            stress.append({"held_out_state":state,"n":len(va),**metric(target[va],p)})
        # Sensitivity at 1 km: geometry-based eligibility, recorded before its results.
        for group in np.unique(group_train):
            tr=train_indices[groups[train_indices]!=group];va=train_indices[groups[train_indices]==group]
            pts=location.iloc[tr][["location_x","location_y"]].to_numpy();test=location.iloc[va][["location_x","location_y"]].to_numpy()
            distance=np.sqrt(((pts[:,None,:]-test[None,:,:])**2).sum(axis=2)).min(axis=1)
            kept=tr[distance>=1000]
            if len(kept)<80:
                buffer_results.append({"fold":int(group),"buffer_m":1000,"status":"no viable: menos de 80 muestras","train_remaining":len(kept)})
            else:
                s=select(kept,target,groups,states,tables,external,location,allow_external=False)
                m=fit_selection(s,kept,target,tables,external,location);p=predict_selection(m,s,va,tables,external,location)
                buffer_results.append({"fold":int(group),"buffer_m":1000,"status":"evaluado","train_remaining":len(kept),**metric(target[va],p)})
        print("Ajuste final con las 138 etiquetas",flush=True)
        official_final=select(train_indices,target,groups,states,tables,external,location,allow_external=False)
        final=select(train_indices,target,groups,states,tables,external,location,base_scores=official_final["_raw_scores"]) if external else official_final
        final_model=fit_selection(final,train_indices,target,tables,external,location)
        official_model=fit_selection(official_final,train_indices,target,tables,external,location)
        final_cal=calibrate(train_indices,target,groups,states,tables,external,location)
    valid_interval=np.isfinite(lo[train_indices])&np.isfinite(hi[train_indices])
    coverage=float(((target[train_indices]>=lo[train_indices])&(target[train_indices]<=hi[train_indices]))[valid_interval].mean()) if valid_interval.any() else None
    interval_ok=bool(valid_interval.all() and coverage>=.85 and final_cal)
    oof=master.loc[train_indices,[ID,"Estado","AREA_HA",TARGET,"spatial_group"]].copy()
    for name,p in predictions.items():oof[name]=p[train_indices]
    oof["interval_low"]=lo[train_indices];oof["interval_high"]=hi[train_indices];oof.to_csv(ARTIFACTS/"oof.csv",index=False)
    report={"metrics":{name:metric(target[train_indices],p[train_indices]) for name,p in predictions.items()},"by_state":{s:metric(target[train_indices][states[train_indices]==s],predictions["selected"][train_indices][states[train_indices]==s]) for s in np.unique(states[train_indices])},"by_area":{},"folds":records,"regional_stress":stress,"buffer_sensitivity":buffer_results,"interval":{"nominal":.9,"coverage":coverage,"available":interval_ok,"mean_width":float(np.nanmean(hi[train_indices]-lo[train_indices])),"calibration_min":25,"limitation":"Dependencia espacial; cobertura empírica, sin garantía por estado o año futuro; centro de modelo separado de calibración"},"seconds":time.perf_counter()-started,"peak_observed_rss_mb":peak_rss/1024**2,"final_selection":_serial_selection(final)}
    bins=pd.qcut(master.iloc[train_indices].AREA_HA,3,labels=["pequeña","mediana","grande"])
    for b in bins.unique():
        ix=np.asarray(bins==b);report["by_area"][str(b)]=metric(target[train_indices][ix],predictions["selected"][train_indices][ix])
    write_json(ARTIFACTS/"validation.json",report);write_json(ARTIFACTS/"candidate-scores.json",all_scores)
    pd.DataFrame(selected_cols).to_csv(ARTIFACTS/"selected-features.csv",index=False)
    dataset_hash=sha256(PROCESSED/"source-manifest.json")
    for name,selection,model in [("selected",final,final_model),("official",official_final,official_model)]:
        interval=final_cal if name=="selected" and interval_ok else None
        required=list(selection["candidates"])+(interval["selection"]["candidates"] if interval else [])
        # A calibration component can use a different source contract or temporal variant.
        table_contract={}
        for c in required:
            key=c.features
            info={"columns":list(table_for(c,tables,external,location).columns),"hash":sha256(PROCESSED/f"features_{key}.parquet"),"sources":list(c.sources),"geo":c.geo,"family":c.family}
            if key in table_contract and table_contract[key]!=info:
                key=key+f"__component_{len(table_contract)}"
                info["base_key"]=c.features
            table_contract[key]=info
        contract={"dataset_hash":dataset_hash,"code_hash":code_hash(),"dependencies":dependencies(),"cutoff":CUTOFF,"seed":SEED,"selection":_serial_selection(selection),"tables":table_contract,"sources":sorted(set(s for c in required for s in c.sources)),"prediction_sources":sorted(set(s for c in selection["candidates"] for s in c.sources))}
        contract["external_hashes"]={s:sha256(PROCESSED/f"external_{s}.parquet") for s in contract["sources"]}
        contract["parcels_hash"]=sha256(PROCESSED/"parcels.parquet")
        bundle={"model":model,"selection":selection,"contract":contract,"interval":interval}
        joblib.dump(bundle,ARTIFACTS/f"model_{name}.joblib")
        contract["model_hash"]=sha256(ARTIFACTS/f"model_{name}.joblib")
        write_json(ARTIFACTS/f"contract_{name}.json",contract)
    p=predict_selection(final_model,final,hidden,tables,external,location)
    if not np.isfinite(p).all() or (p<0).any():raise ValueError("Predicciones no finitas o negativas; exportación bloqueada")
    export=pd.DataFrame({ID:master.iloc[hidden][ID].to_numpy(),TARGET:p}).sort_values(ID)
    if len(export)!=59 or export[ID].duplicated().any():raise ValueError("Exportación debe contener 59 parcelas únicas")
    export.to_csv(ARTIFACTS/"predictions_59.csv",index=False)
    print("Finalizado:",report["metrics"]["selected"],"intervalo disponible:",interval_ok,flush=True)
