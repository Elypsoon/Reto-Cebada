# Evaluación de prioridades predictivas

Evidencia de desarrollo sobre las mismas 138 etiquetas de abril–octubre de 2025. No es una validación de otra campaña.

Versión congelada: `f582940ed8bbb99e0d7d21065bca6df347cffc877fdcf2766151c24e9969facf`.

| Ejecución | Estado | Predicción externa verificada | Motivo |
| --- | --- | --- | --- |
| P00-C-activa | completed | True | — |
| P00-C-soporte | completed | True | — |
| P01 | completed | True | — |
| P02 | completed | True | — |
| P03 | completed | True | — |
| P04 | completed | True | — |
| P05 | completed | True | — |
| P06 | completed | True | — |
| P07-monthly_20_10 | completed | True | — |
| P07-whittaker_20_10 | completed | True | — |
| P08-monthly_20_10 | completed | True | — |
| P08-whittaker_20_10 | completed | True | — |

| Ejecución | Ruta | Esquema | RMSE (t/ha) | MAE | Sesgo | Δ RMSE activa oficial |
| --- | --- | --- | --- | --- | --- | --- |
| P00-C-activa | official | balanceado-4 | 0.808494 | 0.615228 | 0.150110 | +0.000000 |
| P00-C-activa | selected | balanceado-4 | 0.808494 | 0.615228 | 0.150110 | +0.000000 |
| P00-C-activa | official | intraestado-3 | 0.632023 | 0.475035 | -0.008022 | — |
| P00-C-activa | selected | intraestado-3 | 0.632023 | 0.475035 | -0.008022 | — |
| P00-C-activa | official | principal-5 | 0.764573 | 0.593509 | 0.109382 | +0.000000 |
| P00-C-activa | selected | principal-5 | 0.764053 | 0.592685 | 0.114071 | -0.000521 |
| P00-C-activa | official | rotado-45-5 | 0.761048 | 0.633836 | 0.156506 | +0.000000 |
| P00-C-activa | selected | rotado-45-5 | 0.776111 | 0.646639 | 0.137131 | +0.015062 |
| P00-C-soporte | official | balanceado-4 | 0.764389 | 0.599947 | 0.180592 | -0.044104 |
| P00-C-soporte | selected | balanceado-4 | 0.769436 | 0.603165 | 0.198139 | -0.039058 |
| P00-C-soporte | official | intraestado-3 | 0.647705 | 0.484062 | -0.007403 | — |
| P00-C-soporte | selected | intraestado-3 | 0.647705 | 0.484062 | -0.007403 | — |
| P00-C-soporte | official | principal-5 | 0.756346 | 0.603169 | 0.159040 | -0.008228 |
| P00-C-soporte | selected | principal-5 | 0.749458 | 0.596553 | 0.158253 | -0.015116 |
| P00-C-soporte | official | rotado-45-5 | 0.749169 | 0.592095 | 0.149697 | -0.011880 |
| P00-C-soporte | selected | rotado-45-5 | 0.749169 | 0.592095 | 0.149697 | -0.011880 |
| P01 | official | balanceado-4 | 0.782792 | 0.632690 | 0.167934 | -0.025702 |
| P01 | official | principal-5 | 0.756130 | 0.607350 | 0.144045 | -0.008444 |
| P01 | official | rotado-45-5 | 0.787680 | 0.620228 | 0.189923 | +0.026631 |
| P02 | official | balanceado-4 | 0.780101 | 0.622802 | 0.180994 | -0.028393 |
| P02 | official | principal-5 | 0.781325 | 0.623696 | 0.162351 | +0.016752 |
| P02 | official | rotado-45-5 | 0.808298 | 0.628824 | 0.226696 | +0.047250 |
| P03 | official | balanceado-4 | 0.750231 | 0.579794 | 0.092042 | -0.058263 |
| P03 | official | principal-5 | 0.756915 | 0.587237 | 0.051450 | -0.007659 |
| P03 | official | rotado-45-5 | 0.883896 | 0.721695 | 0.225936 | +0.122848 |
| P04 | official | balanceado-4 | 0.774607 | 0.617388 | 0.172547 | -0.033887 |
| P04 | official | principal-5 | 0.779307 | 0.629055 | 0.172692 | +0.014734 |
| P04 | official | rotado-45-5 | 0.821665 | 0.659158 | 0.157166 | +0.060617 |
| P05 | official | balanceado-4 | 0.813583 | 0.640337 | 0.013282 | +0.005090 |
| P05 | official | principal-5 | 0.822607 | 0.651332 | 0.004114 | +0.058033 |
| P05 | official | rotado-45-5 | 0.920293 | 0.778893 | 0.149013 | +0.159244 |
| P06 | official | balanceado-4 | 0.738843 | 0.571213 | 0.143103 | -0.069651 |
| P06 | official | intraestado-3 | 0.643239 | 0.494898 | -0.023685 | — |
| P06 | official | principal-5 | 0.754369 | 0.600941 | 0.121925 | -0.010204 |
| P06 | official | rotado-45-5 | 0.918634 | 0.760834 | 0.226217 | +0.157586 |
| P07-monthly_20_10 | official | balanceado-4 | 0.755085 | 0.569363 | 0.144188 | -0.053409 |
| P07-monthly_20_10 | official | principal-5 | 0.749756 | 0.564933 | 0.149386 | -0.014817 |
| P07-monthly_20_10 | official | rotado-45-5 | 0.624633 | 0.487438 | 0.088730 | -0.136415 |
| P07-whittaker_20_10 | official | balanceado-4 | 0.764385 | 0.579081 | 0.131322 | -0.044109 |
| P07-whittaker_20_10 | official | principal-5 | 0.761585 | 0.576563 | 0.133507 | -0.002989 |
| P07-whittaker_20_10 | official | rotado-45-5 | 0.643578 | 0.506359 | 0.079329 | -0.117470 |
| P08-monthly_20_10 | official | balanceado-4 | 0.733853 | 0.540817 | 0.116552 | -0.074641 |
| P08-monthly_20_10 | official | principal-5 | 0.737668 | 0.542344 | 0.120338 | -0.026906 |
| P08-monthly_20_10 | official | rotado-45-5 | 0.687838 | 0.520954 | 0.120105 | -0.073211 |
| P08-whittaker_20_10 | official | balanceado-4 | 0.744782 | 0.549007 | 0.112977 | -0.063711 |
| P08-whittaker_20_10 | official | principal-5 | 0.744175 | 0.546381 | 0.123283 | -0.020398 |
| P08-whittaker_20_10 | official | rotado-45-5 | 0.689426 | 0.528530 | 0.114225 | -0.071622 |

Elegibilidad P06: False. Activación, despliegue y envío: false.

Comprobaciones: {'official_combined_only': True, 'three_complete_schemes': True, 'controls_reproduced': True, 'verification': True, 'principal_gain': False, 'two_schemes_gain': False, 'mean_ratio': False, 'none_above_105': True, 'regional_protection': False, 'principal_active_gain': False, 'none_above_active_105': False}

Fallos de protección estatal: [{'scheme': 'principal-5', 'state': 'Puebla', 'n': 71, 'mae': 0.4679401414327172, 'regional_mae': 0.41492147898662796}, {'scheme': 'rotado-45-5', 'state': 'Puebla', 'n': 71, 'mae': 0.5050776228011545, 'regional_mae': 0.37792164303387926}]

Las configuraciones individuales conservan OOF y resultados en cada ejecución; ninguna sustituye retrospectivamente la selección interna.

Las referencias agronómicas y la bibliografía motivan hipótesis, sin demostrar ganancias locales. Véase la matriz de evidencia y cobertura.

BART, TabM, NGBoost, radar, ERA5, SoilGrids, AlphaEarth y simulación completa de cultivo siguen diferidos. No se afirma haber probado todas las posibilidades.

Un fallo, interrupción u omisión cierra su incidencia, pero no certifica evaluación predictiva completa.
