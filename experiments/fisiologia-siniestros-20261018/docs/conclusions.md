# Conclusiones y Decisión Arquitectónica — Fase `fisiologia-siniestros-20261018` (`E01`–`E12`)

## 1. Hallazgos Principales de los Experimentos (`E01`–`E12`)

1. **Desacoplamiento por Fuente de Origen Municipal: `Comercializadora` vs. `Productor` (`PyR` P1, P3 y P4 — `E09`)**:
   - Al separar los municipios con reportes de báscula de comercializadora (precisión a 2 decimales, baja varianza: `Almoloya` $\mu=4.52, \sigma=0.19$, `Cuautepec de Hinojosa` $\mu=4.60, \sigma=0.15$, `Tepeapulco` $\mu=4.45$, `Chignahuapan` $\mu=4.48$) de los municipios con reporte de encuesta al productor (redondeo a `0.5` o `0.1 t/ha`: `Singuilucan` $\mu=3.08$, `Emiliano Zapata` $\mu=3.50$, `Apan` $\mu=3.00$, `Calpulalpan` $\mu=3.00$, `Nanacamilpa` $\mu=2.50$), se elimina el sesgo que ocurría al encoger municipios de Hidalgo hacia una media estatal ficticia (`3.74 t/ha`).
   - Como resultado inmediato, en `E09` el error en **Hidalgo** cae de `0.3968 t/ha` (`R08`) a **`0.3329 t/ha` ($R^2 = 0.8114$)** en `estratificado-5`, alcanzando el **menor MAE global del proyecto (`0.3364 t/ha`, `RMSE = 0.4880 t/ha`)**, mientras que en `principal-5` el RMSE global cae de `0.6596 t/ha` a **`0.5128 t/ha` ($R^2 = 0.6344$)**.

2. **Contigüidad Física Borde-a-Borde de Polígonos ($d_{\text{borde}} \le 35\text{ m}$ — `E10`)**:
   - El **33.9% (`20/59`)** de los polígonos de prueba comparten lindero a $\le 10\text{ m}$ con un polígono de entrenamiento (y el **42.4% (`25/59`)** a $\le 25\text{ m}$), aun cuando los centroides de lotes extensivos distan entre `300` y `550 m`.
   - Incorporar el kernel de distancia exacta entre linderos `d_boun` ponderado por similitud agronómica reduce el RMSE en `estratificado-5` a **`0.4852 t/ha` ($R^2 = 0.6726$)** y en 30 sorteos 70/30 a **`0.4779 t/ha`** (`RMSE_median = 0.4849 t/ha`), aprobando las `4/4` compuertas de elegibilidad.

3. **Ciclo Anual Completo 2025 (`PyR` P6 — `F6`) + Clima Diario Open-Meteo 5km y Micro-Topografía (`F7` — `E11`)**:
   - Aprovechando la autorización explícita de la Pregunta 6 de `PyR.pdf`, las **30,550 escenas satelitales de Ene–Mar 2025 (barbecho/humedad invernal residual)** y **Nov–Dic 2025 (cosecha tardía/rastrojo)** aportan predictores intra-estatales superiores a cualquier ventana Abr–Oct: `g1_pl_ndvi_janmar` ($r = +0.335$ en Puebla), `g1_pl_evi_novdec` ($r = +0.406$ en Hidalgo) y `g1_pl_ndvi_harvest_drop_aug_nov` ($r = +0.325$ en Tlaxcala).
   - Al cruzar los 25 nodos diarios de 5 km de **`Open-Meteo Historical Archive API`** (corregidos por gradiente adiabático `-6.5 °C/km` y drenaje de aire frío `TPI 360m/840m`) con la fecha individual de espigamiento ($t_{\text{pico}}$), la temperatura mínima en llenado de grano (`g2_min_temp_grainfill`) alcanza **$r = -0.493$ en Hidalgo** y el corrector bi-etapa Huber-Ridge (`E11`) baja el RMSE en `estratificado-5` a **`0.4823 t/ha` ($R^2 = 0.6766$)** y en `principal-5` a **`0.5105 t/ha` ($R^2 = 0.6377$)**.

4. **Síntesis en el Ensamble Maestro Integral (`E12` — Nuevo Campeón Absoluto)**:
   - `E12` (`E12_master_regime_boundary_meteo_ead`) fusiona adaptativamente `E11` con un ensamble espectral-climático global (`GPR Matérn 2.5 + CatBoost MAE`) entrenado sobre los residuos des-sesgados por régimen ($y - \mu_{\text{reg}}$) usando las familias `F1`–`F7`.
   - **`E12` domina simultáneamente los 4 esquemas de validación cruzada y los 30 sorteos 70/30**:
     - `estratificado-5`: **`RMSE = 0.4812 t/ha`**, **`MAE = 0.3399 t/ha`**, **`R² = 0.6781`** (Puebla **`0.5747`** [$R^2 = +0.0192$], Hidalgo **`0.3330`** [$R^2 = 0.8114$], Tlaxcala **`0.3814`**).
     - Simulación 30× Holdout 70/30: **`RMSE_mean = 0.4741 t/ha`** (`RMSE_median = 0.4861 t/ha`, `MAE_mean = 0.3422 t/ha`, **`R²_mean = 0.6728`**).
     - `principal-5`: **`RMSE = 0.5104 t/ha`** ($R^2 = 0.6378$, mejora de `-0.1492 t/ha` sobre `R08`).
     - `balanceado-4`: **`RMSE = 0.5112 t/ha`** ($R^2 = 0.6366$, mejora de `-0.1606 t/ha` sobre `R08`).
     - `rotado-45-5`: **`RMSE = 0.5503 t/ha`** ($R^2 = 0.5790$, mejora de `-0.1333 t/ha` sobre `R08`).
     - Aprueba **las 4 compuertas de elegibilidad (`4/4`)** con cobertura conformal empírica de **`93.5%`** y un ancho adaptativo de **`1.558 t/ha`** (`110 kg/ha` más estrecho que `R08`).
