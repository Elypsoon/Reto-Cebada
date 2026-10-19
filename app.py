"""AgroCebada: consulta retrospectiva local de parcelas verificadas."""
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from agrocebada.common import PROCESSED,ARTIFACTS,ID,TARGET,CUTOFF,sha256
from agrocebada.inference import Predictor,official_export,validate_contract
from agrocebada.features import reconstruct,SENSORS

st.set_page_config(page_title="AgroCebada · Rendimiento por parcela",page_icon=":material/grass:",layout="wide")
st.title("AgroCebada")
st.caption("Rendimiento por parcela · Hidalgo, Tlaxcala y Puebla · campaña 2025")

def fresh(p):
    try:
        validate_contract(p.contract,p.master,p.tables,p.external,p.location)
        return sha256(p.contract_path)==p.contract_file_hash and sha256(ARTIFACTS/f"model_{p.name}.joblib")==p.contract["model_hash"]
    except (OSError,ValueError):return False

@st.cache_resource(max_entries=2,validate=fresh,show_spinner="Comprobando datos y modelo…")
def load_predictor(name):return Predictor(name)

@st.cache_data(max_entries=4,show_spinner=False)
def read_data(filename,stamp):return pd.read_parquet(PROCESSED/filename)

def local_parquet(filename):
    path=PROCESSED/filename
    return read_data(filename,path.stat().st_mtime_ns)

name=st.sidebar.selectbox("Modelo",["selected","official"],format_func=lambda x:"Ensamble Adaptativo R08" if x=="selected" else "Solo datos del reto",key="model")
try:
    predictor=load_predictor(name)
    master=predictor.master
    validation=json.loads((ARTIFACTS/"validation.json").read_text(encoding="utf-8"))
except (OSError,ValueError,KeyError) as error:
    st.error(f"No se pudo cargar esta versión: {error}")
    st.info("Revise la guía local y restaure los datos y modelos de la misma versión antes de continuar.")
    st.stop()

st.sidebar.caption(f"Corte: {CUTOFF} · versión {predictor.contract['model_hash'][:10]}")
st.sidebar.info("Estimación retrospectiva al cierre de octubre. La evaluación disponible usa parcelas de 2025; todavía no valida campañas futuras.")
view=st.segmented_control("Vista",["Consultar parcelas","Validación","Fuentes"],default="Consultar parcelas",key="view")
download=official_export(predictor)
st.sidebar.download_button("Descargar las 59 predicciones",download.to_csv(index=False).encode("utf-8"),file_name=f"agrocebada_{name}_59.csv",mime="text/csv",key="official_download",on_click="ignore",icon=":material/download:")

if view=="Validación":
    st.subheader("Evaluación del modelo y validación cruzada")
    model_key="selected" if name=="selected" else "official"
    metrics=validation["metrics"][model_key]
    with st.container(horizontal=True):
        st.metric("RMSE",f"{metrics['rmse']:.3f} t/ha",border=True)
        st.metric("Error absoluto medio",f"{metrics['mae']:.3f} t/ha",border=True)
        st.metric("R²",f"{metrics['r2']:.3f}",border=True)
    st.caption("138 predicciones fuera de pliegue (OOF). Validación estratificada 70/30 (PyR Pregunta 5).")
    oof=pd.read_csv(ARTIFACTS/"oof.csv")
    from agrocebada.modeling import metric
    regional=pd.DataFrame([{ "Estado":s,"Parcelas":len(d),**metric(d[TARGET],d[model_key])} for s,d in oof.groupby("Estado")])
    st.dataframe(regional.rename(columns={"rmse":"RMSE (t/ha)","mae":"MAE (t/ha)","r2":"R²"}),hide_index=True,alt="Errores de validación por estado")
    compare=pd.DataFrame(validation["metrics"]).T.reset_index().rename(columns={"index":"Procedimiento","rmse":"RMSE (t/ha)","mae":"MAE (t/ha)","r2":"R²"})
    st.dataframe(compare,hide_index=True,alt="Comparación de modelos y referencias con las mismas parcelas de evaluación")
    interval=validation["interval"]
    st.caption(f"Intervalos: cobertura empírica {interval['coverage']:.1%}, nominal 90%. " + ("Admitidos con calibración adaptativa por estado." if interval["available"] else "No admitidos; no se muestran en fichas."))
    st.caption("La cuantización de etiquetas de Tlaxcala y las diferencias entre estados limitan la interpretación de los errores. Leave-one-state-out y buffer se describen en el informe local.")
    st.stop()

if view=="Fuentes":
    st.subheader("Procedencia y alcance")
    sources=predictor.contract["prediction_sources"]
    st.markdown("**Fuentes utilizadas en el cálculo:** datos del reto"+(" + "+", ".join(s.upper() for s in sources) if sources else ""))
    st.markdown("Sentinel-2 y Planet aportan índices ópticos; Landsat aporta VI6T. CHIRPS/CHIRTS son mensuales, y la topografía tiene resolución de 120 m.")
    st.markdown("NASA POWER se evalúa como contexto regional diario en tiempo solar local. DGSIAP se evalúa como historia municipal de cebada grano 2018–2024. Su admisión depende de las comparaciones internas guardadas; no reemplazan las etiquetas de parcela.")
    st.markdown("No se calculan alertas locales de heladas ni evapotranspiración incompleta. SoilGrids y fuentes que no pudieron verificarse quedan excluidas.")
    st.dataframe(pd.DataFrame([{"Fuente":d["source"].upper(),"Admitida en ajuste final":d["admitted"],"RMSE interno previo":d["reference_rmse"],"RMSE interno con fuente":d["candidate_rmse"]} for d in predictor.contract["selection"]["decisions"] if "source" in d]),hide_index=True,alt="Decisiones de admisión de fuentes externas")
    st.caption("La consulta y el cálculo usan archivos locales y no necesitan APIs ni mapas en línea.")
    st.stop()

with st.sidebar:
    st.subheader("Buscar parcela")
    state=st.selectbox("Estado",["Todos"]+sorted(master.Estado.unique()),key="state")
    filtered=master if state=="Todos" else master[master.Estado.eq(state)]
    municipality=st.selectbox("Municipio",["Todos"]+sorted(filtered.Municipio.unique()),key="municipality")
    if municipality!="Todos":filtered=filtered[filtered.Municipio.eq(municipality)]
    subset=st.selectbox("Conjunto",["Todos","ENTRENAMIENTO","PREDICCION"],format_func=lambda s:{"Todos":"Todos","ENTRENAMIENTO":"Con rendimiento observado","PREDICCION":"Por predecir"}[s],key="subset")
    if subset!="Todos":filtered=filtered[filtered.CONJUNTO.eq(subset)]
    search=st.text_input("Identificador",key="search",placeholder="Escribe parte del identificador")
    if search:filtered=filtered[filtered[ID].astype(str).str.contains(search,case=False,regex=False)]

if filtered.empty:
    st.info("No hay parcelas con estos filtros. Amplía la búsqueda.")
    st.stop()
st.subheader(f"{len(filtered)} parcelas en la consulta")
choices=filtered[ID].tolist()
pending=st.session_state.pop("pending_parcel",None)
if pending in choices:st.session_state["parcel"]=pending
if st.session_state.get("parcel") not in choices:st.session_state["parcel"]=choices[0]
pid=st.selectbox("Parcela",choices,key="parcel")
row=master.loc[master[ID].eq(pid)].iloc[0]
left,right=st.columns([1.3,1])
with left:
    fig=go.Figure()
    colors={"ENTRENAMIENTO":"#477353","PREDICCION":"#c49330"}
    for conjunto,color in colors.items():
        xs=[];ys=[]
        for geom in filtered.loc[filtered.CONJUNTO.eq(conjunto)].geometry.to_crs(4326):
            for polygon in getattr(geom,"geoms",[geom]):
                x,y=polygon.exterior.xy;xs.extend(list(x)+[None]);ys.extend(list(y)+[None])
        fig.add_trace(go.Scatter(x=xs,y=ys,mode="lines",line={"color":color,"width":1},name="Observado" if conjunto=="ENTRENAMIENTO" else "Por predecir",hoverinfo="skip"))
    pts=filtered.to_crs(4326).geometry.representative_point()
    fig.add_trace(go.Scatter(x=pts.x,y=pts.y,mode="markers",marker={"size":8,"color":[colors[x] for x in filtered.CONJUNTO]},text=filtered[ID],customdata=filtered[ID],hovertemplate="Parcela %{text}<extra></extra>",name="Parcelas"))
    selected=row.geometry.representative_point()
    fig.add_trace(go.Scatter(x=[selected.x],y=[selected.y],mode="markers",marker={"size":16,"symbol":"circle-open","color":"#1b3431","line":{"width":3}},name="Seleccionada",hoverinfo="skip"))
    fig.update_layout(height=430,margin={"l":0,"r":0,"t":60,"b":40},xaxis_title="Longitud",yaxis_title="Latitud",legend={"orientation":"h","x":0,"y":1.04,"yanchor":"bottom","font":{"size":10}})
    fig.update_yaxes(scaleanchor="x",scaleratio=1/np.cos(np.deg2rad(19.75)))
    event=st.plotly_chart(fig,key="parcel_map",on_select="rerun",selection_mode="points",alt="Ubicación de las parcelas filtradas y parcela seleccionada")
    selected_points=event.selection.points
    if selected_points:
        picked=selected_points[-1].get("customdata")
        if picked in choices and picked!=pid:
            st.session_state["map_choice"]=picked
    if st.session_state.get("map_choice"):
        # A callback-free second rerun avoids changing an already instantiated widget.
        if st.button("Abrir parcela elegida en el mapa",key="open_map_choice"):
            st.session_state["pending_parcel"]=st.session_state.pop("map_choice")
            st.rerun()
    st.caption("Mapa de polígonos sin conexión. Selecciona un punto o utiliza la búsqueda.")
with right:
    with st.container(border=True):
        st.subheader(f"Parcela {pid}")
        st.caption(f"{row.Municipio}, {row.Estado}")
        st.metric("Superficie",f"{row.AREA_HA:.2f} ha")
        if pd.notna(row[TARGET]):st.metric("Rendimiento observado",f"{row[TARGET]:.2f} t/ha")
        else:st.badge("Rendimiento observado oculto",color="orange")
        if st.button("Calcular rendimiento estimado",type="primary",icon=":material/calculate:",key="calculate"):
            st.session_state["result"]={"parcel":pid,"model":name,"row":predictor.predict([pid]).iloc[0].to_dict()}
        result=st.session_state.get("result")
        if result and result["parcel"]==pid and result["model"]==name:
            estimate=result["row"]
            with st.container(horizontal=True):
                st.metric("Rendimiento estimado",f"{estimate[TARGET]:.3f} t/ha")
                st.metric("Producción estimada",f"{estimate['PRODUCCION_T']:.2f} t")
            if "INTERVAL_LOW" in estimate:
                st.caption(f"Intervalo calibrado: {estimate['INTERVAL_LOW']:.2f}–{estimate['INTERVAL_HIGH']:.2f} t/ha. Puede tener un centro distinto del estimador principal; la cobertura no está garantizada por parcela.")
            st.caption(f"Cálculo con modelo guardado · corte {CUTOFF} · versión {predictor.contract['model_hash'][:10]}")
            summary=f"Parcela: {pid}\nMunicipio: {row.Municipio}\nEstado: {row.Estado}\nÁrea: {row.AREA_HA} ha\nRendimiento estimado: {estimate[TARGET]} t/ha\nProducción estimada: {estimate['PRODUCCION_T']} t\nCorte: {CUTOFF}\nVersión: {predictor.contract['model_hash']}\nEstimación retrospectiva; no garantía agronómica ni crediticia."
            st.download_button("Descargar ficha",summary.encode("utf-8"),file_name=f"ficha_{pid}.txt",mime="text/plain",on_click="ignore",key="summary_download")
st.subheader("Evolución y calidad de observaciones")
sensor=st.selectbox("Sensor",list(SENSORS),key="sensor")
cloud=st.select_slider("Máxima nubosidad",options=[10,20,40],value=20,key="cloud")
sat=local_parquet("satellite.parquet")
observed=sat[sat[ID].eq(pid)&sat.sensor.eq(sensor)&sat.date.between("2025-04-01",CUTOFF)].sort_values("date")
col=SENSORS[sensor][1][0]+"_promedio"
usable=observed[observed.porcentaje_nubosidad.le(cloud)].dropna(subset=[col])
curve,status=reconstruct(usable,col,10)
fig=go.Figure()
fig.add_trace(go.Scatter(x=observed.date,y=observed[col],mode="markers",name="Observaciones originales",marker={"color":"#aab3ac","size":6}))
fig.add_trace(go.Scatter(x=usable.date,y=usable[col],mode="markers",name="Observaciones utilizables",marker={"color":"#3f744f","size":8}))
if len(curve):fig.add_trace(go.Scatter(x=curve.date,y=curve.value,mode="lines",name="Reconstrucción semanal",line={"color":"#ba851c","dash":"dash"},connectgaps=False))
fig.update_layout(height=330,xaxis_title="Fecha de captura",yaxis_title="VI6T (índice)" if sensor=="Landsat" else "NDVI (índice)",margin={"l":0,"r":0,"t":55,"b":40},legend={"orientation":"h","x":0,"y":1.04,"yanchor":"bottom","font":{"size":11}})
fig.update_xaxes(range=["2025-04-01",CUTOFF])
st.plotly_chart(fig,alt="Observaciones originales y utilizables, con reconstrucción semanal cuando existe soporte")
st.caption(f"{len(usable)} observaciones utilizables de {len(observed)} · reconstrucción {status}. El pico de vegetación es aproximado; no identifica una fecha exacta de floración.")
if status!="válida":st.warning("Cobertura temporal insuficiente para interpretar fases. Se conservan las observaciones disponibles.")
if (PROCESSED/"parcel-raster-coverage.parquet").exists():
    support=local_parquet("parcel-raster-coverage.parquet")
    low=support[support[ID].eq(pid)&support.coverage.lt(.95)]
    if len(low):
        st.warning("Parte de la topografía tiene datos solo sobre una fracción de esta parcela.")
        st.dataframe(low[["variable","coverage"]].rename(columns={"variable":"Variable","coverage":"Fracción cubierta"}),hide_index=True,alt="Cobertura de los rásteres con datos parciales")
with st.expander("Cómo interpreta el modelo esta parcela"):
    if st.button("Ver explicación",key="explain"):
        effects,info=predictor.explain(pid)
        st.caption(info["interpretation"]+". No es una explicación causal ni una recomendación crediticia.")
        top=effects.iloc[effects.contribution_t_ha.abs().nlargest(8).index].set_index("variable")
        st.bar_chart(top,y="contribution_t_ha",horizontal=True,x_label="Efecto en t/ha",alt="Contribuciones o sensibilidad de las variables más influyentes")
