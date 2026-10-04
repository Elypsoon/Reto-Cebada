## Context

La motivación está en `proposal.md`. Se estima rendimiento parcelario retrospectivo abril–octubre de 2025 en t/ha, con corte 2025-10-31 y semilla 2026; se conservan 197 identificadores, 138 etiquetas y 59 consultas ocultas. No existen etiquetas verificadas de otra campaña ni manejo disponible.

La raíz activa contiene el procedimiento previo, mientras `experiments/regional-20261003` conserva la corrección regional, el protocolo de 26 candidatos y las verificaciones de la fase rechazada. Su `candidate_grid` fija dos tablas y sus contratos suponen componentes con selector, escala y modelo; hay que parametrizarlos dentro de una nueva copia, sin instalar el código experimental sobre la activa. `common.py` y los preparadores escriben por defecto a destinos del proyecto, por lo que el aislamiento debe abarcar código y datos derivados, no solo los modelos.

### Antecedentes registrados al diseñar la fase

| Identificador de antecedente | Resultado observado | Estado real y fuente |
| --- | --- | --- |
| H00-vigente | RMSE principal 0.764052925; MAE 0.592684942; referencia regional 0.743975677 | Versión activa; `artifacts/validation.json`, `artifacts/oof.csv` y paquete `artifacts/versions/selection-current-20261003` |
| H01-regional | RMSE principal 0.749457826; MAE 0.596552607; balanceado 0.769435864; rotado 0.749168684 | Ejecución completada, promoción rechazada; `experiments/regional-20261003/artifacts/phase-comparison.json` |
| D01-soporte | Principal y balanceado: 30 de 31 etiquetas de Tlaxcala en un bloque; una en entrenamiento al retirarlo. Rotado: las 31 en un bloque | Diagnóstico recalculado de `oof-*.csv`, sin nuevo entrenamiento |
| D02-calidad | 88/138 etiquetas sin `s2_peak_doy` en `features_whittaker_20_10.parquet`; la regla vigente rechaza curvas con cualquier laguna >21 días | Diagnóstico y lectura de `features.py`; ausencia no equivale a etiqueta errónea |
| D03-sesgo | Sesgo Tlaxcala seleccionado: +0.703926 principal, +0.703195 balanceado y +0.849603 rotado, t/ha | Promedio predicción menos etiqueta de las OOF respectivas |

Hashes comprobados durante esta propuesta:

- H00 `validation.json`: `2ecea854357a4a63f4f846aa420fecc42c0642a7e6301f53bcf0cddd1359d4b7`.
- H01 `phase-comparison.json`: `a95c481a1e528a46e40d38545b5e00955403bbd8366d51de55fda5a00392370a`.
- Política H01: `71353aead0fc1dd2a87e01444fb34f349ad4f9736d0e65afcd68fa638c94c099`.
- Particiones H01: `b988b4e089c298c1442808b1aa549251448a17dbcbba0437f120cfb6f98b23c0`.

Las correlaciones descritas en la exploración son diagnósticos sobre estas mismas etiquetas, no criterios para fijar columnas. El registro de ejecución importará los antecedentes desde artefactos, verificará estos hashes y distinguirá su fecha original de la fecha de importación.

## Goals / Non-Goals

**Goals:**

- Hacer identificable y reproducible cada diferencia frente a un control, manteniendo historial aunque la ejecución falle.
- Separar el efecto de cada mecanismo y evaluar una combinación predeclarada, sin decidirla usando las métricas externas de las ablaciones.
- Mantener una interfaz de ajuste, predicción, serialización y explicación que incluya soporte regional y transformaciones de consulta.

**Non-Goals:**

- No sustituir la activa durante esta fase, publicar el dashboard o enviar predicciones al organizador; se entregará un paquete elegible si corresponde.
- No entrenar modelos independientes por estado/municipio, optimizar pesos continuos ni abrir una búsqueda automática hasta lograr el umbral.
- No añadir SoilGrids, otras descargas, pseudoetiquetas de campañas previas o variables de manejo inventadas.
- No afirmar que tres particiones proporcionan 414 observaciones independientes o que cumplir los umbrales constituye validación temporal.

## Decisions

### 1. Entorno aislado y controles completos

Crear `experiments/soporte-regional-<phase-id>` a partir de la versión experimental existente. Referenciar originales en lectura con sus hashes y escribir tablas nuevas, modelos, registros e informes exclusivamente en esa copia. Preservar un manifiesto completo de la raíz activa y reproducir sus 59 predicciones antes y después de la fase en un proceso nuevo.

E00 reproduce el procedimiento oficial H01 y su ruta enriquecida, con las mismas tablas, política y particiones. Si no reproduce OOF y predicciones a tolerancia absoluta 1e-10, detener comparaciones: primero resolver versiones y compatibilidad. No reemplazar contratos históricos mediante actualización de sus hashes. Usar H00 para comparación histórica principal, pero E00 como control técnico de los cambios nuevos.

Alternativa descartada: cambiar `src` en la raíz y separar solo archivos de salida, porque alteraría el comportamiento de la versión activa y sus contratos.

### 2. Catálogo congelado antes de resultados

E00 y E01–E08 se registran como pendientes al iniciar la implementación. Congelar antes del primer ajuste población, tablas, límites, orden de experimentos, controles, esquemas y composición E08. Cambiar la política por una incidencia de implementación exige nueva versión y nueva ejecución; conservar la versión anterior con su estado. Corregir un defecto demostrado no se justifica por un RMSE desfavorable.

Las comparaciones aisladas usan datos oficiales exclusivamente: no alterar a la vez representación y admisión NASA/DGSIAP. E00 conserva ambas rutas para reproducción histórica; E08 ensaya enriquecimiento de forma independiente y pareada sobre los ganadores oficiales, con las seis ablaciones existentes. No se asignan resultados enriquecidos a controles oficiales.

| Experimento | Hipótesis y cambio único | Control y límite de candidatos oficiales | Estado al proponer |
| --- | --- | --- | --- |
| E00 | Reproducción del procedimiento regional congelado | H01; 26 candidatos, dos tablas; referencia H00 solo en principal | Pendiente |
| E01a | Evitar correcciones fuertes con 1–9 etiquetas estatales mediante atenuación dura | E00 oficial; mismos 26 candidatos y fuentes | Pendiente |
| E01b | Atenuación gradual según tamaño de entrenamiento | E00 oficial; mismos 26 candidatos; no elegir entre a/b con OOF externa | Pendiente |
| E02 | Centrar predictores dentro del estado antes de seleccionar y ajustar la corrección | E00 oficial; 26 candidatos, cambio exclusivo en los 16 compuestos | Pendiente |
| E03 | Recuperar información al sustituir `whittaker_20_10` por `whittaker_40_10` | E00 oficial; 26 candidatos; mantener `monthly_20_10`, misma grilla y selector | Pendiente |
| E04a | Conservar soporte observado mediante reconstrucción por segmentos | E00 oficial; 26 candidatos; sustituir solo tabla reconstruida por `segmented_20_10` | Pendiente |
| E04b | Añadir integrales respaldadas de EVI/MSAVI | E04a; 26 candidatos; misma reconstrucción y filtro, índices disponibles por sensor | Pendiente |
| E05 | Separar señal de cada sensor y patrones de adquisición | E00 oficial; cinco máscaras y 122 candidatos únicos como máximo | Pendiente |
| E06 | Ajustar el ruido GPR y evaluar optimización acotada de kernel | E00 oficial; 62 candidatos únicos como máximo; CatBoost y tablas intactos | Pendiente |
| E07 | Evaluar un modelo tabular preentrenado con datos pequeños | E00 oficial; dos configuraciones directas, una por tabla; comparación opcional | Pendiente |
| E08 | Evaluar soporte duro E01a + centrado E02 + segmentos E04a en una política conjunta | E00 oficial/enriquecido por ruta; 26 candidatos oficiales, seis ablaciones externas y cuatro promedios | Pendiente |

E08 excluye expresamente E01b, nubes 40%, índices adicionales E04b, máscaras E05, ajuste GPR E06 y TabPFN. Es una decisión previa sobre una combinación concreta, no una combinación de los ganadores. Los demás resultados orientarán hipótesis futuras y se conservarán aunque sean mejores. La fase termina cuando sus ejecuciones obligatorias estén cerradas, incluidas las fallidas; no requiere obtener una mejora.

Alternativa descartada: encadenar automáticamente los cambios con mejor RMSE externo o formar el producto cartesiano de todos los factores, por contaminación de decisiones y crecimiento de búsqueda.

### 3. Atenuación por soporte aplicada dentro de cada ajuste

Para un estado visto con n etiquetas en el `fit`, definir `b` como su media entrenada y `p` como la predicción del candidato original. E01a devuelve `b + w*(p-b)`, con w=0 si 1<=n<10 y w=1 si n>=10. E01b utiliza w=n/(n+10) para estados vistos. Las referencias no se atenúan; en compuestos se registra tanto alpha nominal como alpha efectivo multiplicado por w.

En un estado ausente, un compuesto conserva media global y corrección cero como exige la especificación; un modelo directo compartido conserva su predicción original y se identifica como transferencia. No trasladar a esa región una media aprendida con las etiquetas externas. Guardar n, estado visto/ausente, referencia, predicción original, atenuación y salida por parcela. E08 utiliza únicamente la regla dura, aplicada también a la selección interna y al ajuste de calibración; no introducirla solo al final de la OOF.

Una referencia entrenada con una etiqueta sigue siendo inestable. La atenuación no promete resolver el problema de representatividad y puede perder desempeño; se contrasta con el control y permanece sujeta al criterio regional.

### 4. Centrado parcelario con estadísticas de entrenamiento

E02 modifica únicamente candidatos de corrección regional. Aprender disponibilidad y medianas de entrenamiento; imputar con ellas y calcular medias de predictores por estado. Transformar z=x-media_x_train(estado), formar r=y-media_y_train(estado) y seleccionar columnas por asociación z/r, quitando constantes y redundancia como en el control. Aplicar escala y modelo a z seleccionado. Conservar k=10 GPR y k=20 CatBoost; no usar el ranking descriptivo de la exploración para fijar columnas.

Para consultas de estados ausentes, usar medias globales de predictores entrenadas como transformación recuperable y mantener corrección cero. Para estado visto, reutilizar sus medias de entrenamiento, no las de un lote de consultas. Registrar medias, medianas, columnas y escalas en los contratos. Evaluar también E02 aislado, porque E00 ya aprende residuos regionales y el aporte nuevo es el centrado de los predictores y su selección correspondiente.

### 5. Segmentos temporales y ablaciones definidas

En E04a mantener nube <=20%, lambda=10 y rejilla semanal. Dividir observaciones finitas de cada índice/sensor en saltos >21 días; suavizar independientemente segmentos con al menos cuatro observaciones distintas y sin extrapolación fuera de sus extremos. Segmentos más pequeños siguen contados en calidad, pero no generan reconstrucción. Sumar integrales de segmentos utilizables sin integrar entre extremos separados; registrar días respaldados y AUC por día respaldado, con ausencia explícita si no hay soporte. Mantener las medianas por ventanas del control.

Un máximo interior respaldado necesita al menos dos observaciones originales anteriores y dos posteriores en el segmento. Informarlo como pico local respaldado; no dar un pico o duración de toda la temporada cuando falte cobertura entre segmentos. Las variables de temporada que no puedan acreditarse permanecen NaN. Conservar método, soporte, observaciones/interpolaciones, lagunas, segmentos y motivos de ausencia. E04b añade AUC respaldada y AUC/día de EVI en Sentinel-2/Planet y MSAVI en Planet; no produce índices ausentes en Landsat ni convierte VI6T en temperatura o fenología vegetal confirmada.

E05 usa cinco máscaras predeclaradas sobre las dos tablas originales: Sentinel-2; Planet; Sentinel-2+Planet; todos los sensores; todos los sensores sin conteos de adquisición. En todas se conserva clima, topografía y área. Eliminar columnas espectrales y de cobertura del sensor retirado; la máscara sin calidad elimina conteos `coverage`, pero conserva dispersión espacial del índice como señal. No agregar indicadores de faltantes inexistentes en el control. Son 5*24 variantes predictivas más dos referencias únicas =122; la máscara se elige internamente y las métricas aisladas se describen como diagnóstico.

### 6. GPR y candidato opcional acotados

E06 conserva Matérn nu=2.5, normalización de y, tablas y selector. Su grilla fija longitudes {1,5}, ruido WhiteKernel {0.05,0.15,0.5}, y añade una variante optimizada por cada longitud inicial con ruido inicial 0.15, bounds longitud [0.3,30], ruido [0.01,1], sin reinicios adicionales. El optimizador actúa solo en cada `fit`; guardar kernel aprendido y normalización objetivo. Con dos tablas y tres modos directo/compuesto alpha {0.5,1}: 48 GPR, 12 CatBoost y dos referencias =62. No confundir ruido del kernel con intensidad de corrección.

E07 usa checkpoint TabPFN-2.5 de regresión con versiones, pesos, licencia/condiciones y parámetros efectivos congelados antes de su primer ajuste. Dos entradas: `monthly_20_10` y `whittaker_20_10`; configuración estándar documentada, semilla 2026, sin ajuste fino ni búsqueda de ensambles. Aprender imputación y escala con entrenamiento si el adaptador las requiere. Ejecutar en un entorno independiente y local; no modificar `requirements.lock` ni la versión activa para este candidato. Una dependencia, licencia o recurso incompatible produce estado omitido con motivo, sin prometer resultado ni alterar los experimentos obligatorios.

Fundamento técnico consultado: [GPR de scikit-learn](https://scikit-learn.org/stable/modules/gaussian_process.html), [validación por grupos](https://scikit-learn.org/stable/modules/cross_validation.html) y [reporte de autores de TabPFN-2.5](https://arxiv.org/abs/2511.08667). Los resultados publicados motivan hipótesis; no se transfieren como expectativas de RMSE parcelario.

### 7. Evaluación y elegibilidad separadas

Reutilizar exactamente `schemes.csv` de H01 para los tres esquemas; guardar su hash. Mantener >=15 etiquetas de validación y >=80 de entrenamiento externo, selección interna retirando un grupo disponible y los criterios internos existentes: mejora RMSE >=2%, mejora en dos folds y MAE estatal <=1.10 de su referencia cuando hay >=10 etiquetas evaluadas internamente. El soporte de cada `fit` se registra separadamente de ese conteo de evaluación.

Todos los experimentos principales producen 138 OOF finitas por esquema, métricas, sesgo p-y, tamaños y diferencias pareadas frente a E00 de su misma ruta y a la media regional del esquema. E04b usa además E04a como control de mecanismo. En E07 sin búsqueda, evaluar las dos configuraciones por separado como diagnóstico; no seleccionar una usando sus OOF externas.

Agregar `intraestado-3` solo a E00/E08: tres bloques por estado construidos mediante cortes balanceados sobre geometría UTM y orden canónico por ID; combinar el bloque local 0 de cada estado como validación 0 y análogamente 1/2. Registrar sus zonas disjuntas y composición. La construcción usa presencia de etiqueta y estado oficial, no magnitudes de rendimiento. Mantener separación parcelaria y mínimos externos; registrar inviabilidad en vez de rediseñar según resultados. Esta evaluación mide predicción dentro de regiones conocidas y no cambia la elegibilidad.

Solo E08 obtiene `eligibility.json` por ruta con todas las condiciones vigentes. El umbral principal con los datos actuales es 0.729096163 t/ha y el máximo MAE Tlaxcala principal es 0.55; recalcular ambos desde la referencia comprobada, no codificarlos como constantes universales. Comparar E08 también con H00 en principal, sin atribuir independencia temporal. Registrar `eligible`, `activated=false` y razones por condición. E01–E07 conservan diferencias y criterios diagnósticos, con `promotion_scope=exploratorio`.

E08 incluye leave-one-state-out y buffer de 1 km entre polígonos; preservar escenarios no viables. Recalibrar intervalos con selección sin etiquetas de calibración, nominal 90%, mínimo 25 y criterio de disponibilidad principal >=85%; reportar cobertura/amplitud estatal, incluso cuando el global pase. Una predicción puntual puede ser válida con intervalo desactivado. Cada ruta conserva su propio contrato y final de 59 filas. Si E08 falla, entregar la decisión negativa y terminar sin ampliar la grilla.

### 8. Registro local por ejecución y cambios del modelo

Guardar bajo la nueva copia:

| Destino propuesto | Contenido |
| --- | --- |
| `registry/catalog.json` | Hipótesis, IDs, controles, orden, obligatoriedad, protocolos y hashes |
| `registry/events.jsonl` | Eventos con secuencia, run_id, fecha UTC, estado, motivo y referencias; presentación en America/Mexico_City |
| `runs/<run-id>/protocol.json` | Configuración congelada, comparación, rutas, candidate IDs, fuentes, límites, semilla, población, tablas, grupos y versión |
| `runs/<run-id>/run.json` | Estado actual, inicios/cierres, parent/control, hashes, ejecución e incidencias |
| `runs/<run-id>/changes.json` | Diferencias estructuradas y humanas del protocolo frente al control; selección y modelo ajustados por fold/ruta y modelo final |
| `runs/<run-id>/artifacts/` | OOF, pares, métricas, soportes, decisiones internas, variables, modelos finales, contratos, intervalos, pruebas y manifiestos |
| `runs/<run-id>/result.md` | Hipótesis, qué cambió, tabla pareada, errores regionales, resultado, limitaciones y decisión |
| `registry/summary.csv` y `docs/experiment-history.md` | Índice derivado del registro: todos los runs, métricas por esquema/ruta, diferencias, verificación y enlaces |

Campos mínimos del registro: `schema_version`, `phase_id`, `experiment_id`, `run_id`, `control_run_id`, `parent_run_id`, `hypothesis`, `status`, `started_at`, `finished_at`, `cutoff`, `seed`, `data_hashes`, `code_hash`, `dependency_manifest`, `protocol_hash`, `scheme_hash`, `feature_manifest`, `changes`, `metrics`, `verification`, `artifact_manifest`, `decision`, `limitations`. Las métricas no disponibles se guardan como null, nunca cero. H00/H01 usan `origin=historical`, importación con fecha propia, artefactos de origen y cobertura realmente disponible; no se simulan esquemas H00 que no existen.

Estados de ejecución: `planned`, `frozen`, `running`, `completed`, `failed`, `interrupted`, `skipped`. `completed` significa métricas y artefactos requeridos verificados, no ganancia ni promoción. E07 puede `skipped`; una obligatoria que no se pueda ejecutar es `failed` con motivo y la fase conserva ese resultado. Una ejecución fallida no se borra ni se reetiqueta completada al reintentarse.

Un solo escritor mantiene el registro de la fase. Crear protocolo con rechazo de colisión; validar el hash al ajustar. Cerrar resultados y manifiesto con archivos temporales y reemplazo atómico en el mismo volumen, dejando el evento de cierre al final; generar índices solo desde runs con manifiestos válidos. Un fallo entre escrituras conserva el último estado verificable y requiere un evento de recuperación antes de volver a publicar el índice. Reintentar crea nuevo run_id con `retry_of`; reanudar solo conserva el ID si coinciden todos los hashes y el checkpoint es verificable. Detectar un proceso anterior terminado registra interrupción, nunca inventa un éxito. No ejecutar writers simultáneos.

`changes.json` distingue cambio de procedimiento de cambio de modelo finalmente ajustado: familias, parámetros declarados/efectivos, tablas, máscaras, columnas, estadísticas, intensidad, soporte, fuentes, componentes, pesos y hashes anteriores/nuevos. Las etiquetas no cambian en esta fase. Sin ajuste final, registrar modelo ausente y el motivo. Correcciones de interpretación del informe generan una revisión con `supersedes`, conservando el original y sin cambiar métricas históricas.

Al finalizar cada run: comprobar OOF y métricas, contratos y resultados; guardar diferencias y manifiesto; cerrar estado y decisión; regenerar índice e informe; emitir una actualización breve al usuario con el efecto y la siguiente prueba. La actualización no espera al informe final. E00/E08 guardan además modelos finales y 59 salidas por ruta en procesos nuevos; las ablaciones obligatorias E01–E06 guardan final oficial y 59 salidas para registrar el cambio efectivo. E07 completado conserva checkpoint, adaptador/configuración, contexto de entrenamiento y 59 salidas por configuración, sin exigir un archivo joblib convencional.

Alternativa descartada: MLflow remoto, porque agrega un servicio y dependencia operativa innecesarios para esta fase local. JSON/CSV permite revisar y transportar evidencia con el proyecto.

## Risks / Trade-offs

- [Desarrollo repetido sobre las mismas etiquetas] → Predeclarar E08, conservar decisiones internas y llamar desarrollo a toda la fase; nueva campaña sigue pendiente.
- [Media estatal basada en una sola etiqueta] → Mostrar soporte y sesgo; comparar atenuación dura y gradual sin ajustar offsets con OOF externa.
- [Una laguna oculta un máximo no observado] → Conservar integrales respaldadas y picos locales, manteniendo ausentes las fases de temporada no acreditadas.
- [Mayor grilla de máscaras o kernels favorece ajuste interno] → Límites explícitos, evaluación anidada y exclusión de sus ganadores de E08.
- [E08 pierde un diagnóstico favorable de E03/E06/E07] → Aceptar el costo de una composición previa; una incorporación futura exige otra política registrada.
- [TabPFN requiere recursos o condiciones incompatibles] → Candidato opcional en entorno separado, resultado omitido trazable y continuidad de obligatorios.
- [Fallo al actualizar registro] → Manifiestos, eventos, escritor único y publicación atómica; no presentar un índice viejo como resultado nuevo.
- [Cambios experimentales contaminan la activa] → Destinos aislados, versión íntegra recuperable y comprobación de hashes/predicciones al inicio y al cierre.

## Migration Plan

### Incidencia de implementación registrada

El primer intento de `intraestado-3` reutilizó cortes binarios y produjo tamaños globales 68/35/35, con entrenamiento mínimo de 70. La incidencia se detectó por tamaños geométricos, sin usar errores de variantes para decidir la corrección. La revisión 2 implementa el balance declarado con tres cortes iguales sobre el eje UTM de mayor extensión, desempate por ID y asignación canónica; los tamaños globales son 47/46/45. Se conservan la política, el código y el intento parcial anteriores, y se crean IDs nuevos con `retry_of`. Los tres esquemas H01 y la composición E08 permanecen iguales. La evidencia se guarda en `experiments/soporte-regional-20261003/registry/partition-revision.json`.

### Secuencia de entrega

El primer intento TabPFN (`E07-v2-monthly_20_10`) terminó de entrenar, pero su CSV `float32` redondeó hasta 2.2082519546273716e-7 y no cumplió la comprobación absoluta 1e-10. Al reconstruir se obtuvieron exactamente los mismos valores float32; la incidencia pertenece a la exportación. El reintento `E07-v3` mantiene modelo, pesos, parámetros, tablas y particiones, y exporta float64 con 17 dígitos. Usa un adaptador en una raíz independiente con código y datos recuperables, dejando intacto el código base congelado de E00–E08. El catálogo adicional y los protocolos de ambas configuraciones se congelaron antes de repetir los entrenamientos. Se conservan los intentos fallidos y las relaciones `retry_of` en `registry/optional-retry-catalog.json`.

1. Verificar paquetes H00/H01 y crear la nueva copia aislada; conservar hashes y predicciones activas.
2. Implementar registro, comandos y contratos; importar antecedentes y registrar todos los experimentos pendientes sin métricas.
3. Congelar política, controles, composición E08 y particiones; verificar E00 antes de comparaciones.
4. Implementar y ejecutar E01–E06 secuencialmente, registrando cada run y su control; cerrar E07 con ejecución o motivo de omisión.
5. Ejecutar E08 oficial/enriquecido, diagnósticos, intervalos, pruebas e inferencia reproducible; publicar su elegibilidad por ruta.
6. Entregar registro completo y, si procede, paquete candidato sin activar; comprobar otra vez la versión activa. Una ejecución negativa conserva todos sus artefactos y no provoca sustitución.
7. Una activación posterior usará un paquete íntegro y una decisión explícita independiente; su recuperación utilizará el paquete anterior completo.
