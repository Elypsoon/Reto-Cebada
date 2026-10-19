# Fase Experimental: Estratificación Oficial 70/30, Kriging Multiescala y Ensamble Adaptativo (`estratificacion-pyr-20261018`)

Esta fase experimental surge a partir de la incorporación y auditoría del documento oficial del jurado [`DataSet/PyR.pdf`](file:///d:/Dev/Ciencia%20de%20datos/Cebada/DataSet/PyR.pdf) (*"Documento de apoyo para integrantes del jurado — Reto AgroCebada FIRA 2026"*). El protocolo, las particiones y el catálogo de modelos (`B0` y `R00`–`R08`) están congelados en [`registry/frozen-protocol.json`](file:///d:/Dev/Ciencia%20de%20datos/Cebada/experiments/estratificacion-pyr-20261018/registry/frozen-protocol.json).

## Documentación de la Fase

* **[Auditoría de `PyR.pdf` y Geometría 70/30 (`docs/pyr-audit.md`)](file:///d:/Dev/Ciencia%20de%20datos/Cebada/experiments/estratificacion-pyr-20261018/docs/pyr-audit.md):** Síntesis de las 8 respuestas oficiales del jurado, distribución estratificada por municipio y verificación de distancias al vecino de entrenamiento más cercano (mediana $= 350.4\text{ m}$).
* **[Informe de Resultados (`docs/results.md`)](file:///d:/Dev/Ciencia%20de%20datos/Cebada/experiments/estratificacion-pyr-20261018/docs/results.md):** Tablas comparativas completas en los 4 esquemas de validación cruzada (`estratificado-5`, `principal-5`, `balanceado-4`, `rotado-45-5`), simulación de 30 sorteos estratificados 70/30 (`StratifiedShuffleSplit`), métricas desglosadas por estado y calibración conformal de intervalos al $90\,\%$.
* **[Conclusiones y Elegibilidad (`docs/conclusions.md`)](file:///d:/Dev/Ciencia%20de%20datos/Cebada/experiments/estratificacion-pyr-20261018/docs/conclusions.md):** Análisis de mecanismos ganadores (`R06`, `R07`, `R08`), cumplimiento simultáneo de compuertas en los 4 esquemas e interpretación productiva del error (Pregunta 7 de `PyR.pdf`).

## Reproducción y Verificación Local

Desde la raíz del proyecto en PowerShell (utilizando el entorno aislado `.venv` con Python `3.12.14`):

```powershell
# 1. Regenerar todos los experimentos, artefactos y registros de la fase
.\.venv\Scripts\python.exe experiments/estratificacion-pyr-20261018/scripts/execute_phase.py

# 2. Ejecutar la suite de pruebas automatizadas de la fase
.\.venv\Scripts\pytest.exe experiments/estratificacion-pyr-20261018/tests -q
```

## Estructura de Recibos y Ejecuciones

* `registry/pyr-split-audit.json`: Verificación del muestreo estratificado 70/30 y distancias euclidianas en `EPSG:32614`.
* `registry/schemes.csv`: Asignación de pliegues para las 138 parcelas en los 4 esquemas.
* `registry/summary.csv` y `registry/summary.json`: Métricas globales y por estado de todas las corridas (`B0`, `R00`–`R08`).
* `registry/holdout-70-30-simulation.json`: Resultados agregados sobre 30 particiones aleatorias estratificadas 70/30 ($59/197$).
* `registry/interval-calibration.json`: Radios conformales al $90\,\%$ escalados por estado, cobertura empírica y anchura media.
* `registry/eligibility-evaluation.json`: Verificación de compuertas de promoción ($\ge 2\,\%$ sobre `B0` y $\text{MAE}_{\text{estado}} \le 110\,\%$ de `B0`).
* `runs/<ID>/`: Contiene `run.json`, `metrics.json`, los cuatro archivos `oof-*.csv`, `predictions_59.csv` y `predictions_59_intervals.csv`.

