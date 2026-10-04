"""Produce tablas y documentación directamente de las predicciones externas."""
import json
import pandas as pd
import numpy as np
from agrocebada.common import ROOT,ARTIFACTS,PROCESSED,TARGET,write_json
from agrocebada.modeling import metric

report=json.loads((ARTIFACTS/"validation.json").read_text(encoding="utf-8"))
oof=pd.read_csv(ARTIFACTS/"oof.csv")
def markdown(d):
    headers=list(d.columns)
    lines=["| "+" | ".join(headers)+" |","| "+" | ".join(["---"]*len(headers))+" |"]
    for row in d.itertuples(index=False,name=None):lines.append("| "+" | ".join(f"{v:.4f}" if isinstance(v,(float,np.floating)) else str(v) for v in row)+" |")
    return "\n".join(lines)

comparisons=pd.DataFrame(report["metrics"]).T.reset_index(names="procedimiento")
regional=[];intervals=[]
for state,d in oof.groupby("Estado"):
    for procedure in report["metrics"]:regional.append({"estado":state,"procedimiento":procedure,"n":len(d),**metric(d[TARGET],d[procedure])})
    valid=d.interval_low.notna()&d.interval_high.notna()
    intervals.append({"estado":state,"n":len(d),"valid":int(valid.sum()),"coverage":float(((d[TARGET]>=d.interval_low)&(d[TARGET]<=d.interval_high))[valid].mean()),"mean_width":float((d.interval_high-d.interval_low)[valid].mean())})
pd.DataFrame(regional).to_csv(ARTIFACTS/"regional-comparison.csv",index=False)
write_json(ARTIFACTS/"interval-quality.json",{"global":report["interval"],"by_state":intervals})
folds=pd.DataFrame([{"fold":r["fold"],"train":r["train"],"validación":r["validation"],"RMSE":r["metrics"]["rmse"],"estrategia":r["selection"]["strategy"],"fuentes":",".join(sorted(set(s for c in r["selection"]["candidates"] for s in c["sources"]))),"calibración":r["calibration_n"]} for r in report["folds"]])
decisions=[]
for r in report["folds"]:
    for d in r["selection"]["decisions"]:
        if "source" in d:decisions.append({"fold":r["fold"],**d})
pd.DataFrame(decisions).to_csv(ARTIFACTS/"source-decisions.csv",index=False)
final=report["final_selection"]
selected=pd.read_csv(ARTIFACTS/"selected-features.csv")
stability=selected.groupby("feature").fold.nunique().sort_values(ascending=False).rename("folds").reset_index()
stability.to_csv(ARTIFACTS/"feature-stability.csv",index=False)
text=f'''# Validación del modelo

Resultado de ejecución local con semilla 2026 y corte fijo 2025-10-31. Se evalúa un procedimiento de selección anidado; no se elige un ganador mirando el error externo y después se atribuye ese mismo error a una selección independiente. El test oculto de 59 parcelas no tiene etiquetas locales.

## Evaluación principal

Cinco grupos geográficos se construyeron con geometrías únicamente, en UTM 14N, por cortes balanceados sobre el eje de mayor extensión. Tamaños 34, 34, 35, 17 y 18; cada validación tiene al menos 15 etiquetas y cada entrenamiento al menos 80. `folds.csv` y `spatial-folds.html` permiten inspeccionar cobertura y vecindad. Apan/Tepeapulco no forman un fold de dos etiquetas.

Inner usa GroupKFold retirando un grupo espacial por partición, con tantos folds como grupos disponibles en outer-train. Se reproduce así la separación externa sin combinar bloques que puedan retirar un estado completo. Imputación por mediana, disponibilidad ≥50%, eliminación de constantes, ranking por correlación con y y exclusión de redundancia absoluta >0.95 se ajustan dentro de cada entrenamiento. Después se estandariza. Hasta veinte variables por modelo, diez en GPR. Cambiar deliberadamente etiquetas outer-test no modifica la configuración ni el modelo ajustados, como verifica la prueba de contaminación.

La búsqueda contiene 81 configuraciones: nueve representaciones temporales por ElasticNet (alpha 0.05/0.2, l1_ratio 0.25), Bayesian Ridge, SVR-RBF (C 1/10, epsilon 0.1), CatBoost (profundidad 2/3, 220 iteraciones, tasa 0.03, L2=10) y GPR (Matérn 2.5, longitud 1/5, ruido 0.15, sin optimización de kernel). La media global y regional participan además como modelos elegibles en las mismas particiones internas. Los indicadores de estado proceden de la geometría oficial; sus medias se ajustan solo con train. No se usa outer-test para early stopping. Las alternativas temporales se calculan por parcela sin y; su elección por rendimiento pertenece al ajuste interno.

{markdown(comparisons)}

Cada familia tiene su propia configuración elegida internamente y predicciones externas guardadas. `official` evalúa selección y ensamble con solo datos del reto; `selected` añade candidatos que superen el criterio interno. `with_location` es sensibilidad con coordenadas, no reemplazo post hoc del procedimiento principal. Referencias de media/mediana global y media regional se calculan solo con train; un estado no visto utiliza la media global.

{markdown(folds)}

## Fuentes y ensambles

Antes de esta ejecución se guardó `selection-policy.json`: reemplazar la mejor media interna por un modelo, añadir NASA, DGSIAP o ensamble exige reducción relativa de RMSE ≥2%, mejora en al menos dos folds internos y deterioro de MAE regional ≤10% cuando esa región tiene ≥10 ejemplos. Las fuentes se ensayan sobre el ganador interno de cada familia, secuencialmente; las referencias no incorporan fuentes externas. Decisiones completas están en `source-decisions.csv` y `validation.json`. Ningún peso se optimiza sobre OOF externa. Esta revisión se motivó por los resultados anteriores de las mismas 138 etiquetas; la nueva OOF mide el procedimiento revisado pero no constituye un test independiente de esa decisión de desarrollo.

Se evalúa un promedio uniforme de los ganadores de cada familia y la mejor referencia, un promedio de dos componentes y pesos convexos para esos dos componentes mediante SLSQP sobre OOF internas. Se exige no negatividad y suma uno. Cada reemplazo debe superar el criterio frente a la opción vigente y la referencia. Si no lo logra, se conserva el procedimiento anterior. El ajuste final aplica ese mismo procedimiento a las 138 etiquetas: estrategia **{final['strategy']}**, pesos **{final['weights']}**, candidatos **{[(c['family'],c['features'],c['sources']) for c in final['candidates']]}**. El RMSE interno final {final['inner_rmse']:.4f} no sustituye la evaluación externa.

## Errores regionales y superficie

{markdown(pd.DataFrame([{'estado':s,**v} for s,v in report['by_state'].items()]))}

{markdown(pd.DataFrame([{'tercil':s,**v} for s,v in report['by_area'].items()]))}

`regional-comparison.csv` incluye errores por estado de todos los procedimientos. Las etiquetas de Tlaxcala toman solo tres valores: esta estructura y el fuerte contraste regional deben acompañar la lectura del desempeño. No se redondean predicciones ni se adjudica importancia causal a proxies regionales. `feature-stability.csv` describe frecuencia de selección en outer-train, sin escoger retrospectivamente un subconjunto usando outer-test.

## Transferencia y separación adicional

Leave-one-state-out retira por completo cada estado y repite selección oficial dentro de los otros. Es un escenario de transferencia más exigente, distinto del reto que incluye los tres estados.

{markdown(pd.DataFrame(report['regional_stress']))}

Buffer de 1 km entre puntos representativos es sensibilidad, no una distancia obligatoria tomada de la literatura. Solo se evalúa si quedan ≥80 etiquetas de entrenamiento; los casos inviables se conservan como tales. No implica distancia de borde exacta ni validación temporal.

{markdown(pd.DataFrame(report['buffer_sensitivity']).fillna('—'))}

## Intervalos y recursos

Calibración por un grupo interno separado, al menos 25 etiquetas, selección repetida sin sus etiquetas, cuantíl superior de residuos absolutos con corrección de tamaño y nominal 90%. Cobertura externa global **{report['interval']['coverage']:.2%}**, amplitud media **{report['interval']['mean_width']:.4f} t/ha**, presentación admitida **{report['interval']['available']}**. La cobertura mínima predefinida es 85%; no se cambia el nominal al observar fallos. Centro del modelo calibrado separado, dependencia espacial y falta de campañas nuevas limitan garantías. El detalle por estado está en `interval-quality.json`.

Tiempo medido del entrenamiento completo: **{report['seconds']/60:.2f} minutos**. Máximo RSS observado al cierre de folds: **{report['peak_observed_rss_mb']:.1f} MB**, no pico instantáneo certificado. CPU limitada a dos hilos por biblioteca/estimador; no se usó GPU ni cómputo remoto. Estas mediciones corresponden a la computadora y versiones registradas, y no incluyen la preparación previa de datos.

## Reproducir

`python -m agrocebada.cli prepare`, `python scripts/check_preparation.py`, `python -m agrocebada.cli train`, `python -m agrocebada.cli verify`. Dependencias exactas en `requirements.lock`. La verificación recalcula métricas desde `oof.csv` y reproduce las 59 predicciones con el modelo guardado. Pruebas separadas comprueban fuga, compatibilidad, física de fuentes y comportamiento del dashboard sin red.
'''
(ROOT/"docs/model-validation.md").write_text(text,encoding="utf-8")
print(comparisons.to_string(index=False),flush=True)
