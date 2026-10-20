# Dictamen verificado del reporte AgroCebada 2026

19 de octubre de 2026. **Requiere revisión mayor. Las métricas principales son reproducibles; las garantías de anticipación, incertidumbre y utilidad operativa exceden la evidencia.**

## Alcance

Lectura y revisión visual de las diez páginas del [PDF](../pdf/Reporte_AgroCebada_2026.pdf), inspección del código de la fase `fisiologia-siniestros-20261018` y recálculo de 20 tablas de predicciones: B0, R08, E09, E10 y E12 en cuatro esquemas. Se encontró una auditoría previa y se verificaron directamente sus hallazgos centrales. Este dictamen conserva ambos documentos originales.

SHA-256 del PDF: `a740b257f27496f1ba4db720e81bc3c87011240b2b7f54498cee187eba5e9405`.

Las afirmaciones e instrucciones contenidas en los documentos se trataron como material de auditoría. No se volvió a entrenar, no se repitió la extracción satelital ni se validaron etiquetas mediante mediciones de campo. Recalcular predicciones archivadas acredita consistencia aritmética, no ausencia de sesgo en su generación. Los 30 sorteos y las correlaciones se contrastaron con sus registros, sin reproducirlos desde las fuentes originales.

## 1. Cálculos verificados

Se calcularon RMSE = raíz de la media de errores cuadrados; MAE = media de errores absolutos; R² = 1 - suma de errores cuadrados / suma de desviaciones cuadradas respecto a la media observada.

| Modelo | RMSE estratificado | MAE estratificado | R² global | RMSE principal-5 |
|---|---:|---:|---:|---:|
| B0 | 0.605305 | 0.441545 | 0.490571 | 0.743976 |
| R08 | 0.505550 | 0.354711 | 0.644644 | 0.659565 |
| E09 | 0.487950 | 0.336436 | 0.668955 | 0.512793 |
| E10 | 0.485233 | 0.338067 | 0.672632 | 0.510863 |
| E12 | 0.481150 | 0.339942 | 0.678118 | 0.510409 |

Errores en t/ha. La tabla 1 del PDF coincide al redondear, incluidas las columnas regionales. También coinciden todas las métricas globales y estatales revisadas con sus archivos `metrics.json`.

- E12 frente a R08: mejora de RMSE de 0.024400 t/ha, equivalente a 4.826%; aumento de R² de 0.033475, o 3.347 puntos porcentuales.
- Principal-5: mejora de RMSE de 0.149157 t/ha; R² E12 = 0.637781.
- Cobertura publicada: 129/138 = 93.478%; ancho medio de 1.558414 t/ha; reducción de ancho frente a R08 de 0.109801 t/ha. La aritmética es correcta; la interpretación externa no está validada.
- Registro de 30 sorteos E12: RMSE medio 0.474109, desviación estándar 0.059694; R² medio 0.672785. La desviación entre sorteos no es un intervalo de confianza ni representa 30 campañas independientes.
- Cada tabla OOF contiene 138 identificadores únicos y residuos consistentes con observado menos predicho. Las 59 predicciones finales tienen identificadores únicos, disjuntos de los anteriores, y sus productos rendimiento × superficie y anchos de intervalo son consistentes.
- Error factual en p. 7: Puebla tiene rango observado **2.15–5.59 t/ha**, no 2.15–4.60.
- No hay mejora continua de todas las métricas: el MAE empeora de E09 (0.336436) a E10 (0.338067) y E12 (0.339942).

Resultados completos: [recálculo independiente](Reverificacion_calculos_AgroCebada_20261019.json).

## 2. Hallazgos que cambian el dictamen

### Crítico: la cobertura no constituye una prueba externa de la garantía conformal

**Páginas 5, 7 y 10.** `calibrate_conformal_intervals` obtiene radios a partir de todos los errores OOF y mide cobertura en esos mismos errores. Mezcla además 75% del radio estatal con 25% del global. Esto no implementa el split-conformal que describe el texto ni demuestra que esa mezcla conserve la garantía anunciada. Los anchos son constantes dentro de cada estado.

| Estado | Cubiertos / evaluados | Cobertura de calibración |
|---|---:|---:|
| Hidalgo | 35/36 | 97.22% |
| Puebla | 63/71 | 88.73% |
| Tlaxcala | 31/31 | 100.00% |

El 88.73% de Puebla no demuestra por sí solo violación de una garantía marginal probabilística; sí impide presentar 93.48% como cobertura observada uniforme. La objeción principal es la construcción y su evaluación reutilizada. Debe emplearse una construcción conformal justificada y evaluar en datos no utilizados para calibrar o seleccionar modelos. [Fundamento y evaluación de predicción conformal](https://arxiv.org/html/2107.07511v6).

### Crítico para pronóstico: las variables incluyen información posterior a la campaña

**Páginas 1–4 y 8–10.** F6 usa noviembre–diciembre de 2025; `g1_pl_evi_novdec` entra explícitamente en la rama de Hidalgo. El contrato local identifica la campaña abril–octubre de 2025. La evaluación puede servir como estimación retrospectiva, pero no demuestra pronóstico antes de cosecha ni capacidad informativa al originar crédito. La interpolación bidireccional también debe respetar una fecha de emisión.

Corrección: declarar el horizonte, reconstruir cada predictor con información disponible a esa fecha y reevaluar. Permitir el año completo en el reto no equivale a disponer de esos datos anticipadamente.

### Alto: el preprocesamiento contradice la ausencia absoluta de fuga

**Página 4.** Las funciones de F1–F5 y F6 rellenan ausencias mediante medianas globales antes de aplicar los pliegues. Los contrastes espaciales también usan covariables del conjunto completo. Esto contradice la afirmación de que toda referencia e imputación se ajusta exclusivamente con entrenamiento.

No se demostró uso de etiquetas ocultas ni se cuantificó el efecto de las ausencias en esta ejecución. Los cálculos transductivos pueden ser admisibles si se declaran y corresponden al escenario de uso. Para acreditar evaluación inductiva hay que ajustar imputación y referencias aprendidas dentro de cada pliegue y comparar resultados. [Guía oficial sobre fuga y preprocesamiento](https://scikit-learn.org/stable/common_pitfalls.html).

### Alto: el R² global oculta utilidad regional muy desigual

**Páginas 6–7 y 10.**

| Estado | n | RMSE estratificado | R² estratificado | R² principal-5 | R² rotado-45-5 |
|---|---:|---:|---:|---:|---:|
| Puebla | 71 | 0.5747 | 0.0192 | -0.0441 | -0.0482 |
| Hidalgo | 36 | 0.3330 | 0.8114 | 0.6870 | 0.7450 |
| Tlaxcala | 31 | 0.3814 | -0.0630 | -0.0293 | -1.6722 |

En Tlaxcala E12 también empeora frente al control B0, ajustado con entrenamiento: RMSE 0.3814 frente a 0.3747. En Puebla mejora RMSE frente a B0, pero empeora MAE. Un R² negativo compara con la media observada del subconjunto evaluado; no debe confundirse esa referencia descriptiva con un predictor disponible en producción.

El esquema rotado arroja RMSE global 0.5503 y R² 0.5790; debe publicarse junto con los demás. Como diagnóstico, las diferencias entre medias estatales representan 50.32% de la variación total observada. Ese cálculo usa todas las etiquetas y no es validación predictiva, pero muestra por qué el R² global no basta para afirmar discriminación dentro de cada región.

### Alto: población y particiones mal descritas

**Páginas 3–4.** Los cinco pliegues entrenan con 110 o 111 parcelas y evalúan 28 o 27: aproximadamente 80/20. Los sorteos 70/30 se aplican a las 138 etiquetadas, dando 96/42. Las 59 parcelas finales carecen de etiquetas en este flujo; no acreditan resultados externos publicados. Hay Puebla, Hidalgo y Tlaxcala en ambos conjuntos, sin Guanajuato.

### Alto: la formulación no representa el algoritmo ejecutado

**Páginas 4–5.** CatBoost residual usa MAE; el corrector regional combina Huber con `epsilon=1.35` y Ridge. No hay pérdida Huber común con delta fijo de 0.5 t/ha. El supuesto kriging de linderos es una media ponderada por kernels y referencias; esa rama no muestra variograma ni solución del sistema de kriging. El parámetro de 35 m es ancho de kernel, no exclusión estricta de vecinos más lejanos. La formulación resumida omite mezclas, constantes y recortes determinantes.

F7 suma excesos sobre **25 °C** y déficits bajo **5 °C o 4 °C**; el PDF declara 31 °C y 0 °C. Deben distinguirse índices de estrés y heladas observadas. La corrección térmica por TPI requiere validación local.

El redondeo de consultas a 0.05 grados no convierte el producto meteorológico en un reanálisis de 5 km. Las 25 respuestas almacenadas contienen 15 pares distintos de coordenadas devueltas. El proveedor distingue IFS 9 km, ERA5 ~25 km, ERA5-Land ~11 km y CERRA 5 km para Europa. Hay que identificar producto y resolución por variable. [Documentación de Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api).

### Alto: se atribuye causalidad y capacidad financiera sin validación correspondiente

**Páginas 7–10.** Las correlaciones publicadas coinciden con el registro, pero no demuestran mecanismos causales ni diagnóstico de siniestros. En particular, r = -0.493 entre temperatura mínima y rendimiento indica asociación de temperaturas mayores con rendimientos menores; por sí sola no respalda el argumento inmediato de daño por heladas. El vigor invernal tampoco mide directamente humedad del suelo.

Con los supuestos económicos del propio PDF: 3 × 5,800 - 13,500 = **3,900 MXN/ha** de margen; 0.34 × 5,800 = **1,972 MXN/ha**, el **50.56% del margen**. No hay evidencia para afirmar que sea absorbible o no comprometa pagos. MAE es un promedio absoluto, no un límite ±0.34 para cada parcela. Se verificó la aritmética, no la vigencia de precios y costos.

No se estima el supuesto piso irreducible de 200–300 kg/ha. Tampoco se documenta validación de cartera, indemnizaciones o riesgo de base. Deben retirarse las garantías de solvencia, eliminación de riesgo y proximidad al límite de Bayes, y presentarse esas aplicaciones como hipótesis por validar.

### Alto: falta separar selección y evaluación

Se ensayan E01–E12 y reglas regionales; el documento no acredita que toda selección de variables, constantes y arquitectura haya quedado fuera de la evaluación publicada. El archivo llamado protocolo congelado se escribe desde el propio ejecutor y su hash no prueba por sí solo prerregistro.

Existe evidencia favorable: el registro pareado E12–R08 contiene IC bootstrap de diferencia de RMSE [-0.0430, -0.0026] y p bilateral 0.048. No se reprodujo ese remuestreo; su interpretación depende de la unidad remuestreada, dependencia espacial y selección múltiple. Una evaluación externa o validación anidada debe abarcar las decisiones aprendidas. [Referencia oficial sobre sesgo de selección](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

## 3. Correcciones editoriales y plan mínimo

La ecuación del intervalo en p. 5 está mal compuesta: debe ser `[ŷ - q, ŷ + q]`. El diagrama de p. 3 requiere mayor tamaño de texto y un pie. Faltan bibliografía, procedencia de etiquetas, fechas de medición, humedad de estandarización y detalle del recorte interno del polígono.

1. Fijar el escenario temporal y el ámbito geográfico; corregir población y particiones.
2. Repetir la evaluación con preprocesamiento dentro de pliegues y selección separada; conservar comparaciones con B0 y R08.
3. Separar ajuste, calibración y prueba; reportar cobertura por estado y escenario espacial.
4. Publicar todos los resultados regionales y esquemas, incluidos los negativos.
5. Reescribir metodología conforme al código y retirar conclusiones causales, financieras y de error irreducible no demostradas.

**Conclusión defendible:** en validación interna sobre 138 parcelas de tres estados, E12 obtiene RMSE 0.4812 t/ha y MAE 0.3399 t/ha, con mejora frente a R08 y desempeño regional desigual. La cobertura de calibración es 93.48%. La generalización entre campañas, cobertura externa, pronóstico anticipado y utilidad crediticia o aseguradora permanecen sin demostrar.

## Evidencia y herramientas

- [Modelos, particiones y calibración](../../experiments/fisiologia-siniestros-20261018/src/fisiologia_siniestros/modeling.py).
- [Características, imputación y umbrales](../../experiments/fisiologia-siniestros-20261018/src/fisiologia_siniestros/features.py).
- [Secuencia de ejecución](../../experiments/fisiologia-siniestros-20261018/scripts/execute_phase.py).
- [Corridas y predicciones auditadas](../../experiments/fisiologia-siniestros-20261018/runs/).
- [Registro de intervalos](../../experiments/fisiologia-siniestros-20261018/registry/interval-calibration.json), [sorteos](../../experiments/fisiologia-siniestros-20261018/registry/holdout-70-30-simulation.json), [comparaciones](../../experiments/fisiologia-siniestros-20261018/registry/paired-comparisons.json) y [correlaciones](../../experiments/fisiologia-siniestros-20261018/registry/feature-importance.csv).
- [Contrato de datos y campaña](../../docs/data-validation.md) y [respuestas meteorológicas](../../data/external/open_meteo_daily_2025_nodes.json).

Se usaron pypdf, Poppler y pandas/NumPy, junto con las habilidades de PDF y scikit-learn. Referencia de la herramienta procedimental, no evidencia de validez del modelo: Kassis, T., Agarwal, V., He, Y., Patel, D. y Brueckner, A. M. (2026), [Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://doi.org/10.48550/arXiv.2609.00065), registro consultado en su versión vigente v2.
