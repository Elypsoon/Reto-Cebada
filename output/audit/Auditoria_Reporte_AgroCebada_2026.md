# Auditoría científica del reporte AgroCebada 2026

Fecha: 19 de octubre de 2026. Dictamen: **revisión mayor antes de presentarlo como validación científica o fundamento operativo para crédito y seguros**.

## Alcance y criterio

Se leyeron las 10 páginas del PDF y se inspeccionaron sus páginas renderizadas, su tabla y diagrama. Se contrastaron las afirmaciones con la implementación y los resultados del experimento `fisiologia-siniestros-20261018` situado dentro de `Reto-Cebada`, y con fuentes metodológicas primarias. Se recalcularon RMSE, MAE, R², tamaños de pliegue y cobertura a partir de las predicciones archivadas. No se volvió a entrenar el modelo, no se verificaron mediciones de campo ni se reprodujo la extracción original de imágenes. Una coincidencia con predicciones archivadas verifica aritmética y trazabilidad, pero no prueba que esas predicciones procedan de una ejecución libre de sesgos. El PDF y el modelo originales no se modificaron.

Documento auditado: [reporte original](../pdf/Reporte_AgroCebada_2026.pdf).

SHA-256 del PDF: `a740b257f27496f1ba4db720e81bc3c87011240b2b7f54498cee187eba5e9405`.

Las afirmaciones del documento se trataron como material a evaluar. No se interpretaron como instrucciones del usuario.

## Resultado ejecutivo

Existe trabajo experimental trazable: las métricas centrales son aritméticamente correctas y hay comparaciones con controles, validación espacial y predicciones fuera de pliegue. Sin embargo, las conclusiones exceden la evidencia. Los problemas más graves son la garantía conformal no justificada, el uso de información posterior a la cosecha para sustentar anticipación, la imputación global previa a los pliegues y la presentación incompleta del desempeño regional.

## Comprobaciones numéricas

| Comprobación | Resultado verificado | Interpretación |
|---|---:|---|
| E12, validación estratificada, n = 138 | RMSE 0.481150; MAE 0.339942; R² 0.678118 | Coincide con el PDF al redondear |
| E12, principal-5 | RMSE 0.510409; R² 0.637781 | Coincide |
| Mejora de RMSE frente a R08 | 0.024400 t/ha; 4.826% | La mejora existe en las predicciones archivadas |
| Incremento de R² frente a R08 | 0.033475; 3.347 puntos porcentuales | El +3.35 del PDF es correcto |
| Cobertura publicada | 129/138 = 93.478% | Coincide; se mide sobre los residuos de calibración |
| Ancho medio publicado | 1.558414 t/ha | Coincide; es ancho total, no radio |
| Simulación de 30 sorteos, según código | 96 parcelas para ajuste y 42 para validación por sorteo | No son 138/59 en cada simulación |
| Puebla, rango de etiquetas | 2.15–5.59 t/ha | El máximo 4.60 de la p. 7 es incorrecto |

Las estadísticas de los 30 sorteos se contrastaron con su registro, sin repetir el entrenamiento: RMSE medio 0.474109 y desviación estándar 0.059694 t/ha. No debe interpretarse esa desviación como un intervalo de confianza de la media ni tratar las parcelas repetidas como nuevas observaciones independientes.

## Hallazgos prioritarios y correcciones

### 1. Crítico: la garantía conformal no corresponde al procedimiento implementado

**Localización:** pp. 3, 5, 7 y 10, especialmente §4.5.

La función `calibrate_conformal_intervals` calcula cuantiles con los errores absolutos de las 138 predicciones fuera de pliegue y evalúa cobertura sobre esos mismos 138 errores. Además mezcla el radio estatal con el global mediante `0.75*r_estatal + 0.25*r_global`. Esto no es el procedimiento split-conformal descrito en el texto, ni acredita por sí solo la garantía finita anunciada. Que cada predicción sea fuera de pliegue no convierte en independiente la evaluación posterior del radio ajustado con todos los errores. Tampoco se demuestra que la mezcla de radios preserve cobertura estatal.

La cobertura de calibración es Hidalgo 35/36 = 97.22%, Puebla 63/71 = 88.73% y Tlaxcala 31/31 = 100%. El promedio global no acredita el 90% en cada región. Estos resultados tampoco validan cobertura bajo los otros esquemas espaciales.

**Corrección:** denominar lo actual «intervalos empíricos calibrados con residuos OOF», eliminar la garantía hasta justificarla y evaluar cobertura en un conjunto externo no usado para ajustar radios ni seleccionar modelos. Si se desea una garantía conformal, implementar y documentar split-conformal o una construcción de validación cruzada con su teorema y supuestos correspondientes. La dependencia espacial y el cambio entre campañas requieren tratamiento explícito. [Fundamento conformal, secciones 1, 3 y 6](https://arxiv.org/html/2107.07511v6).

### 2. Crítico para uso anticipado: información de noviembre–diciembre del mismo año

**Localización:** pp. 1–4, 8–10.

F6 utiliza explícitamente imágenes de noviembre–diciembre de 2025, y E12 incorpora `g1_pl_evi_novdec` en la rama de Hidalgo. Son datos posteriores a la campaña abril–octubre que consta en la documentación local. Permiten una estimación retrospectiva, pero no sustentan un pronóstico disponible antes de la cosecha o al originar un crédito. La interpolación temporal bidireccional también necesita respetar una fecha de disponibilidad si se usa en tiempo real.

**Corrección:** fijar fecha de emisión y anticipación por parcela, reconstruir todas las variables usando solo información disponible entonces y reevaluar. Si el reto permite el año completo, conservar esa evaluación como retrospectiva y limitar a ese escenario las conclusiones. La autorización del reto para usar datos no demuestra disponibilidad anticipada.

### 3. Alto: la ausencia absoluta de fuga se contradice con la imputación global

**Localización:** p. 4, §4.2.

Las funciones de características F1–F5 y F6 rellenan ausencias con la mediana de la columna antes de construir y aplicar los pliegues. La matriz se construye para el conjunto de parcelas. Los contrastes espaciales también calculan medianas y referencias con el conjunto disponible. Por tanto, es falsa la afirmación de que toda imputación y referencia se calcula exclusivamente con el entrenamiento de cada pliegue.

Esto evidencia uso global de covariables; no demuestra que se hayan usado las etiquetas de las 59 parcelas ocultas. Algunos contrastes pueden defenderse como aprendizaje transductivo, pero deben declararse así. El efecto numérico de la imputación global queda pendiente de una nueva ejecución: no se cuantificó si las columnas tenían ausencias relevantes en esta corrida.

**Corrección:** ajustar medianas y referencias aprendidas dentro de cada pliegue; explicar por separado los cálculos geométricos deterministas y cualquier uso transductivo de covariables. Comparar contra una ejecución estrictamente inductiva.

### 4. Alto: el desempeño regional contradice la robustez generalizada

**Localización:** pp. 6–7 y 10.

| Estado | n etiquetado | RMSE E12 estratificado | R² estratificado | R² principal-5 | R² rotado-45-5 |
|---|---:|---:|---:|---:|---:|
| Puebla | 71 | 0.5747 | 0.0192 | -0.0441 | -0.0482 |
| Hidalgo | 36 | 0.3330 | 0.8114 | 0.6870 | 0.7450 |
| Tlaxcala | 31 | 0.3814 | -0.0630 | -0.0293 | -1.6722 |

El R² global de 0.6781 coexiste con poca capacidad explicativa dentro de Puebla y con resultados negativos en Tlaxcala. Un R² negativo significa mayor suma de errores cuadrados que la referencia constante igual a la media del subconjunto evaluado; esa media es una referencia descriptiva, no necesariamente un predictor disponible en producción. Frente al control operativo B0, E12 también empeora en Tlaxcala: RMSE 0.3814 frente a 0.3747 y MAE 0.2927 frente a 0.2835. En Puebla mejora el RMSE, pero empeora el MAE: 0.4106 frente a 0.3832.

**Corrección:** incluir métricas y tamaños por estado, los tres esquemas espaciales y comparaciones contra B0. Presentar la utilidad regional como heterogénea. Los datos no sustentan capacidad uniforme en todo el territorio.

### 5. Alto: se confunden población, conjunto oculto y prueba independiente

**Localización:** pp. 3–4 y 7.

Las 138 etiquetas corresponden a Puebla, Hidalgo y Tlaxcala; las 59 predicciones ocultas también pertenecen a esos tres estados. No hay Guanajuato en los archivos de evaluación revisados. Las 59 parcelas carecen de etiqueta en este flujo: no aportan resultados de evaluación independiente publicados. Las métricas citadas provienen de validación interna sobre las 138 etiquetas.

`StratifiedKFold(5)` usa aproximadamente 80/20: 110/28 o 111/27 parcelas, no 70/30. Los 30 sorteos usan 96/42 sobre las 138 etiquetadas. Las muestras se solapan entre sorteos y no equivalen a 30 campañas independientes.

**Corrección:** separar con claridad CV de 5 pliegues, holdout repetido y conjunto oculto; eliminar Guanajuato del ámbito empírico salvo aportar sus registros. Indicar año de cosecha, municipio, origen de la etiqueta y fecha de medición.

### 6. Alto: la arquitectura matemática no describe fielmente E12

**Localización:** p. 5, §4.4 y diagrama de p. 3.

CatBoost usa `loss_function="MAE"`, Ridge su criterio cuadrático y GPR su modelo probabilístico. El corrector regional combina `HuberRegressor(epsilon=1.35)` con Ridge; no se observa una pérdida Huber común con umbral fijo δ = 0.5 t/ha. La fórmula genérica omite varias ramas, medias municipales, reglas estatales, mezclas y recortes de predicción.

El componente denominado Kriging es una media ponderada por kernels y anclajes; en esa rama no se muestra la estimación de un variograma ni la solución del sistema de kriging. El ancho de kernel de 35 m tampoco es un corte duro: `exp(-0.5*(d/35)**2)` conserva peso para distancias mayores. La caracterización como Empirical Bayes necesita explicar qué parámetros se estiman y de dónde provienen constantes como 0.08 y los límites 0.25–0.90; parte de la adaptación depende de densidad de vecinos, no de una varianza predictiva formal.

**Corrección:** escribir el algoritmo exacto con sus hiperparámetros, pérdidas y reglas; llamarlo suavizado espacial por kernels donde corresponda. Justificar el nombre bayesiano o describirlo como contracción regularizada heurística.

### 7. Alto: afirmaciones causales y diagnósticas sin contraste de campo

**Localización:** p. 7, §5.3 y conclusiones.

Las correlaciones no prueban que heladas, humedad o suelo causaron las diferencias de rendimiento. En particular, `r = -0.493` entre temperatura mínima y rendimiento indica que temperaturas mínimas mayores se asocian con rendimientos menores; por sí sola no respalda la explicación inmediata de daño por heladas. El vigor de enero–marzo no es una medición directa de humedad y puede reflejar otro cultivo, maleza, cobertura o manejo. Un mínimo de píxeles tampoco equivale a diagnóstico confirmado de siniestro.

**Corrección:** presentar mecanismos como hipótesis agronómicas, incluir dispersogramas por municipio/régimen y controlar confusores. Verificar eventos con fechas fenológicas observadas, estaciones y visitas de campo. Reportar asociaciones exploratorias y su incertidumbre, sin llamar a esto diagnóstico preciso.

### 8. Alto: resolución meteorológica y umbrales descritos incorrectamente

**Localización:** pp. 3–4.

El código agrupa consultas por coordenadas redondeadas a 0.05°, alrededor de 5 km. Ese espaciamiento no es la resolución nativa del clima. Las 25 respuestas almacenadas contienen solo 15 pares distintos de coordenadas devueltas. La documentación de Open-Meteo especifica IFS a 9 km, ERA5 a unos 25 km y ERA5-Land a unos 11 km; su producto de 5 km CERRA corresponde a Europa. Deben identificarse el producto y las variables efectivamente descargadas. [Documentación del proveedor](https://open-meteo.com/en/docs/historical-weather-api).

El PDF menciona calor por encima de 31 °C y helada a 0 °C; las características F7 suman excesos sobre 25 °C y déficits bajo 5 °C o 4 °C. Pueden ser índices de estrés, pero no son los umbrales que declara el reporte. La corrección `+0.04*TPI` y el gradiente térmico aplicado requieren fundamento y validación local; no son mediciones de microclima.

**Corrección:** distinguir malla de consulta, resolución de origen y corrección topográfica; publicar fórmula, unidades, producto, fecha y umbrales exactos, y evaluar sensibilidad.

### 9. Alto: el supuesto límite de Bayes carece de estimación

**Localización:** pp. 7–8 y 10.

No se estima una cota de error irreducible mediante mediciones repetidas, error instrumental o descomposición validada del ruido. El MAE de aproximadamente 340 kg/ha no demuestra proximidad al piso declarado de 200–300 kg/ha. Tampoco basta citar redondeo o variables omitidas para cuantificar ese piso.

**Corrección:** eliminar «converge al límite teórico» y la recomendación de abandonar mejoras algorítmicas. Expresar que falta identificar cuánto error se debe a medición, información faltante o modelo.

### 10. Alto: utilidad financiera presentada como demostrada

**Localización:** pp. 8–10.

Con los propios supuestos del PDF, el margen es 3,900 MXN/ha y 0.34 t/ha equivalen a 1,972 MXN/ha: **50.6% del margen**. No hay evidencia para concluir que esa desviación es absorbible o que no compromete el crédito. MAE tampoco significa que cada error esté acotado por ±0.34 t/ha.

Un intervalo de rendimiento no establece automáticamente probabilidad de impago ni una regla de indemnización validada. «Erradica el riesgo de base», «blindando rentabilidad» y garantías de inclusión financiera deben sustituirse por aplicaciones potenciales. No se presentan resultados de cartera, siniestros, precios reales por calidad o evaluación prospectiva. Los precios, costos y porcentajes de castigo necesitan fecha, región, contrato y fuente; aquí se audita su aritmética, no se certifica su vigencia comercial.

**Corrección:** conservar un ejemplo económico expresamente hipotético, con sensibilidad y pérdidas por decisiones. Validar por separado cualquier uso crediticio o asegurador.

### 11. Alto: selección de modelo y precisión estadística incompletas

**Localización:** pp. 4 y 6–7.

Hay al menos 12 variantes E01–E12 y decisiones regionales ajustadas al conjunto. El reporte no demuestra que toda elección de variables y constantes haya quedado fuera de la evaluación que se publica. El registro congelado se escribe desde el propio ejecutor; su nombre y hash no prueban por sí solos un prerregistro anterior a explorar los resultados.

Existe evidencia estadística adicional omitida: la comparación archivada de E12 contra R08 registra IC bootstrap de la diferencia de RMSE [-0.0430, -0.0026] t/ha y p bilateral 0.048. Es evidencia exploratoria favorable, condicionada al remuestreo utilizado; no incorpora automáticamente selección entre múltiples candidatos ni dependencia espacial. Desde E09 hasta E12 la mejora adicional de RMSE global es solo 0.0068 t/ha y el MAE empeora de 0.3364 a 0.3399. No toda métrica mejora de forma continua.

**Corrección:** documentar cronología, búsqueda completa y criterio de selección; evaluar mediante partición externa o CV anidada que incluya todas las decisiones aprendidas. Usar incertidumbre acorde con la unidad espacial y explicar que la generalización entre campañas no ha sido evaluada. [Referencia oficial sobre sesgo de selección](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

### 12. Medio: reproducibilidad, referencias y presentación

**Localización:** conjunto del documento.

- No hay bibliografía ni citas para algoritmos, sensores, supuestos agronómicos o cifras económicas. La existencia de fuentes en el repositorio no sustituye su cita en el reporte.
- Faltan identificación de autores, fecha/versión, disponibilidad de datos y código, y detalle de la obtención del rendimiento: humedad de estandarización, área medida, báscula, encuesta y trazabilidad por lote.
- El recorte al «10% interno» no define si se erosiona área, distancia o una estadística; se requiere procedimiento y evidencia de la extracción original.
- La fórmula del intervalo en la p. 5 está mal compuesta. Debe leerse `[ŷ_i − q̂_k, ŷ_i + q̂_k]`.
- El diagrama de la p. 3 usa texto demasiado pequeño y carece de número y pie explicativo. La p. 6 deja gran espacio vacío tras la tabla.
- Debe usarse «intervalo de predicción», diferenciado de un intervalo de confianza de parámetros. Los intervalos son de ancho constante dentro de cada estado en esta implementación.

## Orden de corrección recomendado

1. Corregir el alcance temporal, las particiones y la evaluación de intervalos; repetir validación después de mover la imputación al interior de los pliegues.
2. Publicar los resultados completos por estado y por esquema, incluyendo los negativos y el conjunto oculto sin etiquetas.
3. Reescribir metodología según el código, aclarar productos meteorológicos y retirar las garantías causal, bayesiana, financiera y de error irreducible que carecen de demostración.
4. Añadir bibliografía, tabla de procedencia y disponibilidad temporal de variables, hiperparámetros, fechas de medición y disponibilidad de código/datos.
5. Corregir rango de Puebla, ecuación y figuras antes de emitir una nueva versión.

## Conclusión científicamente defendible con la evidencia actual

En una evaluación interna de 138 parcelas etiquetadas de tres estados de la campaña 2025, E12 obtuvo RMSE de 0.4812 t/ha y MAE de 0.3399 t/ha con predicciones archivadas de validación estratificada de cinco pliegues. El rendimiento varía sustancialmente entre estados y esquemas espaciales. Las mejoras frente a R08 son prometedoras, pero requieren una reevaluación que controle el preprocesamiento y la selección. Los intervalos publicados tienen cobertura de calibración de 93.48%; su cobertura externa, su garantía formal y la utilidad para pronóstico previo a cosecha y decisiones financieras aún no están demostradas.

## Evidencia local y herramientas

Rutas relativas a este archivo, dentro del mismo proyecto:

- [Implementación del modelo y calibración, líneas 125–160 y 520–720](../../experiments/fisiologia-siniestros-20261018/src/fisiologia_siniestros/modeling.py).
- [Construcción de características, líneas 175–415](../../experiments/fisiologia-siniestros-20261018/src/fisiologia_siniestros/features.py).
- [Ejecución, particiones y evaluación, líneas 73–84, 121–185 y 191–286](../../experiments/fisiologia-siniestros-20261018/scripts/execute_phase.py).
- [Métricas E12 y desempeño por estado](../../experiments/fisiologia-siniestros-20261018/runs/E12/metrics.json).
- [Predicciones OOF estratificadas E12](../../experiments/fisiologia-siniestros-20261018/runs/E12/oof-estratificado-5.csv), además de las de los tres esquemas espaciales y los controles B0, R08 y E09 del mismo directorio de corridas.
- [Radios y cobertura de calibración](../../experiments/fisiologia-siniestros-20261018/registry/interval-calibration.json).
- [Comparaciones pareadas](../../experiments/fisiologia-siniestros-20261018/registry/paired-comparisons.json).
- [Registro de los 30 sorteos](../../experiments/fisiologia-siniestros-20261018/registry/holdout-70-30-simulation.json).
- [Predicciones de las 59 parcelas ocultas](../../experiments/fisiologia-siniestros-20261018/runs/E12/predictions_59_intervals.csv).
- [Respuestas meteorológicas almacenadas](../../data/external/open_meteo_daily_2025_nodes.json).
- [Definición local de datos y campaña](../../docs/data-validation.md).
- [Comprobaciones numéricas de esta auditoría](comprobaciones_AgroCebada_2026.json).

Herramientas: extracción con pypdf; renderizado con Poppler; recálculo con pandas/NumPy; inspección de código y documentación primaria. Se aplicaron las habilidades locales de PDF y scikit-learn. Referencia del recurso de procedimientos científicos utilizado: Kassis, T., Agarwal, V., He, Y., Patel, D., y Brueckner, A. M. (2026). [Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://doi.org/10.48550/arXiv.2609.00065). Esta referencia documenta la herramienta de apoyo; no constituye evidencia a favor o en contra del modelo auditado.
