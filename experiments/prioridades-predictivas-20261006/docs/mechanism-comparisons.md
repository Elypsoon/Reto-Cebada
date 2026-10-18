# Contrastes de mecanismos

Cada par utiliza las mismas 138 etiquetas y configuración, variando únicamente el mecanismo indicado. Los resultados son descriptivos y no eligen ni sustituyen modelos.

| Bloque | Esquema | Contraste | Pares completos | Pares con menor RMSE | Mediana Δ RMSE (t/ha) |
| --- | --- | --- | --- | --- | --- |
| P01 | balanceado-4 | Selector agronomic frente a rank | 24/24 | 20 | -0.015027 |
| P01 | balanceado-4 | Selector all frente a rank | 24/24 | 12 | -0.000730 |
| P01 | principal-5 | Selector agronomic frente a rank | 24/24 | 20 | -0.014064 |
| P01 | principal-5 | Selector all frente a rank | 24/24 | 14 | -0.002851 |
| P01 | rotado-45-5 | Selector agronomic frente a rank | 24/24 | 14 | -0.001851 |
| P01 | rotado-45-5 | Selector all frente a rank | 24/24 | 12 | -0.000242 |
| P02 | balanceado-4 | Tiempo térmico frente a calendario; contexto NASA idéntico | 4/4 | 2 | -0.000068 |
| P02 | principal-5 | Tiempo térmico frente a calendario; contexto NASA idéntico | 4/4 | 2 | -0.000594 |
| P02 | rotado-45-5 | Tiempo térmico frente a calendario; contexto NASA idéntico | 4/4 | 2 | -0.000294 |
| P03 | balanceado-4 | GPR con covarianza estatal frente a tau²=0 | 8/8 | 4 | -0.070756 |
| P03 | balanceado-4 | Ridge con efecto estatal frente a sin efecto estatal | 18/18 | 0 | +0.027262 |
| P03 | principal-5 | GPR con covarianza estatal frente a tau²=0 | 8/8 | 4 | -0.065257 |
| P03 | principal-5 | Ridge con efecto estatal frente a sin efecto estatal | 18/18 | 0 | +0.028188 |
| P03 | rotado-45-5 | GPR con covarianza estatal frente a tau²=0 | 8/8 | 4 | -0.012371 |
| P03 | rotado-45-5 | Ridge con efecto estatal frente a sin efecto estatal | 18/18 | 0 | +0.010850 |
| P04 | balanceado-4 | EBM con dos interacciones frente a aditivo | 6/6 | 6 | -0.006914 |
| P04 | balanceado-4 | GAM con cuatro nudos frente a tres | 9/9 | 6 | -0.003415 |
| P04 | principal-5 | EBM con dos interacciones frente a aditivo | 6/6 | 6 | -0.008598 |
| P04 | principal-5 | GAM con cuatro nudos frente a tres | 9/9 | 6 | -0.003754 |
| P04 | rotado-45-5 | EBM con dos interacciones frente a aditivo | 6/6 | 5 | -0.003050 |
| P04 | rotado-45-5 | GAM con cuatro nudos frente a tres | 9/9 | 3 | +0.004812 |
| P05 | balanceado-4 | Proyección funcional frente a resúmenes calendarizados | 30/30 | 15 | -0.000206 |
| P05 | principal-5 | Proyección funcional frente a resúmenes calendarizados | 30/30 | 15 | -0.000130 |
| P05 | rotado-45-5 | Proyección funcional frente a resúmenes calendarizados | 30/30 | 15 | +0.000052 |
| P06 | balanceado-4 | Representación funcional frente a compacta; diagnóstico fijo de P06 | 12/12 | 4 | +0.002270 |
| P06 | principal-5 | Representación funcional frente a compacta; diagnóstico fijo de P06 | 12/12 | 3 | +0.004884 |
| P06 | rotado-45-5 | Representación funcional frente a compacta; diagnóstico fijo de P06 | 12/12 | 2 | +0.002385 |

Los mínimos individuales observados se publican en mechanism-comparisons.json como diagnósticos. No se ajustan pesos ni se usa OOF externa para reconfigurar P06.

Las diferencias por parcela y por estado están en paired-mechanisms.csv y mechanism-comparisons.json. Una mejora en un par no demuestra estabilidad entre campañas.
