"""Entrega verificable derivada de ejecuciones cerradas; no activa modelos."""
from pathlib import Path
import os,sys,subprocess,json,shutil,uuid
import numpy as np,pandas as pd
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from agrocebada.tracking import Registry,read,check_manifest,atomic_json,LIMITATION
from agrocebada import robust as r
from agrocebada.common import ID,TARGET,sha256

registry=Registry(root);registry.publish();catalog=read(root/'registry/catalog.json')
supersedes=None
if (root/'registry/phase-closure.json').exists():
    supersedes=read(root/'registry/phase-closure.json')['report_hash']
    assert sha256(root/'docs/phase-results.md')==supersedes
    previous=root/'registry/report-revisions'/supersedes;previous.mkdir(parents=True,exist_ok=False)
    shutil.copy2(root/'docs/phase-results.md',previous/'phase-results.md');shutil.copy2(root/'registry/phase-closure.json',previous/'phase-closure.json')
assert sha256(root/'registry/catalog.json')==read(root/'registry/catalog-receipt.json')['sha256']
for entry in catalog['experiments']:
    state=read(root/'runs'/entry['run_id']/'run.json')
    assert state['status'] in ['completed','failed','skipped']
    assert check_manifest(root/'runs'/entry['run_id']/'artifacts',read(root/'runs'/entry['run_id']/'artifact-manifest.json'))
retry=read(root/'registry/optional-retry-catalog.json')
assert sha256(root/'registry/optional-retry-catalog.json')==read(root/'registry/optional-retry-receipt.json')['sha256']
assert check_manifest(root/'optional/adapter-v3',read(root/'optional/adapter-v3/manifest.json'))
for folder in (root/'runs').iterdir():
    state=read(folder/'run.json')
    assert state['status'] in ['completed','failed','skipped']
    if state.get('origin')!='historical':assert check_manifest(folder/'artifacts',read(folder/'artifact-manifest.json'))
assert read(root/'registry/test-results.json')['passed']
subprocess.run([sys.executable,str(root/'scripts/verify_sources.py')],check=True)
active=Path(read(root/'workspace.json')['active_root']);r.active_intact()
env=dict(os.environ,PYTHONPATH=str(active/'src'),PYTHONDONTWRITEBYTECODE='1');env.pop('AGROCEBADA_ARTIFACTS',None)
subprocess.run([sys.executable,'-c',"from agrocebada.inference import Predictor,official_export; from agrocebada.common import ARTIFACTS,ID,TARGET; import pandas as pd,numpy as np;\nfor route,file in [('selected','predictions_59.csv'),('official','predictions_official_only_59.csv')]:\n a=official_export(Predictor(route)); b=pd.read_csv(ARTIFACTS/file); assert a[ID].equals(b[ID]) and np.allclose(a[TARGET],b[TARGET],atol=1e-10,rtol=0)\nprint('Activa: 59 predicciones verificadas por ruta')"],cwd=active,env=env,check=True)
assert r.active_intact()
e08_id=next(entry['run_id'] for entry in catalog['experiments'] if entry['experiment']=='E08')
e08=root/'runs'/e08_id;decisions=read(e08/'run.json')['decision']['by_route'];eligible=[route for route,z in decisions.items() if z['eligible']]
if eligible and not (root/'packages'/('candidate-'+e08_id)).exists():subprocess.run([sys.executable,str(root/'scripts/recover_package.py'),e08_id,'--candidate'],check=True)
for package in ['E00-v2',e08_id,'recovery-E07-v3-monthly_20_10','recovery-E07-v3-whittaker_20_10']:
    assert check_manifest(root/'packages'/package,read(root/'packages'/package/'manifest.json'))
summary=pd.read_csv(root/'registry/summary.csv');new=summary[summary.status.eq('completed')&summary.scheme.eq('principal-5')&~summary.experiment.str.startswith('H')]
lines=['# Resultados de la fase de soporte regional','',LIMITATION,'','La versión activa conserva sus hashes y las 59 predicciones por ruta. La elegibilidad de E08 se calcula por separado; ninguna ruta se activa en esta fase.','', '| ejecución | ruta | RMSE principal | MAE | diferencia con control |','| --- | --- | --- | --- | --- |']
for _,z in new.iterrows():lines.append(f'| [{z.run_id}](../runs/{z.run_id}/run.json) | {z.route} | {z.rmse:.6f} | {z.mae:.6f} | {z.control_delta_rmse:+.6f} |')
lines+=['','## Comparación entre esquemas','','![RMSE en los tres esquemas](figures/experiment-rmse.png)','','| ejecución | ruta | principal | balanceado | rotado |','| --- | --- | --- | --- | --- |']
for (rid,route),part in summary[summary.status.eq('completed')&summary.scheme.isin(r.SCHEMES)&~summary.experiment.str.startswith('H')].groupby(['run_id','route']):
    values=part.set_index('scheme').rmse
    assert all(s in values for s in r.SCHEMES)
    lines.append(f'| {rid} | {route} | '+' | '.join(f'{values[s]:.6f}' for s in r.SCHEMES)+' |')
tests=read(root/'registry/test-results.json')
lines+=['',f'Pruebas: **{tests["counts"]["passed"]} pasan**; artefactos de entrenamiento intactos. [Registro de pruebas](../registry/test-results.json).','']
lines+=['','## Decisión E08','']
if not eligible:lines+=['**Ninguna ruta E08 es elegible.** La mejora global pasa los umbrales, pero falla la protección de Puebla en el rotado: MAE 0.424265 frente a 0.377922 regional, superior al máximo 0.415714. [Paquete de recuperación experimental, sin candidatura ni activación](../packages/'+e08_id+'/manifest.json).','']
for route,z in decisions.items():lines.extend([f'**{route}: elegible={z["eligible"]}; activated=false.**',''])
condition_names={'three_valid_schemes':'Tres esquemas válidos','principal_gain_2pct':'Principal mejora al menos 2% frente a media regional','at_least_two_gains':'Al menos dos esquemas mejoran 2%','mean_ratio_098':'Promedio de razones de error ≤0.98','none_above_105':'Ningún esquema empeora más de 5%','regional_protection':'MAE de cada estado ≤110% de su referencia regional','verification':'Verificación completa de métricas e inferencia'}
for route in decisions:
    lines+=[f'Condiciones de la ruta {route}:','','| condición | cumple |','| --- | --- |']+[f'| {condition_names.get(key,key)} | {"Sí" if value else "No"} |' for key,value in decisions[route]['checks'].items()]+['']
primary=read(e08/'artifacts/validation.json')
lines+=['## Intervalos E08','','Nominal 90%; mínimo de calibración 25. Cobertura empírica sobre esta campaña, sin garantía temporal ni estatal.','', '| ruta | cobertura principal | predicciones evaluadas | disponible |','| --- | --- | --- | --- |']
for route in decisions:
    z=primary['interval_by_route'][route]
    lines.append(f'| {route} | {z["coverage"]:.6f} | {z["valid_n"]} | {z.get("available")} |')
lines+=['','[Cobertura por estado, soporte y folds](../runs/'+e08_id+'/artifacts/validation-principal-5.json). [Pruebas de exclusión estatal y separación entre polígonos](../runs/'+e08_id+'/artifacts/stress.json).','']
lines+=['Los intervalos permanecen desactivados en ambas rutas: cobertura principal 84.78%, inferior al mínimo 85%. En Hidalgo la cobertura es 58.33%; en Puebla 91.55% y en Tlaxcala 100%. No se ajustaron los umbrales después de observar estos resultados.','']
lines+=['## Lectura de los experimentos','', 'Cada prueba conserva el efecto sobre los tres esquemas y su diferencia por parcela. E04b se contrasta con E04a. El esquema intraestado es diagnóstico y reutiliza las mismas etiquetas. Los resultados de E01–E07 no deciden los factores de E08.','', 'La revisión 1 quedó cerrada tras detectar bloques diagnósticos desiguales (68/35/35; train mínimo70) por sus tamaños geométricos. La revisión 2 usa cortes iguales por estado (47/46/45 globales), mantiene los tres esquemas H01 y conserva el intento E00 y sus resultados parciales. [Incidencia y hashes](../registry/partition-revision.json).','', 'Los detalles por estado, soporte, selección interna, parámetros efectivos, fuentes y composición final se encuentran en el `result.md`, `changes.json` y artefactos de cada ejecución. El registro conserva también fallos y omisiones.','', '## Prioridades de datos','', '1. Obtener etiquetas verificadas de otra campaña para una evaluación temporal independiente; su disponibilidad sigue pendiente.', '2. Obtener registros de manejo por parcela: siembra y cosecha, variedad, fertilización, riego y eventos documentados, con origen y fecha; su disponibilidad sigue pendiente.', '3. Una vez disponibles, versionar esos datos y registrar una fase nueva antes de entrenar. No ampliar esta grilla para forzar una mejora.','', '## Archivos y reproducción','', '- [Historial completo](experiment-history.md).', '- [Índice CSV](../registry/summary.csv).', '- [Catálogo congelado](../registry/catalog.json).', '- [Condiciones y checkpoint TabPFN](../optional/tabpfn-2.5/manifest.json); comparación opcional independiente, sin activación.', '- `scripts/recover_package.py <run-id>` ensambla código, dependencias, tablas, modelos y contratos verificados en un destino nuevo y reproduce las 59 consultas por ruta.', '- [Scientific Agent Skills](https://arxiv.org/abs/2609.00065): procedimientos de scikit-learn y GeoPandas utilizados para implementar y verificar esta fase.','']
lines+=['## Efectos observados','','- E01a reduce el error principal y el sesgo de Tlaxcala; E01b empeora los tres esquemas. La regla dura no es una solución regional universal: también falla la protección de Puebla en el rotado.', '- E02 mantiene prácticamente el control. E03 mejora principalmente el rotado. E04a recupera integrales con soporte temporal y mantiene ausentes los picos globales sin respaldo, con cambios pequeños en RMSE. E04b no añade una mejora global reproducida entre esquemas.', '- E05 mejora principal y rotado pero empeora balanceado. E06 mejora balanceado, con pequeños retrocesos en principal y rotado. Sus ganadores internos no se trasladan a E08.', '- Las dos configuraciones TabPFN se presentan por separado, sin selección externa; sus resultados no alteran E08.', '- E08 mejora el RMSE principal frente al control E00 y la media regional, pero perjudica Puebla según el criterio congelado. El diagnóstico intraestado E08 da 0.652265 frente a 0.647705 E00; reutiliza etiquetas y no valida otra campaña.', '- Las 59 salidas finales de E08 oficial/enriquecido coinciden con E01a, aunque cambian el procedimiento y sus contratos. Una mejora OOF o un cambio de procedimiento no implica necesariamente cambiar las consultas finales.', '', '[Diagnósticos de umbrales por experimento](../registry/diagnostic-criteria.json); descriptivos para E01–E06, elegibilidad únicamente para E08.','']
lines+=['## Incidencia de exportación TabPFN','','El entrenamiento del primer intento E07 terminó, pero su CSV float32 redondeó hasta 2.2082519546273716e-7; la reconstrucción produjo exactamente los mismos valores float32. El reintento E07-v3 conserva pesos, tablas, particiones y parámetros, y exporta los valores como float64 con 17 dígitos. Cada configuración se entrenó de nuevo y sus 59 consultas se verificaron en un proceso nuevo con tolerancia absoluta 1e-10. El intento fallido permanece cerrado y no se presenta como resultado verificado.','', '[Catálogo del reintento congelado antes de entrenar](../registry/optional-retry-catalog.json). [Código, datos y pesos del adaptador recuperable](../optional/adapter-v3/manifest.json).','']
(root/'docs/phase-results.md').write_text('\n'.join(lines),encoding='utf-8')
atomic_json(root/'registry/phase-closure.json',{'all_mandatory_closed':True,'all_runs_closed':True,'active_hashes_unchanged':True,'active_predictions_reproduced':{'selected':59,'official':59},'eligible_routes':eligible,'activated':False,'tests':read(root/'registry/test-results.json'),'report_hash':sha256(root/'docs/phase-results.md'),'supersedes_report_hash':supersedes,'catalog_hash':sha256(root/'registry/catalog.json'),'optional_retry_catalog_hash':sha256(root/'registry/optional-retry-catalog.json'),'source_integrity':read(root/'registry/source-integrity.json'),'recovery_packages':['E00-v2',e08_id,'recovery-E07-v3-monthly_20_10','recovery-E07-v3-whittaker_20_10']})
print({'eligible_routes':eligible,'activated':False,'new_results':new[['run_id','route','rmse']].to_dict(orient='records')},flush=True)
