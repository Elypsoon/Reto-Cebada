# Fase Experimental `fisiologia-siniestros-20261018`

Investigación forense de parcelas atípicas, ingeniería de variables fisiológicas/siniestros (`F1`–`F5`), hallazgos estructurales adicionales de `PyR.pdf` (`F6`: ciclo 2025 completo Ene–Dic de Pregunta 6; jerarquía `Comercializadora` vs. `Productor` de Preguntas 1, 3 y 4; contigüidad física borde-a-borde de polígonos) e integración de datos externos en línea de alta resolución física (`F7`: clima diario 2025 y humedad radicular de `Open-Meteo Archive API` sobre 25 nodos de 5 km + micro-topografía `TPI`), evaluados mediante las arquitecturas `E01`–`E12` frente a `B0` y `R08`.

## Estructura de la Fase
- **Datos externos en caché**:
  - [`../../data/external/open_meteo_daily_2025_nodes.json`](../../data/external/open_meteo_daily_2025_nodes.json) (25 nodos únicos de 5 km × 365 días de clima diario 2025 y humedad de suelo radicular 7–28 cm)
  - [`../../data/external/micro_topography_197.json`](../../data/external/micro_topography_197.json) (Índice de Posición Topográfica `TPI` a 360 m, 840 m y 1,800 m, concavidad Laplaciana y drenaje de aire frío para los 197 polígonos)
- **Código fuente**:
  - [`src/fisiologia_siniestros/common.py`](src/fisiologia_siniestros/common.py)
  - [`src/fisiologia_siniestros/features.py`](src/fisiologia_siniestros/features.py)
  - [`src/fisiologia_siniestros/modeling.py`](src/fisiologia_siniestros/modeling.py)
  - [`scripts/execute_phase.py`](scripts/execute_phase.py)
- **Documentación**:
  - [`docs/forensic-outliers-and-features.md`](docs/forensic-outliers-and-features.md)
  - [`docs/results.md`](docs/results.md)
  - [`docs/conclusions.md`](docs/conclusions.md)
- **Registro y Auditorías**:
  - [`registry/frozen-protocol.json`](registry/frozen-protocol.json)
  - [`registry/forensic-outlier-audit.json`](registry/forensic-outlier-audit.json)
  - [`registry/feature-importance.csv`](registry/feature-importance.csv)
  - [`registry/feature-importance.json`](registry/feature-importance.json)
  - [`registry/summary.csv`](registry/summary.csv)
  - [`registry/summary.json`](registry/summary.json)
  - [`registry/holdout-70-30-simulation.json`](registry/holdout-70-30-simulation.json)
  - [`registry/paired-comparisons.json`](registry/paired-comparisons.json)
  - [`registry/interval-calibration.json`](registry/interval-calibration.json)
  - [`registry/eligibility-evaluation.json`](registry/eligibility-evaluation.json)
- **Pruebas automatizadas**:
  - [`tests/test_fisiologia_siniestros.py`](tests/test_fisiologia_siniestros.py)

## Resumen de Resultados Principales
- **`E12` (`E12_master_regime_boundary_meteo_ead`) — Nuevo Campeón Integral del Proyecto**:
  - **`estratificado-5`**: **`RMSE = 0.4812 t/ha`**, **`MAE = 0.3399 t/ha`**, **`R² = 0.6781`** (Puebla `0.5747` [$R^2 = +0.0192$], Hidalgo **`0.3330`** [$R^2 = 0.8114$], Tlaxcala **`0.3814`**).
  - **Simulación 30× Holdout 70/30**: **`RMSE_mean = 0.4741 t/ha`** (`RMSE_median = 0.4861 t/ha`, `MAE_mean = 0.3422 t/ha`, **`R²_mean = 0.6728`**), reduciendo el error en **`-0.0195 t/ha`** respecto a `R08` (`0.4936 t/ha`).
  - **Extrapolación espacial estricta**: **`RMSE = 0.5104 t/ha`** ($R^2 = 0.6378$) en `principal-5`, **`0.5112 t/ha`** ($R^2 = 0.6366$) en `balanceado-4` y **`0.5503 t/ha`** ($R^2 = 0.5790$) en `rotado-45-5`, aprobando **las 4 compuertas de elegibilidad (`4/4`)** con cobertura conformal de **`93.5%`** y ancho adaptativo de **`1.558 t/ha`**.
- **`E11` (`E11_fullyear2025_openmeteo_huber`)**: Alcanza **`RMSE = 0.4823 t/ha` ($R^2 = 0.6766$)** en `estratificado-5`, **`0.5105 t/ha`** en `principal-5` y **`RMSE_mean = 0.4759 t/ha`** en 30 sorteos 70/30 al incorporar las 30,550 escenas de Ene–Mar y Nov–Dic 2025 (`PyR` P6) más el clima diario de `Open-Meteo` en ventanas fenológicas críticas.
- **`E10` (`E10_polygon_boundary_adjacency`)**: Reduce el RMSE de `estratificado-5` a **`0.4852 t/ha`** (`MAE = 0.3381 t/ha`, $R^2 = 0.6726$) y aprueba `4/4` esquemas al ponderar la contigüidad exacta entre linderos de polígonos ($d_{\text{borde}} \le 35\text{ m}$).
- **`E09` (`E09_source_regime_kriging`)**: Al separar los municipios de `Comercializadora` (precisión de 2 decimales, baja varianza) de los de `Productor` (redondeo a 0.5/0.1 t/ha) conforme a las Preguntas 1, 3 y 4 de `PyR.pdf`, reduce el error de Hidalgo de `0.3968` a **`0.3329 t/ha` ($R^2 = 0.8114$)** y logra el **menor MAE global en `estratificado-5` (`0.3364 t/ha`)**, aprobando `4/4` esquemas.
- **`E06` (`E06_twostage_huber_residual`) y `E08` (`E08_master_agro_spatial_ead`)**: Rompen la barrera de `0.500 t/ha` con variables fisiológicas internas `F1`–`F5` (`0.4935 t/ha` y `0.5026 t/ha`).
