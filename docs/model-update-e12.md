# Integración del modelo E12 · 19 de octubre de 2026

Se incorporó el commit `32a6d2116e480c9388b9024faa300d1a48ee075d` de `Reto-Cebada`, sin reentrenamiento. El modelo activo es **Ensamble Maestro Integral E12** (`E12_master_regime_boundary_meteo_ead`).

## Resultados que muestra la aplicación

Métricas recalculadas desde las 138 predicciones fuera de pliegue de `artifacts/oof.csv`, bajo cinco grupos estratificados por estado:

| Métrica | E12 | R08 anterior |
| --- | ---: | ---: |
| MAE (t/ha) | 0.339942 | 0.354711 |
| RMSE (t/ha) | 0.481150 | 0.505550 |
| R² | 0.678118 | 0.644644 |
| Cobertura empírica del intervalo nominal 90% | 93.48% | 93.48% |
| Amplitud media del intervalo (t/ha) | 1.558414 | 1.668215 |

Las cifras comunicadas inicialmente (0.35 y 0.49 t/ha) no son las métricas finales guardadas en ese commit. La interfaz muestra **0.340 MAE** y **0.481 RMSE**, sin reemplazarlas por valores manuales.

| Estado | Parcelas observadas | MAE (t/ha) | RMSE (t/ha) | R² |
| --- | ---: | ---: | ---: | ---: |
| Hidalgo | 36 | 0.241220 | 0.332955 | 0.811435 |
| Puebla | 71 | 0.410604 | 0.574672 | 0.019184 |
| Tlaxcala | 31 | 0.292747 | 0.381392 | -0.063020 |

## Alcance y procedencia

E12 integra régimen municipal de reporte, vecindad entre linderos, fisiología, señales del ciclo completo 2025, clima diario de Open-Meteo y microtopografía con GPR/CatBoost. Es una estimación retrospectiva; no debe presentarse como un pronóstico disponible en octubre. El contrato heredado conserva `cutoff=2025-10-31` de la canalización base; `presentation.feature_period_end=2025-12-31` documenta el periodo de señales de E12. Las curvas NDVI que muestra la interfaz siguen correspondiendo a abril–octubre y se identifican como contexto.

Los campos heredados `final_selection`, `folds`, `regional_stress`, tiempos y memoria de `validation.json` describen el procedimiento base; no se atribuyen a E12. Para E12, consultar los resultados y protocolos de `experiments/fisiologia-siniestros-20261018/`. Los resultados estratificados acompañaron el desarrollo y no son un test independiente de selección. Las 59 etiquetas ocultas no permiten medir un error de prueba local.

El artefacto contiene estimaciones precalculadas para las 197 parcelas oficiales. No contiene contribuciones por variable que reproduzcan E12; la interfaz conserva esa limitación.

## Integración y reproducción

`artifacts/upstream-cloud-compatibility.json` registra el commit, hashes importados, adaptación de contratos y comparación exacta de las 197 predicciones e intervalos con el Predictor del proyecto original. El modelo «Solo datos del reto» conserva exactamente sus predicciones e intervalos anteriores. Los respaldos locales están en `artifacts/versions/upstream-sync-32a6d21/`.

Se actualizaron los artefactos activos, registros y código de la fase experimental, nuevas fuentes externas, fichas de ambas interfaces, métricas regionales, puntos de validación e intervalos. React obtiene identidad, alcance y fuentes del contrato; no conserva el nombre R08 en sus componentes. Las descargas incluyen las 59 estimaciones E12.

Para regenerar la interfaz desde los artefactos compatibles:

```powershell
.venv/Scripts/python.exe scripts/export_react_dashboard.py
npm run dashboard:build
npm run dashboard
```

La integración inicial se conserva en `scripts/sync_e12_model.py`; requiere el respaldo y la captura independiente del Predictor de origen para verificar igualdad exacta. El exportador comprueba MAE, RMSE, R², métricas por estado, hashes, IDs, predicciones e intervalos antes de completar la exportación.

## Verificación de la integración

- 37 pruebas aprobadas: 33 del proyecto y cuatro de la fase fisiológica E01–E12. Incluyen reproducción de ambos modelos, igualdad de descargas, valores exportados al frontend e interacción de Streamlit.
- Compilación TypeScript/Vite aprobada con las 16 familias de videos disponibles.
- Revisión en navegador de métricas, ficha AGC_071, intervalos, explicación y procedencia; sin errores de consola. Sin desbordamiento horizontal a 375 px ni en orientación horizontal.
- La copia original `Reto-Cebada` conserva su estado de Git limpio.

En este entorno de Windows, las pruebas de Streamlit requieren conexiones locales para su bucle de eventos; se ejecutaron con acceso a localhost. Las pruebas que crean archivos temporales utilizaron una carpeta dentro del proyecto.
