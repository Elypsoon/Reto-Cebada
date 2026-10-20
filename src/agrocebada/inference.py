"""Inferencia local compartida por consola y dashboard, sin reentrenamiento."""
import json
import joblib
import numpy as np
import pandas as pd
import geopandas as gpd
from .common import ROOT,PROCESSED,ARTIFACTS,ID,TARGET,CUTOFF,sha256,code_hash,dependencies,write_json
from .modeling import Candidate,load_tables,table_for,predict_selection,metric


def compatible_dependencies(expected, actual):
    """Keep library versions exact; permit CPython security patches within 3.12."""
    if expected.keys() != actual.keys():
        return False
    if expected["python"].split(".")[:2] != actual["python"].split(".")[:2]:
        return False
    return all(actual[name] == value for name, value in expected.items() if name != "python")


def validate_contract(contract,master,tables,external,location,check_files=True):
    if contract["cutoff"]!=CUTOFF or contract["code_hash"]!=code_hash():
        raise ValueError("El modelo corresponde a otra versión del código o fecha de corte. Regenere los artefactos compatibles.")
    if not compatible_dependencies(contract["dependencies"],dependencies()):
        raise ValueError("Las versiones instaladas no coinciden con las del modelo. Use requirements.lock.")
    if len(master)!=197 or master[ID].duplicated().any():raise ValueError("La tabla de parcelas está incompleta o duplicada.")
    for source in contract["sources"]:
        if source not in external:raise ValueError(f"Falta la fuente requerida {source}. No se sustituirá el modelo.")
    for key,info in contract["tables"].items():
        base_key=info.get("base_key",key)
        if base_key not in tables:raise ValueError(f"Falta la configuración de variables {base_key}.")
        c=Candidate(base_key,info.get("family","bayesian"),0,tuple(info.get("sources",contract["sources"])),info.get("geo",False))
        x=table_for(c,tables,external,location)
        if list(x.columns)!=info["columns"]:raise ValueError("Las columnas u orden de variables son incompatibles con el modelo.")
        if not x.index.equals(pd.Index(master[ID])):raise ValueError("Las variables no corresponden al orden de las parcelas.")
    if check_files:
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
            if "state_radii" in cal:
                r_vec=np.array([cal["state_radii"].get(s,cal.get("radius",0.78)) for s in self.master.loc[indices,"Estado"]])
                rows["INTERVAL_LOW"]=np.maximum(0.0,center-r_vec);rows["INTERVAL_HIGH"]=center+r_vec
            else:
                rows["INTERVAL_LOW"]=np.maximum(0.0,center-cal["radius"]);rows["INTERVAL_HIGH"]=center+cal["radius"]
        return rows.set_index(ID).reindex(ids).reset_index()

    def explain(self,pid):
        if getattr(self.bundle["model"],"precomputed",None) is not None:
            return pd.DataFrame(columns=["variable","contribution_t_ha"]), {
                "available":False,"exact_additive":False,"baseline":None,
                "prediction":float(self.predict([pid])[TARGET].iloc[0]),
                "interpretation":"Este ensamble contiene estimaciones precalculadas para las parcelas oficiales. El artefacto no incluye contribuciones por variable que reproduzcan la estimación guardada.",
            }
        i=int(self.master.index[self.master[ID].eq(pid)][0]);contributions=[];baseline=0.;exact=True
        for w,m,c in zip(self.bundle["model"].weights,self.bundle["model"].models,self.bundle["selection"]["candidates"]):
            raw=table_for(c,self.tables,self.external,self.location).iloc[[i]]
            selected=m.named_steps["select"].transform(raw);scaled=m.named_steps["scale"].transform(selected);model=m.named_steps["model"]
            if hasattr(model,"coef_"):
                effects=scaled[0]*model.coef_;base=float(model.intercept_)
            elif c.family=="catboost":
                from catboost import Pool
                shap=model.get_feature_importance(Pool(scaled),type="ShapValues")[0]
                effects=shap[:-1];base=float(shap[-1])
            else:
                exact=False;neutral=raw.copy()
                neutral.loc[:,:]=m.named_steps["select"].medians_.reindex(raw.columns).to_numpy()
                base=float(m.predict(neutral)[0]);effects=[]
                prediction=float(m.predict(raw)[0])
                for column in selected.columns:
                    changed=raw.copy();changed[column]=m.named_steps["select"].medians_[column]
                    effects.append(prediction-float(m.predict(changed)[0]))
            baseline+=float(w)*base
            contributions.extend({"variable":name,"contribution_t_ha":float(w)*float(v)} for name,v in zip(selected.columns,effects))
        frame=pd.DataFrame(contributions).groupby("variable",as_index=False).contribution_t_ha.sum()
        prediction=float(self.predict([pid])[TARGET].iloc[0])
        if exact and not np.isclose(baseline+frame.contribution_t_ha.sum(),prediction,atol=1e-6):raise ValueError("La explicación no reproduce la predicción.")
        return frame,{"exact_additive":exact,"baseline":baseline,"prediction":prediction,"interpretation":"Contribuciones matemáticas; no causalidad" if exact else "Sensibilidad al sustituir una variable por su mediana de train; efectos no aditivos"}


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
