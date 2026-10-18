# Conclusiones de la evaluación prioritaria

Se completaron las 12 ejecuciones predeclaradas de P00–P08 y su recuperación sin red. P06 no es elegible para sustituir el modelo activo. TabPFN-3 mensual ofrece una señal favorable en los tres esquemas, pero sigue siendo un diagnóstico experimental y no modifica esa decisión.

Las métricas usan las mismas 138 etiquetas de una campaña, abril–octubre de 2025. Las 59 consultas no tienen etiquetas para medir exactitud. La repetición de investigaciones sobre estas etiquetas limita la fuerza de cualquier mejora observada; no se afirma validación en una nueva campaña ni haber agotado todos los modelos posibles.

| Procedimiento | RMSE principal | RMSE balanceado | RMSE rotado |
| --- | --- | --- | --- |
| P00-C-activa | 0.764573 | 0.808494 | 0.761048 |
| P00-C-soporte | 0.756346 | 0.764389 | 0.749169 |
| P01 | 0.756130 | 0.782792 | 0.787680 |
| P02 | 0.781325 | 0.780101 | 0.808298 |
| P03 | 0.756915 | 0.750231 | 0.883896 |
| P04 | 0.779307 | 0.774607 | 0.821665 |
| P05 | 0.822607 | 0.813583 | 0.920293 |
| P06 | 0.754369 | 0.738843 | 0.918634 |
| P07-monthly_20_10 | 0.749756 | 0.755085 | 0.624633 |
| P07-whittaker_20_10 | 0.761585 | 0.764385 | 0.643578 |
| P08-monthly_20_10 | 0.737668 | 0.733853 | 0.687838 |
| P08-whittaker_20_10 | 0.744175 | 0.744782 | 0.689426 |

Todas las cifras de RMSE están en t/ha; menor es mejor. Las filas P00 usan su ruta oficial. Las rutas seleccionadas de los controles, MAE, sesgo, estado, superficie y fold están en [resultados completos](priority-results.md) y `detailed-results.json`.

## Decisión P06

Los umbrales quedaron congelados antes de los resultados. Fallaron las siguientes condiciones: mejora principal de al menos 2% frente a media regional; mejora de al menos 2% en dos esquemas; razón media ≤0,98 frente a media regional; protección de MAE por estado; mejora principal de al menos 2% frente a la activa; y deterioro máximo de 5% en cualquier esquema frente a la activa.

En principal, P06 mejora 1.33% frente a la activa, por debajo del 2% exigido, y empeora 1.40% frente a media regional. En rotado empeora 20.71% frente a la activa.

| Esquema | Estado | n | MAE P06 | MAE media regional | Aumento |
| --- | --- | --- | --- | --- | --- |
| principal-5 | Puebla | 71 | 0.467940 | 0.414921 | 12.78% |
| rotado-45-5 | Puebla | 71 | 0.505078 | 0.377922 | 33.65% |

La protección estatal permite como máximo 10% de aumento de MAE en estados con al menos diez etiquetas. La receta P06 no se reconfiguró con ganadores externos. Se conserva también la decisión negativa E08 histórica. Activación, despliegue y envío permanecen en false.

## Qué aportan las comparaciones

- La lista agronómica mejora frente al ranking en 20/24 pares del esquema principal y 20/24 del balanceado; el efecto es menos uniforme en rotado. Esto apoya revisar el filtro, pero la selección anidada P01 no produce una mejora estable entre los tres esquemas.
- El tiempo térmico gana en dos de cuatro pares por esquema y pierde en otros dos, con diferencias medianas pequeñas. Esta comparación mantiene el mismo contexto NASA y no se atribuye a la ruta oficial.
- La covarianza estatal GPR ayuda en algunos pares; el efecto estatal Ridge empeora en todos los pares comparados. La estructura regional necesita soporte suficiente: un fold rotado no tiene etiquetas de Tlaxcala en entrenamiento.
- Las dos interacciones EBM mejoran sus pares aditivos en los tres esquemas, aunque el procedimiento P04 no mejora de forma estable frente a los controles. Las curvas funcionales tampoco muestran una ventaja consistente.
- TabICL v2 mensual tiene el menor RMSE rotado entre estas configuraciones fijas. TabPFN-3 mensual mejora frente a la activa en los tres esquemas. Son procedimientos diagnósticos separados: no se selecciona una tabla, se mezclan pesos ni se incorporan a P06 a partir de esas OOF.

Los [405 contrastes de mecanismos](mechanism-comparisons.md) y la comparación pareada con TabPFN 2.5 (`optional-vs-TabPFN25.json`) conservan tanto resultados favorables como negativos. Sus mínimos individuales son descriptivos y no sustituyen la selección interna.

## Sensibilidad e intervalos

| Sensibilidad P06 | Exclusión | Estado | Train | Validación | RMSE | Motivo |
| --- | --- | --- | --- | --- | --- | --- |
| exclusión estatal | Hidalgo | completed | 102 | 36 | 0.809934 | — |
| exclusión estatal | Puebla | non_viable | 67 | 71 | — | Train menor que 80 o menos de dos grupos internos |
| exclusión estatal | Tlaxcala | completed | 107 | 31 | 1.306416 | — |
| buffer 1000 m | 0 | completed | 103 | 34 | 1.322736 | — |
| buffer 1000 m | 1 | completed | 90 | 34 | 0.980160 | — |
| buffer 1000 m | 2 | non_viable | 79 | 35 | — | Train menor que 80 o menos de dos grupos internos |
| buffer 1000 m | 3 | completed | 103 | 17 | 0.914659 | — |
| buffer 1000 m | 4 | completed | 97 | 18 | 0.603286 | — |

Las sensibilidades inviables no se cuentan como predicciones evaluadas ni se promedian con las completadas. Los casos de estado ausente completados verificaron la media global exacta; los buffers usan distancia entre polígonos y mínimo de 1000 m.

Los intervalos de nominal 90% cubren 96.38% de las 138 etiquetas en el esquema principal, con amplitud media 3.300 t/ha. La calibración final reserva 34 etiquetas. La disponibilidad de intervalos (True) es una comprobación separada de la elegibilidad puntual y no revierte el rechazo P06. El detalle por estado está en `runs/P06/artifacts/intervals.json`.

## Cobertura y recuperación

La [matriz de evidencia y cobertura](evidence-and-coverage.md) vincula P00–P08 con L01–L08, controles, estados y artefactos reales. BART, TabM, NGBoost, radar, ERA5, SoilGrids, AlphaEarth, simulación completa de cultivo y variantes de mayor complejidad siguen explícitamente diferidos; no fueron probados en esta fase.

Pasaron 47 pruebas de cierre. Se verificaron los 12 paquetes, tres entornos de dependencias, las 59 consultas por ruta y las métricas recalculadas. Los 133 archivos protegidos siguen intactos. Las 12 versiones históricas convencionales reprodujeron ambas rutas y los dos contextos TabPFN 2.5 recuperaron sus consultas con el entorno original. El intento histórico fallido bajo ajustes numéricos nuevos permanece documentado.

Véanse [recuperación](recovery.md), `registry/package-verification.json` y `registry/final-integrity-receipt.json` para recibos y límites de reproducción.
