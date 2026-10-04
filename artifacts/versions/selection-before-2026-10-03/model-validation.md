# Validación del modelo

Resultado de ejecución local con semilla 2026 y corte fijo 2025-10-31. Se evalúa un procedimiento de selección anidado; no se elige un ganador mirando el error externo y después se atribuye ese mismo error a una selección independiente. El test oculto de 59 parcelas no tiene etiquetas locales.

## Evaluación principal

Cinco grupos geográficos se construyeron con geometrías únicamente, en UTM 14N, por cortes balanceados sobre el eje de mayor extensión. Tamaños 34, 34, 35, 17 y 18; cada validación tiene al menos 15 etiquetas y cada entrenamiento al menos 80. `folds.csv` y `spatial-folds.html` permiten inspeccionar cobertura y vecindad. Apan/Tepeapulco no forman un fold de dos etiquetas.

Inner usa GroupKFold con tres particiones de los grupos de outer-train. Imputación por mediana, disponibilidad ≥50%, eliminación de constantes, ranking por correlación con y y exclusión de redundancia absoluta >0.95 se ajustan dentro de cada entrenamiento. Después se estandariza. Hasta veinte variables por modelo, diez en GPR. Cambiar deliberadamente etiquetas outer-test no modifica la configuración ni el modelo ajustados, como verifica la prueba de contaminación.

La búsqueda predefinida contiene 81 configuraciones: nueve representaciones temporales por ElasticNet (alpha 0.05/0.2, l1_ratio 0.25), Bayesian Ridge, SVR-RBF (C 1/10, epsilon 0.1), CatBoost (profundidad 2/3, 220 iteraciones, tasa 0.03, L2=10) y GPR (Matérn 2.5, longitud 1/5, ruido 0.15, sin optimización de kernel). No se usa outer-test para early stopping. Las alternativas temporales se calculan por parcela sin y; su elección por rendimiento pertenece al ajuste interno.

| procedimiento | rmse | mae | r2 |
| --- | --- | --- | --- |
| selected | 0.7902 | 0.6051 | 0.1317 |
| official | 0.7748 | 0.5895 | 0.1653 |
| global_mean | 0.9930 | 0.8853 | -0.3710 |
| global_median | 1.1442 | 0.9720 | -0.8201 |
| regional_mean | 0.7440 | 0.5697 | 0.2304 |
| with_location | 0.7268 | 0.5239 | 0.2654 |
| elastic | 0.7660 | 0.5791 | 0.1842 |
| bayesian | 0.7646 | 0.5760 | 0.1872 |
| svr | 0.7525 | 0.6166 | 0.2127 |
| catboost | 0.7179 | 0.5765 | 0.2834 |
| gpr | 0.7049 | 0.5285 | 0.3092 |

Cada familia tiene su propia configuración elegida internamente y predicciones externas guardadas. `official` evalúa selección y ensamble con solo datos del reto; `selected` añade candidatos que superen el criterio interno. `with_location` es sensibilidad con coordenadas, no reemplazo post hoc del procedimiento principal. Referencias de media/mediana global y media regional se calculan solo con train; un estado no visto utiliza la media global.

| fold | train | validación | RMSE | estrategia | fuentes | calibración |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 104 | 34 | 0.5799 | individual |  | 34 |
| 1 | 104 | 34 | 1.1776 | convexo |  | 34 |
| 2 | 103 | 35 | 0.6325 | promedio |  | 34 |
| 3 | 121 | 17 | 0.7537 | individual | siap | 34 |
| 4 | 120 | 18 | 0.4676 | individual | nasa | 34 |

## Fuentes y ensambles

Antes de observar resultados se guardó `selection-policy.json`: añadir NASA, DGSIAP o ensamble exige reducción relativa de RMSE ≥2%, mejora en al menos dos folds internos y deterioro de MAE regional ≤10% cuando esa región tiene ≥10 ejemplos. NASA y DGSIAP se ensayan secuencialmente sobre la referencia vigente; decisiones completas están en `source-decisions.csv` y `validation.json`. Ningún peso se optimiza sobre OOF externa.

Se evalúa promedio de dos familias complementarias y después pesos convexos mediante SLSQP sobre sus OOF internas, con restricciones de no negatividad y suma uno. Si no supera el criterio, se mantiene el individuo o promedio previo. El ajuste final aplica ese mismo procedimiento a las 138 etiquetas: estrategia **individual**, pesos **[1.0]**, candidatos **[('bayesian', 'monthly_20_10', [])]**. El RMSE interno final 0.7167 no sustituye la evaluación externa.

## Errores regionales y superficie

| estado | rmse | mae | r2 |
| --- | --- | --- | --- |
| Hidalgo | 1.1634 | 1.0307 | -1.3023 |
| Puebla | 0.6077 | 0.4338 | -0.0966 |
| Tlaxcala | 0.6020 | 0.5032 | -1.6485 |

| tercil | rmse | mae | r2 |
| --- | --- | --- | --- |
| mediana | 0.7248 | 0.5472 | 0.0720 |
| pequeña | 0.7366 | 0.5442 | 0.2154 |
| grande | 0.9009 | 0.7279 | -0.0895 |

`regional-comparison.csv` incluye errores por estado de todos los procedimientos. Las etiquetas de Tlaxcala toman solo tres valores: esta estructura y el fuerte contraste regional deben acompañar la lectura del desempeño. No se redondean predicciones ni se adjudica importancia causal a proxies regionales. `feature-stability.csv` describe frecuencia de selección en outer-train, sin escoger retrospectivamente un subconjunto usando outer-test.

## Transferencia y separación adicional

Leave-one-state-out retira por completo cada estado y repite selección oficial dentro de los otros. Es un escenario de transferencia más exigente, distinto del reto que incluye los tres estados.

| held_out_state | n | rmse | mae | r2 |
| --- | --- | --- | --- | --- |
| Hidalgo | 36 | 0.9736 | 0.7972 | -0.6122 |
| Puebla | 71 | 0.7028 | 0.5422 | -0.4668 |
| Tlaxcala | 31 | 0.6502 | 0.5417 | -2.0893 |

Buffer de 1 km entre puntos representativos es sensibilidad, no una distancia obligatoria tomada de la literatura. Solo se evalúa si quedan ≥80 etiquetas de entrenamiento; los casos inviables se conservan como tales. No implica distancia de borde exacta ni validación temporal.

| fold | buffer_m | status | train_remaining | rmse | mae | r2 |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 1000 | evaluado | 103 | 1.0914 | 1.0054 | -7.6467 |
| 1 | 1000 | evaluado | 95 | 1.1175 | 0.9237 | -0.7770 |
| 2 | 1000 | evaluado | 88 | 0.6770 | 0.4798 | -0.4244 |
| 3 | 1000 | evaluado | 114 | 0.5803 | 0.5202 | -0.1815 |
| 4 | 1000 | evaluado | 105 | 0.5125 | 0.4385 | -0.5405 |

## Intervalos y recursos

Calibración por un grupo interno separado, al menos 25 etiquetas, selección repetida sin sus etiquetas, cuantíl superior de residuos absolutos con corrección de tamaño y nominal 90%. Cobertura externa global **88.41%**, amplitud media **2.6046 t/ha**, presentación admitida **True**. La cobertura mínima predefinida es 85%; no se cambia el nominal al observar fallos. Centro del modelo calibrado separado, dependencia espacial y falta de campañas nuevas limitan garantías. El detalle por estado está en `interval-quality.json`.

Tiempo medido del entrenamiento completo: **53.17 minutos**. Máximo RSS observado al cierre de folds: **230.8 MB**, no pico instantáneo certificado. CPU limitada a dos hilos por biblioteca/estimador; no se usó GPU ni cómputo remoto. Estas mediciones corresponden a la computadora y versiones registradas, y no incluyen la preparación previa de datos.

## Reproducir

`python -m agrocebada.cli prepare`, `python scripts/check_preparation.py`, `python -m agrocebada.cli train`, `python -m agrocebada.cli verify`. Dependencias exactas en `requirements.lock`. La verificación recalcula métricas desde `oof.csv` y reproduce las 59 predicciones con el modelo guardado. Pruebas separadas comprueban fuga, compatibilidad, física de fuentes y comportamiento del dashboard sin red.
