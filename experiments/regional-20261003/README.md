# Experimento regional - 2026-10-03

Fase implementada del cambio `seleccion-robusta-con-correccion-regional`. La política y los tres esquemas se congelaron antes del entrenamiento. No se amplió la grilla tras observar resultados.

| Esquema | RMSE selección (t/ha) | RMSE regional (t/ha) |
| --- | --- | --- |
| Principal, 5 bloques vigentes | 0.749458 | 0.743976 |
| Balanceado, 4 bloques | 0.769436 | 0.744156 |
| Rotado 45 grados, 5 bloques | 0.749169 | 0.911941 |

**Promoción rechazada.** El principal no mejora 2% frente a la media regional; solo un esquema cumple esa ganancia y Tlaxcala supera el deterioro permitido de MAE en principal/balanceado. La ruta oficial tampoco cumple. La versión vigente con RMSE 0.764053 permanece intacta y recuperable; este experimento no cambia la aplicación activa.

Se implementaron 26 candidatos, corrección regional compartida, cuatro promedios uniformes y seis ablaciones externas pareadas. La selección final experimental es GPR directo, representación mensual, longitud 5 y NASA; DGSIAP queda excluida. Esos componentes finales fueron elegidos internamente sobre 138 etiquetas, no por la comparación externa. Hay 59 predicciones reproducibles por cada ruta, oficial y enriquecida.

42 pruebas experimentales y 25 de la versión recuperable pasaron. Se revisaron diez casos difíciles de Hidalgo y 176 hashes de originales; no se demostraron discrepancias ni se retiraron etiquetas. La cobertura global de intervalos es 87.7%, Hidalgo 69.4%; no existe garantía regional. Las tres evaluaciones usan las mismas etiquetas y siguen siendo resultados de desarrollo, sin validación temporal ni evaluación oficial.

## Consultar y reproducir

Desde PowerShell en el proyecto principal:

```powershell
./experiments/regional-20261003/run.ps1 verify
./experiments/regional-20261003/run.ps1 app
./experiments/regional-20261003/run.ps1 robust -ArtifactDirectory artifacts-reproduction
```

El lanzador usa el intérprete instalado del proyecto y fija el código de esta copia. El destino alternativo permanece dentro del experimento. La preparación de variables ya está guardada; no hay que descargar fuentes ni instalar el experimento sobre la versión vigente.

`docs/phase-results.md` muestra cifras y razones de decisión. `artifacts/phase-summary.csv`, `promotion.json`, `promotion-official.json` y `phase-comparison.json` conservan la comparación verificable. `artifacts/oof-*.csv` contiene las 138 predicciones por esquema; `validation-*.json` guarda decisiones y estadísticas internas. Las sensibilidades leave-one-state-out y buffer de 1 km se encuentran en `stress.json`, incluidos dos escenarios inviables. `future-data-priorities.json` registra datos futuros con disponibilidad pendiente.

Los informes experimentales están en `docs/technical-report.md` y `output/pdf/`. Los anexos contienen las 59 estimaciones. Los documentos vigentes permanecen en el proyecto principal y en `artifacts/versions/selection-current-20261003`. La receta de recuperación íntegra es `docs/restore-version.md`.
