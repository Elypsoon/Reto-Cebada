"""Documentación experimental desde archivos de resultados; sin cifras fijas."""
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from agrocebada.common import ROOT,ARTIFACTS,PROCESSED,ID,TARGET,write_json,WORKSPACE
from agrocebada import modeling as m
from agrocebada.robust import SCHEMES,promotion,active_intact

def read(name):return json.loads((ARTIFACTS/name).read_text(encoding='utf-8'))
def markdown(frame):
    rows=['| '+' | '.join(frame.columns)+' |','| '+' | '.join(['---']*len(frame.columns))+' |']
    for row in frame.itertuples(index=False,name=None):rows.append('| '+' | '.join(f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v) for v in row)+' |')
    return '\n'.join(rows)

reports={name:read(f'validation-{name}.json') for name in SCHEMES};validation=read('validation.json');decision=read('promotion.json');comparison=read('phase-comparison.json')
official_reports={}
for name,r in reports.items():
    official_reports[name]={**r,'metrics':{**r['metrics'],'selected':r['metrics']['official']},'by_state':{s:{**v,'selected':v['official']} for s,v in r['by_state'].items()}}
official_decision=promotion(official_reports,decision['checks']['verification']);write_json(ARTIFACTS/'promotion-official.json',official_decision)
summary=pd.DataFrame([{'esquema':name,'RMSE selección':r['metrics']['selected']['rmse'],'RMSE oficial':r['metrics']['official']['rmse'],'RMSE regional':r['metrics']['regional_mean']['rmse'],'razón selección/regional':decision['ratios'][name]} for name,r in reports.items()])
summary.to_csv(ARTIFACTS/'phase-summary.csv',index=False)
regional=pd.DataFrame([{'esquema':name,'estado':s,'n':v['n'],'MAE selección':v['selected']['mae'],'MAE regional':v['regional_mean']['mae'],'razón MAE':v['selected']['mae']/v['regional_mean']['mae'],'RMSE selección':v['selected']['rmse']} for name,r in reports.items() for s,v in r['by_state'].items()]);regional.to_csv(ARTIFACTS/'regional-comparison.csv',index=False)
intervals=pd.DataFrame([{'esquema':name,'estado':s,**v} for name,r in reports.items() for s,v in {'global':r['interval'],**r['interval']['by_state']}.items()]).drop(columns=['by_state','nominal'],errors='ignore');intervals.to_csv(ARTIFACTS/'interval-comparison.csv',index=False)
selected=pd.read_csv(ARTIFACTS/'selected-features.csv');selected.groupby('feature').fold.nunique().rename('folds').sort_values(ascending=False).to_csv(ARTIFACTS/'feature-stability.csv')
fold_decisions=[{'fold':f['fold'],**d} for f in reports[SCHEMES[0]]['folds'] for d in f['selection']['decisions'] if 'source' in d];pd.DataFrame(fold_decisions).to_csv(ARTIFACTS/'source-decisions.csv',index=False)
future=[{'priority':1,'data':'Rendimientos parcelarios de una nueva campaña, medidos y con unidades/área verificadas','purpose':'Confirmar generalización temporal en etiquetas no utilizadas para desarrollar la política','availability':'pendiente de obtención y verificación'},
    {'priority':2,'data':'Fechas de siembra/cosecha, variedad, riego, fertilización y manejo por parcela','purpose':'Explicar variación parcelaria y alinear ventanas fenológicas','availability':'pendiente de obtención y verificación'},
    {'priority':3,'data':'Protocolo de medición, humedad/calidad de cosecha y fuente del rendimiento','purpose':'Resolver cuantización y discrepancias con evidencia primaria','availability':'pendiente de obtención y verificación'},
    {'priority':4,'data':'Más etiquetas verificadas de Hidalgo y municipios con pocos casos','purpose':'Evaluar cobertura y errores regionales con mayor soporte','availability':'pendiente de obtención y verificación'}]
write_json(ARTIFACTS/'future-data-priorities.json',future)
primary=validation['metrics'];final=validation['final_selection'];sources=sorted({s for c in final['candidates'] for s in c['sources']});source_text=', '.join(sources) if sources else 'ninguna'
old=comparison['previous_primary']['rmse'];current=primary['selected']['rmse'];gain=(old-current)/old
checks=pd.DataFrame([{'condición':k,'cumple':v} for k,v in decision['checks'].items()])
stress=read('stress.json');review=read('hidalgo-original-review.json');historic=read('diagnostic-historic.json');diagnostic=read('diagnostic-principal-5.json')
hid_old=next(v for v in historic['Estado'] if v['Estado']=='Hidalgo');hid_new=next(v for v in diagnostic['Estado'] if v['Estado']=='Hidalgo')
verdict='Se cumplen los criterios numéricos y de verificación' if decision['promote'] else 'Promoción rechazada: se conserva la versión vigente íntegra'
text=f'''# Fase de selección robusta con corrección regional

{verdict}. Ejecución {WORKSPACE['run_id']}; semilla 2026; corte 2025-10-31. El nuevo RMSE principal es {current:.6f} t/ha frente a {old:.6f} previo y {primary['regional_mean']['rmse']:.6f} de la media regional. Cambio frente a la selección previa: {gain:.2%} de reducción. La comparación histórica usa los mismos identificadores, etiquetas y folds; las otras particiones tienen sus propias referencias.

## Protocolo y límites

Política y particiones congeladas antes de entrenar. Hash de política: {comparison['policy_hash']}. Hay 26 candidatos oficiales: ocho directos, dieciséis correcciones regionales con intensidad 0.5/1 y dos medias. Solo GPR y CatBoost, representaciones monthly_20_10 y whittaker_20_10. Cuatro promedios uniformes; no se optimizan pesos continuos. Seis ablaciones externas sobre los dos ganadores oficiales: NASA, DGSIAP y ambas. Cada opción se compara con su pareja sin fuentes y con la referencia. La admisión interna requiere reducción RMSE ≥2%, mejora en dos folds y deterioro MAE regional ≤10% para n≥10.

Las tres evaluaciones reutilizan las mismas 138 etiquetas. No son 414 observaciones independientes, un test nuevo, validación temporal ni evaluación oficial. La grilla no se amplió después de observar resultados. Los diagnósticos de GPR y CatBoost no sustituyen retrospectivamente la selección.

## Comparación por esquema

{markdown(summary)}

## Decisión de promoción

{markdown(checks)}

Razón media de RMSE: {decision['mean_ratio']:.6f}. La ruta oficial también fue contrastada: promoción {'admitida' if official_decision['promote'] else 'rechazada'}. Requisitos: principal ≤0.98, dos de tres razones ≤0.98, media ≤0.98, ninguna >1.05, protección regional y verificaciones completas. Los motivos individuales permanecen en promotion.json y promotion-official.json.

## Resultados por estado

{markdown(regional)}

Las métricas por tercil de área y por fold, predicciones pareadas, frecuencias de selección/admisión y variables elegidas se conservan por esquema. El dataset evaluado mantiene 197 identificadores, 138 etiquetas y 59 casos ocultos; hash de datos {comparison['data_hash']}.

## Diagnóstico y originales

Hidalgo aportaba {hid_old['squared_error_share']:.1%} del error cuadrático previo y aporta {hid_new['squared_error_share']:.1%} del nuevo esquema principal. Se revisaron {len(review)} casos de mayor error contra CSV y geometría originales. No se demostraron discrepancias de rendimiento, superficie, estado o municipio; no se corrigieron ni retiraron etiquetas por residuo elevado. Se verificaron {read('originals-check.json')['verified_files']} hashes de originales. Las uniones parcelarias, calidad utilizable por sensor, faltantes y cobertura de rásteres están en diagnostic-*. Municipios con n<10 se marcan como muestra pequeña: su error es descriptivo.

## Intervalos y sensibilidad

{markdown(intervals)}

Nominal 90%, mínimo de calibración 25. Intervalos de la ruta enriquecida {'disponibles' if validation['interval']['available'] else 'desactivados'} según cobertura principal ≥85% y modelo final compatible. El centro procede de un ajuste separado; las etiquetas de calibración no entran en selección. La cobertura global no garantiza cobertura regional: Hidalgo principal alcanza {reports[SCHEMES[0]]['interval']['by_state']['Hidalgo']['coverage']:.1%}.

Leave-one-state-out y buffer de 1 km evaluaron la ruta oficial congelada. El buffer usa distancia entre polígonos en UTM, excluyendo físicamente vecinos a menos de 1 km. Escenarios evaluados: {sum(s['status']=='evaluado' for s in stress)}; inviables: {sum(s['status']!='evaluado' for s in stress)}, con razón, conjuntos y tamaños registrados en stress.json. No se retiraron escenarios para mejorar la decisión principal.

## Modelos finales y reproducción

El ajuste experimental final usa {', '.join(c['family']+' '+c['kind'] for c in final['candidates'])}; pesos {final['weights']}; fuentes del rendimiento: {source_text}. Cada componente conserva medias, escala, columnas, intensidad, fuentes y hashes. Referencia más corrección ponderada reproduce la predicción; GPR muestra sensibilidades individuales no aditivas. Se mantienen modelos oficial/enriquecido separados y 59 predicciones por ruta sin cotas artificiales. Producción = rendimiento por superficie.

## Siguiente evidencia necesaria

'''+'\n'.join(f"{v['priority']}. {v['data']}. {v['purpose']}. Disponibilidad: {v['availability']}." for v in future)+'''

No se ha desplegado ni enviado la versión experimental al organizador. La restauración usa el paquete completo de la versión anterior, no la modificación de hashes de contratos incompatibles.
'''
(ROOT/'docs/model-validation.md').write_text(text,encoding='utf-8');(ROOT/'docs/phase-results.md').write_text(text,encoding='utf-8')

template=(ROOT/'docs/technical-report.template.md').read_text(encoding='utf-8')
template=template.replace('Se construyeron cinco grupos geográficos sin utilizar rendimientos y se mantuvo cada grupo fuera del entrenamiento cuando se estimaron sus resultados.','Se congelaron tres esquemas geográficos sin utilizar magnitudes de rendimiento, conservando cada grupo fuera del entrenamiento cuando se estimaron sus resultados.')
methods=template.split('## Metodología\n',1)[1].split('\n## Resultados y discusión',1)[0]
methods=methods.split('Cinco grupos geográficos',1)[0]
methods+='''La nueva fase congeló tres esquemas por identificador: principal de cinco bloques vigentes, cuatro cortes medianos y cinco bloques tras rotación de 45 grados. Todos conservaron quince casos mínimos de validación y ochenta de entrenamiento. Los mismos 138 rendimientos participaron en cada esquema; no se consideraron 414 muestras independientes. La referencia se recalculó sobre la misma versión de datos en cada partición.

Se registraron 26 candidatos: ocho configuraciones directas de GPR y CatBoost, dieciséis correcciones regionales con intensidad 0.5 o 1, y medias global y regional. Dos tablas con nube máxima 20% compararon medianas mensuales y reconstrucción Whittaker. Cada corrección aprendió medias por estado, residuos, imputación, selección y escala exclusivamente dentro del entrenamiento. Un estado ausente recibió la media global sin corrección.

La evaluación interna retiró un bloque de entrenamiento por vez. Reemplazar la referencia exigió mejorar RMSE 2%, mejorar dos folds y proteger MAE regional con deterioro máximo 10%. Se probaron NASA, DGSIAP y ambas sobre cada ganador oficial, con comparación pareada independiente del orden. Cuatro promedios uniformes completaron la búsqueda; no se ajustaron pesos continuos ni se amplió la grilla tras observar resultados.

Se diagnosticaron residuos, faltantes, soporte satelital y cobertura por estado y municipio. Diez casos difíciles de Hidalgo se contrastaron con originales; no se demostraron discrepancias y se conservaron todas las etiquetas. Las sensibilidades excluyeron estados completos o polígonos a menos de un kilómetro. Intervalos nominales 90% separaron al menos 25 etiquetas de calibración de la selección. La promoción exigió mejora estable en esquemas y protección regional, además de contratos, exportación y pruebas. Modelos, código e informes experimentales permanecieron separados de la versión vigente.
'''
results=f'''La fase conservó las 197 parcelas, 138 etiquetas y 59 casos ocultos, sin modificar los originales ni las fórmulas satelitales. Hidalgo tuvo 36 etiquetas, Puebla 71 y Tlaxcala 31. La cuantización de Tlaxcala, con tres valores de rendimiento, limita la interpretación física de pequeños errores. Los municipios con menos de diez casos se señalaron como muestras pequeñas.

El procedimiento enriquecido obtuvo RMSE {current:.3f} t/ha, MAE {primary['selected']['mae']:.3f} t/ha y R² {primary['selected']['r2']:.3f} en el esquema principal. La versión previa obtuvo RMSE {old:.3f}; la referencia regional alcanzó {primary['regional_mean']['rmse']:.3f}. La reducción frente a la selección previa fue {gain:.2%}, pero no superó la referencia. La variante oficial registró RMSE {primary['official']['rmse']:.3f} t/ha.

'''
for name,report in reports.items():
    results+=f"En {name}, el RMSE seleccionado fue {report['metrics']['selected']['rmse']:.3f} t/ha y el regional {report['metrics']['regional_mean']['rmse']:.3f}; razón {decision['ratios'][name]:.3f}. "
results+=f'''

{verdict}. Los umbrales requerían al menos 2% de ganancia principal y en dos esquemas, razón media máxima 0.98 y ninguna superior a 1.05, sin empeorar MAE regional más de 10%. También se verificó la ruta oficial; su decisión quedó registrada por separado. Estas comparaciones reutilizan etiquetas del desarrollo y no representan confirmación temporal ni puntuación oficial.

Hidalgo concentró {hid_old['squared_error_share']:.1%} del error previo y {hid_new['squared_error_share']:.1%} del nuevo principal. La revisión de diez residuos elevados confirmó concordancia con CSV y geometría oficiales; no aporta evidencia para retirar etiquetas. Calidad por sensor, faltantes por variable y cobertura de rásteres acompañan el diagnóstico. Las fuentes externas se admitieron exclusivamente dentro del entrenamiento y no sustituyeron etiquetas parcelarias.

El ajuste final experimental utilizó {', '.join(c['family']+' '+c['kind'] for c in final['candidates'])}, con fuentes {source_text}. Se serializaron ambas rutas y se generaron 59 estimaciones por ruta, reproducidas en un proceso nuevo. El contrato conserva código, dependencias, columnas, fuentes, intensidades y estadísticas aprendidas. Referencia más corrección ponderada reproduce el cálculo; los efectos individuales de GPR permanecen como sensibilidades no aditivas. La aplicación calcula producción multiplicando rendimiento por superficie y opera sin red.

Los intervalos nominales 90% alcanzaron cobertura principal {validation['interval']['coverage']:.1%} y amplitud media {validation['interval']['mean_width']:.3f} t/ha. Su presentación quedó {'admitida' if validation['interval']['available'] else 'desactivada'}. Hidalgo alcanzó {reports[SCHEMES[0]]['interval']['by_state']['Hidalgo']['coverage']:.1%}; la cobertura global no garantiza cobertura de cada región. Las etiquetas de calibración permanecieron fuera de selección. Se publicaron los tres esquemas y estados sin ajustar radios con etiquetas externas.

La sensibilidad dejó estados completos fuera de entrenamiento y excluyó vecinos mediante distancia entre polígonos para el buffer de 1 km. Cada escenario inviable conserva su razón y tamaño. La fase terminó en {comparison['seconds']/60:.2f} minutos de cómputo local. No se modificó la política para buscar un resultado favorable; siguen pendientes nuevas campañas y datos de manejo verificables.
'''
conclusions=f'''Se implementó y evaluó una selección acotada con corrección regional, fuentes pareadas y tres particiones espaciales congeladas. El RMSE principal fue {current:.3f} t/ha frente a {old:.3f} previo y {primary['regional_mean']['rmse']:.3f} de la media regional. {verdict}. La mejora respecto de una versión anterior no basta para acreditar utilidad frente a una referencia sencilla.

Se conservaron todas las etiquetas y originales; ningún residuo elevado justificó retirar casos. Modelos, contratos, predicciones y documentación experimentales forman una versión separada y recuperable. Las verificaciones incluyen contaminación de etiquetas y covariables, serialización, composición de explicaciones, producción por superficie y aplicación sin conexión. La descarga contiene exactamente 59 identificadores ocultos por ruta, sin cotas artificiales.

La incertidumbre sigue siendo desigual por región y las tres evaluaciones reutilizan las mismas 138 etiquetas. No hay test independiente, evaluación oficial, validación temporal ni despliegue nuevo. La siguiente fase debería obtener rendimientos de otra campaña y fechas, variedad, riego y fertilización verificables. Esos insumos permanecen pendientes; su disponibilidad debe comprobarse antes de ampliar la complejidad del modelo.
'''
template=re.sub(r'(?s)(## Metodología\n).*?(?=\n## Resultados y discusión)',lambda match:match[1]+'\n'+methods.strip()+'\n',template)
template=re.sub(r'(?s)(## Resultados y discusión\n).*?(?=\n## Uso de la ciencia)',lambda match:match[1]+'\n'+results.strip()+'\n',template)
template=re.sub(r'(?s)(## Conclusiones\n).*?(?=\n## Bibliografía)',lambda match:match[1]+'\n'+conclusions.strip()+'\n',template)
template='# AgroCebada: selección robusta y corrección regional (experimental)\n'+template.split('\n',1)[1]
team=read('technical-report-check.json')['team_contributions']
template=template.replace('__TEAM_CONTRIBUTIONS__','\n\n'.join('**'+v['name']+'**: '+v['contributions'] for v in team['members']))
counts={k:len(re.findall(r'\S+',v)) for k,v in re.findall(r'^## ([^\n]+)\n(.*?)(?=^## |\Z)',template,re.M|re.S)}
limits={'Introducción':(400,550),'Justificación':(100,200),'Objetivos':(1,200),'Metodología':(600,700),'Resultados y discusión':(1,800),'Uso de la ciencia de datos en la inclusión financiera del sector agro':(1,300),'Conclusiones':(1,400)}
for name,(minimum,maximum) in limits.items():assert minimum<=counts[name]<=maximum,(name,counts[name])
assert not re.search(r'__[A-Z_]+__',template)
bibliography=(ROOT/'docs/ai-tools-and-bibliography.md').read_text(encoding='utf-8')
template=template.replace('Véase `ai-tools-and-bibliography.md` para fuentes primarias, documentación de versiones, atribución de skills y registro de herramientas/prompts de IA. Incorporar esas referencias al formato final de entrega.',bibliography.replace('# Fuentes y registro de asistencia de IA\n','',1))
(ROOT/'docs/technical-report.md').write_text(template,encoding='utf-8')
write_json(ARTIFACTS/'technical-report-check.json',{'words':counts,'body_limits_met':True,'results_from_validation':True,'team_contributions':team,'experimental':True})
active_intact();print(summary.to_string(index=False));print(counts)
