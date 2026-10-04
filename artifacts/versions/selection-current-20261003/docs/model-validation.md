# Validación del modelo

Resultado de ejecución local con semilla 2026 y corte fijo 2025-10-31. Se evalúa un procedimiento de selección anidado; no se elige un ganador mirando el error externo y después se atribuye ese mismo error a una selección independiente. El test oculto de 59 parcelas no tiene etiquetas locales.

## Evaluación principal

Cinco grupos geográficos se construyeron con geometrías únicamente, en UTM 14N, por cortes balanceados sobre el eje de mayor extensión. Tamaños 34, 34, 35, 17 y 18; cada validación tiene al menos 15 etiquetas y cada entrenamiento al menos 80. `folds.csv` y `spatial-folds.html` permiten inspeccionar cobertura y vecindad. Apan/Tepeapulco no forman un fold de dos etiquetas.

Inner usa GroupKFold retirando un grupo espacial por partición, con tantos folds como grupos disponibles en outer-train. Se reproduce así la separación externa sin combinar bloques que puedan retirar un estado completo. Imputación por mediana, disponibilidad ≥50%, eliminación de constantes, ranking por correlación con y y exclusión de redundancia absoluta >0.95 se ajustan dentro de cada entrenamiento. Después se estandariza. Hasta veinte variables por modelo, diez en GPR. Cambiar deliberadamente etiquetas outer-test no modifica la configuración ni el modelo ajustados, como verifica la prueba de contaminación.

La búsqueda contiene 81 configuraciones: nueve representaciones temporales por ElasticNet (alpha 0.05/0.2, l1_ratio 0.25), Bayesian Ridge, SVR-RBF (C 1/10, epsilon 0.1), CatBoost (profundidad 2/3, 220 iteraciones, tasa 0.03, L2=10) y GPR (Matérn 2.5, longitud 1/5, ruido 0.15, sin optimización de kernel). La media global y regional participan además como modelos elegibles en las mismas particiones internas. Los indicadores de estado proceden de la geometría oficial; sus medias se ajustan solo con train. No se usa outer-test para early stopping. Las alternativas temporales se calculan por parcela sin y; su elección por rendimiento pertenece al ajuste interno.

| procedimiento | rmse | mae | r2 |
| --- | --- | --- | --- |
| selected | 0.7641 | 0.5927 | 0.1883 |
| official | 0.7646 | 0.5935 | 0.1872 |
| global_mean | 0.9930 | 0.8853 | -0.3710 |
| global_median | 1.1442 | 0.9720 | -0.8201 |
| regional_mean | 0.7440 | 0.5697 | 0.2304 |
| with_location | 0.7477 | 0.5550 | 0.2227 |
| elastic | 0.7413 | 0.5639 | 0.2359 |
| bayesian | 0.7592 | 0.5718 | 0.1985 |
| svr | 0.8004 | 0.6700 | 0.1093 |
| catboost | 0.7129 | 0.5704 | 0.2935 |
| gpr | 0.6969 | 0.5171 | 0.3247 |

Cada familia tiene su propia configuración elegida internamente y predicciones externas guardadas. `official` evalúa selección y ensamble con solo datos del reto; `selected` añade candidatos que superen el criterio interno. `with_location` es sensibilidad con coordenadas, no reemplazo post hoc del procedimiento principal. Referencias de media/mediana global y media regional se calculan solo con train; un estado no visto utiliza la media global.

| fold | train | validación | RMSE | estrategia | fuentes | calibración |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 104 | 34 | 0.5748 | individual |  | 34 |
| 1 | 104 | 34 | 1.1154 | individual |  | 34 |
| 2 | 103 | 35 | 0.6255 | diverso |  | 34 |
| 3 | 121 | 17 | 0.7220 | promedio |  | 34 |
| 4 | 120 | 18 | 0.4988 | individual | nasa | 34 |

## Fuentes y ensambles

Antes de esta ejecución se guardó `selection-policy.json`: reemplazar la mejor media interna por un modelo, añadir NASA, DGSIAP o ensamble exige reducción relativa de RMSE ≥2%, mejora en al menos dos folds internos y deterioro de MAE regional ≤10% cuando esa región tiene ≥10 ejemplos. Las fuentes se ensayan sobre el ganador interno de cada familia, secuencialmente; las referencias no incorporan fuentes externas. Decisiones completas están en `source-decisions.csv` y `validation.json`. Ningún peso se optimiza sobre OOF externa. Esta revisión se motivó por los resultados anteriores de las mismas 138 etiquetas; la nueva OOF mide el procedimiento revisado pero no constituye un test independiente de esa decisión de desarrollo.

Se evalúa un promedio uniforme de los ganadores de cada familia y la mejor referencia, un promedio de dos componentes y pesos convexos para esos dos componentes mediante SLSQP sobre OOF internas. Se exige no negatividad y suma uno. Cada reemplazo debe superar el criterio frente a la opción vigente y la referencia. Si no lo logra, se conserva el procedimiento anterior. El ajuste final aplica ese mismo procedimiento a las 138 etiquetas: estrategia **individual**, pesos **[1.0]**, candidatos **[('gpr', 'whittaker_40_10', ['nasa'])]**. El RMSE interno final 0.6398 no sustituye la evaluación externa.

## Errores regionales y superficie

| estado | rmse | mae | r2 |
| --- | --- | --- | --- |
| Hidalgo | 1.1014 | 0.9827 | -1.0633 |
| Puebla | 0.6068 | 0.4409 | -0.0935 |
| Tlaxcala | 0.5889 | 0.4873 | -1.5347 |

| tercil | rmse | mae | r2 |
| --- | --- | --- | --- |
| mediana | 0.7035 | 0.5306 | 0.1258 |
| pequeña | 0.7313 | 0.5635 | 0.2267 |
| grande | 0.8525 | 0.6873 | 0.0246 |

`regional-comparison.csv` incluye errores por estado de todos los procedimientos. Las etiquetas de Tlaxcala toman solo tres valores: esta estructura y el fuerte contraste regional deben acompañar la lectura del desempeño. No se redondean predicciones ni se adjudica importancia causal a proxies regionales. `feature-stability.csv` describe frecuencia de selección en outer-train, sin escoger retrospectivamente un subconjunto usando outer-test.

## Transferencia y separación adicional

Leave-one-state-out retira por completo cada estado y repite selección oficial dentro de los otros. Es un escenario de transferencia más exigente, distinto del reto que incluye los tres estados.

| held_out_state | n | rmse | mae | r2 |
| --- | --- | --- | --- | --- |
| Hidalgo | 36 | 0.8574 | 0.6933 | -0.2505 |
| Puebla | 71 | 0.7028 | 0.5422 | -0.4668 |
| Tlaxcala | 31 | 0.5792 | 0.4866 | -1.4516 |

Buffer de 1 km entre puntos representativos es sensibilidad, no una distancia obligatoria tomada de la literatura. Solo se evalúa si quedan ≥80 etiquetas de entrenamiento; los casos inviables se conservan como tales. No implica distancia de borde exacta ni validación temporal.

| fold | buffer_m | status | train_remaining | rmse | mae | r2 |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 1000 | evaluado | 103 | 1.0914 | 1.0054 | -7.6467 |
| 1 | 1000 | evaluado | 95 | 1.0830 | 0.8828 | -0.6688 |
| 2 | 1000 | evaluado | 88 | 0.6584 | 0.4678 | -0.3468 |
| 3 | 1000 | evaluado | 114 | 0.7597 | 0.6938 | -1.0248 |
| 4 | 1000 | evaluado | 105 | 0.5133 | 0.4459 | -0.5454 |

## Intervalos y recursos

Calibración por un grupo interno separado, al menos 25 etiquetas, selección repetida sin sus etiquetas, cuantíl superior de residuos absolutos con corrección de tamaño y nominal 90%. Cobertura externa global **92.03%**, amplitud media **2.9353 t/ha**, presentación admitida **True**. La cobertura mínima predefinida es 85%; no se cambia el nominal al observar fallos. Centro del modelo calibrado separado, dependencia espacial y falta de campañas nuevas limitan garantías. El detalle por estado está en `interval-quality.json`.

Tiempo medido del entrenamiento completo: **6.23 minutos**. Máximo RSS observado al cierre de folds: **229.0 MB**, no pico instantáneo certificado. CPU limitada a dos hilos por biblioteca/estimador; no se usó GPU ni cómputo remoto. Estas mediciones corresponden a la computadora y versiones registradas, y no incluyen la preparación previa de datos.

## Reproducir

`python -m agrocebada.cli prepare`, `python scripts/check_preparation.py`, `python -m agrocebada.cli train`, `python -m agrocebada.cli verify`. Dependencias exactas en `requirements.lock`. La verificación recalcula métricas desde `oof.csv` y reproduce las 59 predicciones con el modelo guardado. Pruebas separadas comprueban fuga, compatibilidad, física de fuentes y comportamiento del dashboard sin red.
