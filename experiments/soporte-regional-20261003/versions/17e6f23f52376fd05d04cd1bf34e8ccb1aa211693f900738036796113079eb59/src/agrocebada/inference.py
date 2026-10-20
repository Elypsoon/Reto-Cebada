"""Inferencia local compartida por consola y dashboard, sin reentrenamiento."""
import json
import joblib
import numpy as np
import pandas as pd
import geopandas as gpd
from .common import ROOT,PROCESSED,ARTIFACTS,ID,TARGET,CUTOFF,sha256,code_hash,dependencies,write_json
from .modeling import Candidate,load_tables,table_for,predict_selection,metric,RegionalCorrection,component_pipeline


def validate_contract(contract,master,tables,external,location,check_files=True):
    if contract["cutoff"]!=CUTOFF or contract["code_hash"]!=code_hash():
        raise ValueError("El modelo corresponde a otra versión del código o fecha de corte. Regenere los artefactos compatibles.")
    if contract["dependencies"]!=dependencies():
        raise ValueError("Las versiones instaladas no coinciden con las del modelo. Use requirements.lock.")
    if len(master)!=197 or master[ID].duplicated().any():raise ValueError("La tabla de parcelas está incompleta o duplicada.")
    for source in contract["sources"]:
        if source not in external:raise ValueError(f"Falta la fuente requerida {source}. No se sustituirá el modelo.")
    for key,info in contract["tables"].items():
        base_key=info.get("base_key",key)
        if base_key not in tables:raise ValueError(f"Falta la configuración de variables {base_key}.")
        if 'candidate' in info:
            spec=dict(info['candidate']);spec['sources']=tuple(spec.get('sources',[]));c=Candidate(**spec)
        else:c=Candidate(base_key,info.get("family","bayesian"),0,tuple(info.get("sources",contract["sources"])),info.get("geo",False),info.get('kind','direct'),info.get('alpha',1.))
        x=table_for(c,tables,external,location)
        if list(x.columns)!=info["columns"]:raise ValueError("Las columnas u orden de variables son incompatibles con el modelo.")
        if not x.index.equals(pd.Index(master[ID])):raise ValueError("Las variables no corresponden al orden de las parcelas.")
    if check_files:
        if 'policy_hash' in contract and sha256(ARTIFACTS/'selection-policy.json')!=contract['policy_hash']:raise ValueError('Política incompatible con el modelo')
        if 'scheme_hash' in contract and sha256(ARTIFACTS/'schemes.csv')!=contract['scheme_hash']:raise ValueError('Particiones incompatibles con el modelo')
        expected={PROCESSED/"source-manifest.json":contract["dataset_hash"],PROCESSED/"parcels.parquet":contract["parcels_hash"]}
        expected.update({PROCESSED/f"features_{v.get('base_key',k)}.parquet":v["hash"] for k,v in contract["tables"].items()})
        expected.update({PROCESSED/f"external_{s}.parquet":h for s,h in contract["external_hashes"].items()})
        if any(not p.exists() or sha256(p)!=h for p,h in expected.items()):raise ValueError("Se modificaron datos requeridos por el modelo. Revise el contrato y regenere la versión completa.")


class Predictor:
    def __init__(self,name="selected"):
        if name not in ["selected","official"]:raise ValueError("Modelo no reconocido")
        self.name=name
        self.master=gpd.read_parquet(PROCESSED/"parcels.parquet")
        self.tables,self.external,self.location=load_tables(self.master)
        self.contract_path=ARTIFACTS/f"contract_{name}.json"
        self.contract_file_hash=sha256(self.contract_path)
        contract=json.loads(self.contract_path.read_text(encoding="utf-8"))
        validate_contract(contract,self.master,self.tables,self.external,self.location)
        model_path=ARTIFACTS/f"model_{name}.joblib"
        if sha256(model_path)!=contract["model_hash"]:raise ValueError("El archivo de modelo no coincide con su contrato.")
        self.bundle=joblib.load(model_path)
        self.contract=contract

    def predict(self,ids):
        ids=list(ids)
        if len(set(ids))!=len(ids) or not set(ids)<=set(self.master[ID]):raise ValueError("Seleccione identificadores únicos del conjunto oficial de parcelas.")
        indices=self.master.index[self.master[ID].isin(ids)].to_numpy()
        p=predict_selection(self.bundle["model"],self.bundle["selection"],indices,self.tables,self.external,self.location)
        if not np.isfinite(p).all() or (p<0).any():raise ValueError("El cálculo produjo valores inválidos. No se exportarán.")
        rows=self.master.loc[indices,[ID,"AREA_HA"]].copy();rows[TARGET]=p;rows["PRODUCCION_T"]=p*rows.AREA_HA
        cal=self.bundle["interval"]
        if cal is not None:
            center=predict_selection(cal["model"],cal["selection"],indices,self.tables,self.external,self.location)
            rows["INTERVAL_LOW"]=center-cal["radius"];rows["INTERVAL_HIGH"]=center+cal["radius"]
        return rows.set_index(ID).reindex(ids).reset_index()

    def explain(self,pid):
        i=int(self.master.index[self.master[ID].eq(pid)][0])
        raw=[table_for(c,self.tables,self.external,self.location).iloc[[i]] for c in self.bundle['selection']['candidates']]
        return explain_components(self.bundle['model'],self.bundle['selection'],raw)


def explain_components(blend,selection,raw_tables):
    if any(c.support!='none' or c.centered for c in selection['candidates']):
        from .variants import explain_variants
        return explain_variants(blend,selection,raw_tables)
    contributions=[];baseline=0.;exact=True;composition=[]
    for w,m,c,raw in zip(blend.weights,blend.models,selection['candidates'],raw_tables):
        pipe=component_pipeline(m);selector=pipe.named_steps['select'];regressor=pipe.named_steps['model']
        multiplier=float(w);reference=0.;correction=float(m.predict(raw)[0]);unseen=False
        features=raw
        if isinstance(m,RegionalCorrection):
            b,r,u=m.decompose(raw);reference=float(b[0]);correction=float(r[0]);unseen=bool(u[0]);features=raw[m.feature_columns_]
            multiplier*=0. if unseen else c.alpha
        elif c.family in ['regional_mean','global_mean']:
            reference=correction;correction=0.
        composition.append({'weight':float(w),'kind':c.kind,'alpha':c.alpha,'reference':reference,'weighted_correction':correction,'prediction':float(m.predict(raw)[0]),'unseen_state':unseen})
        selected=selector.transform(features);scaled=pipe.named_steps['scale'].transform(selected)
        if hasattr(regressor,'coef_'):
            effects=scaled[0]*regressor.coef_;base=float(regressor.intercept_)
        elif c.family=='catboost':
            from catboost import Pool
            shap=regressor.get_feature_importance(Pool(scaled),type='ShapValues')[0];effects=shap[:-1];base=float(shap[-1])
        else:
            exact=False;neutral=features.copy();neutral.loc[:,:]=selector.medians_.reindex(features.columns).to_numpy()
            base=float(pipe.predict(neutral)[0]);prediction=float(pipe.predict(features)[0]);effects=[]
            for column in selected.columns:
                changed=features.copy();changed[column]=selector.medians_[column]
                effects.append(prediction-float(pipe.predict(changed)[0]))
        baseline+=float(w)*reference+multiplier*base if isinstance(m,RegionalCorrection) else float(w)*base
        contributions.extend({'variable':name,'contribution_t_ha':multiplier*float(v)} for name,v in zip(selected.columns,effects))
    frame=pd.DataFrame(contributions,columns=['variable','contribution_t_ha']).groupby('variable',as_index=False).contribution_t_ha.sum()
    prediction=sum(row['weight']*row['prediction'] for row in composition)
    reference=sum(row['weight']*row['reference'] for row in composition)
    correction=sum(row['weight']*row['weighted_correction'] for row in composition)
    if not np.isclose(reference+correction,prediction,atol=1e-10):raise ValueError('Composición incompatible')
    if exact and not np.isclose(baseline+frame.contribution_t_ha.sum(),prediction,atol=1e-6):raise ValueError('La explicación no reproduce la predicción')
    return frame,{'exact_additive':exact,'baseline':baseline,'prediction':prediction,'reference_total':reference,'correction_total':correction,'components':composition,'interpretation':'Contribuciones matemáticas; no causalidad' if exact else 'Sensibilidades no aditivas; composición regional exacta, sin interpretación causal'}


def official_export(predictor):
    ids=sorted(predictor.master.loc[predictor.master.CONJUNTO.eq("PREDICCION"),ID])
    d=predictor.predict(ids)[[ID,TARGET]]
    if len(d)!=59 or set(d[ID])!=set(ids) or d[ID].duplicated().any():raise ValueError("La descarga oficial debe contener las 59 parcelas ocultas.")
    return d


def verify_artifacts():
    selected=Predictor();official=Predictor("official")
    generated=official_export(selected);saved=pd.read_csv(ARTIFACTS/"predictions_59.csv")
    if not generated[ID].equals(saved[ID]) or not np.allclose(generated[TARGET],saved[TARGET],rtol=0,atol=1e-10):raise ValueError("La inferencia no reproduce las 59 predicciones guardadas.")
    official_export(official).to_csv(ARTIFACTS/"predictions_official_only_59.csv",index=False)
    oof=pd.read_csv(ARTIFACTS/"oof.csv");report=json.loads((ARTIFACTS/"validation.json").read_text(encoding="utf-8"))
    for name,expected in report["metrics"].items():
        got=metric(oof[TARGET],oof[name])
        if any(not np.isclose(got[k],expected[k]) for k in got):raise ValueError("Métricas no reproducibles desde OOF")
    result={"predictions":len(generated),"oof":len(oof),"finite":bool(np.isfinite(generated[TARGET]).all()),"same_predictions":True,"metrics_reproduced":True,"selected_sources":selected.contract["prediction_sources"],"model_hash":selected.contract["model_hash"]}
    write_json(ARTIFACTS/"integration-check.json",result)
    return result
