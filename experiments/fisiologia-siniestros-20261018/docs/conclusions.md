# Conclusiones y Decisión Arquitectónica — Fase `fisiologia-siniestros-20261018`

## 1. Hallazgos Principales de los Experimentos (`E01`–`E08`)

1. **Rompimiento de la barrera de `0.500 t/ha` en el esquema oficial estratificado (`E06`)**:
   - Al combinar el **Kriging Multiescala con Similitud Agronómica (`E04`)** con un **Corrector Residual Intra-Estatal Huber-Ridge (`E06`)** alimentado exclusivamente por las variables con mayor señal física dentro de Puebla (`f2_fapar_early`, `slope`, `f4_tillage_ndti_std_early`, `log_area`, `f5_ndwi_q90_hist`, `f3_fapar_min_early`) y Tlaxcala (`s2_senescence`, `f3_damage_floor_early`, `f3_srndi_min_sepoct`, `landsat_vi6t_middle_diff_local1km`), el error en `estratificado-5` baja de `0.5056 t/ha` (`R08`) a **`0.4935 t/ha` ($R^2 = 0.6613$)** y en los 30 sorteos 70/30 baja de `0.4936 t/ha` a **`0.4865 t/ha` ($R^2 = 0.6561$)**.
   - Por primera vez en todo el proyecto, el modelo logra **$R^2$ intra-estatal positivo dentro de Puebla (`+0.0094`, `RMSE = 0.5775 t/ha`)** en validación estratificada, reduciendo el error sobre el clúster occidental de lotes extensivos (`AGC_171` y `AGC_024`) mientras mantiene `0.3872 t/ha` ($R^2 = 0.7450$) en Hidalgo y `0.3825 t/ha` (`MAE = 0.2960 t/ha`) en Tlaxcala.

2. **Salto en extrapolación a regiones sin vecinos cercanos gracias a los 788 ciclos multianuales (`E03`) y la fisiología satelital (`E01`)**:
   - Sin añadir una sola etiqueta externa de rendimiento, la representación auto-supervisada sobre los **788 ciclos Parcela × Año (2022–2025)** (`E03`) reduce el RMSE en `principal-5` a **`0.6334 t/ha` ($R^2 = 0.4423$)** y marca un **nuevo récord histórico absoluto del proyecto en `balanceado-4` con `0.6404 t/ha` ($R^2 = 0.4299$)**.
   - A su vez, la alineación fenológica dinámica por $t_{\text{pico}}$ y los índices fisiológicos `FAPAR`/`LAI`/`SAVI`/`MSI` (`E01`) alcanzan el **récord histórico en Hidalgo dentro de `estratificado-5` con `RMSE = 0.3594 t/ha` ($R^2 = 0.7803$, `MAE = 0.2881 t/ha`)**.

3. **Propagación Transductiva por Laplaciano de Grafo (`E05`)**:
   - Al resolver el sistema lineal exacto $(\operatorname{diag}(c_{\text{vec}} + c_{\text{prior}}) + 0.65 L_{197}) f = \text{rhs}$ sobre los **197 polígonos simultáneamente**, `E05` alcanza el **menor MAE global en `estratificado-5` (`0.3507 t/ha`, `RMSE = 0.5039 t/ha`)** y aprueba las compuertas de elegibilidad en los 4 esquemas.

4. **Síntesis en el Ensamble Maestro Adaptativo Bi-Etapa (`E08`)**:
   - `E08` fusiona la rama local bi-etapa/transductiva (`E06 + R05 + E05`) con la rama espectral fisiológica-multianual (`E07`) mediante la compuerta continua de densidad de vecinos $\alpha(w_{\text{eff}})$.
   - Como resultado, **`E08` supera simultáneamente al modelo productivo previo `R08` en `estratificado-5` (`0.5026` vs `0.5056`, mejorando en los 3 estados a la vez: Puebla `0.5895`, Hidalgo `0.3922`, Tlaxcala `0.3870`), en los 30 sorteos 70/30 (`0.4917` vs `0.4936`, `MAE = 0.3510`), en `principal-5` (`0.6580` vs `0.6596`) y en `balanceado-4` (`0.6690` vs `0.6718`)**, aprobando el 100% de las compuertas de elegibilidad (`4/4` esquemas) con una cobertura conformal del **`94.9%`**.

## 2. Límites Físicos Confirmados
- Estos experimentos confirman empíricamente que las mejoras alcanzables exprimiendo aún más el dataset actual (138 etiquetas de entrenamiento) son del orden de **`0.003 a 0.012 t/ha`** (`~1.2 centésimas` en `E06` y `~0.3 centésimas` en `E08` bajo el esquema estratificado, y hasta `2.6 centésimas` con `E03` en bloques espaciales).
- Para romper la barrera de **`0.40 t/ha` de RMSE** en Puebla y Tlaxcala se requiere información extrínseca al sensor satelital: fecha exacta de siembra, variedad/fertilización, registro puntual de siniestros climáticos (granizo/helada/acame) y pesaje en báscula ajustado por humedad e impurezas.

