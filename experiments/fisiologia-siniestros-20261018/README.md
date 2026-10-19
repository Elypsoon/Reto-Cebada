# Fase Experimental `fisiologia-siniestros-20261018`

Investigación forense de parcelas atípicas, ingeniería de variables fisiológicas/siniestros (`F1`–`F5` incluyendo auto-supervisión sobre los 788 ciclos Parcela × Año 2022–2025) y arquitecturas bi-etapa y transductivas (`E01`–`E08`) sobre el modelo adaptativo productivo `R08`.

## Estructura de la Fase
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
- **`E06` (`E06_twostage_huber_residual`)**: Alcanza **`RMSE = 0.4935 t/ha` ($R^2 = 0.6613$)** en `estratificado-5` y **`RMSE_mean = 0.4865 t/ha` ($R^2 = 0.6561$)** en 30 sorteos estratificados 70/30, rompiendo por primera vez la barrera de `0.500 t/ha` y logrando $R^2$ intra-estatal positivo en Puebla (`0.5775 t/ha`).
- **`E03` (`E03_multiannual_788_latent`)**: Alcanza **`RMSE = 0.6334 t/ha` ($R^2 = 0.4423$)** en `principal-5` y un nuevo récord absoluto del proyecto en `balanceado-4` con **`RMSE = 0.6404 t/ha` ($R^2 = 0.4299$)** usando representación auto-supervisada de los 788 ciclos 2022–2025.
- **`E01` (`E01_phenology_stress_gpr`)**: Logra el menor error histórico en Hidalgo bajo validación estratificada con **`RMSE = 0.3594 t/ha` ($R^2 = 0.7803$)** y **`0.6414 t/ha`** en `rotado-45-5`.
- **`E05` (`E05_transductive_graph_197`)**: Alcanza el menor MAE global en `estratificado-5` (**`0.3507 t/ha`**) y aprueba las compuertas de elegibilidad en los 4 esquemas.
- **`E08` (`E08_master_agro_spatial_ead`)**: Supera al control productivo `R08` simultáneamente en `estratificado-5` (**`0.5026` vs `0.5056`**, mejorando en los 3 estados a la vez), en 30 sorteos 70/30 (**`0.4917` vs `0.4936`**), en `principal-5` (**`0.6580` vs `0.6596`**) y en `balanceado-4` (**`0.6690` vs `0.6718`**), aprobando las 4 compuertas de elegibilidad (`4/4`) con cobertura conformal de **`94.9%`**.

