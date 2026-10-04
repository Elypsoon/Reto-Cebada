# E00: Reproducción del control regional

Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.

Control: H01-regional.

| ruta | esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- | --- |
| official | principal-5 | 0.756346 | 0.603169 | 0.159040 | 0.000000 |
| official | balanceado-4 | 0.764389 | 0.599947 | 0.180592 | 0.000000 |
| official | rotado-45-5 | 0.749169 | 0.592095 | 0.149697 | 0.000000 |
| official | intraestado-3 | 0.647705 | 0.484062 | -0.007403 | 0.000000 |
| selected | principal-5 | 0.749458 | 0.596553 | 0.158253 | 0.000000 |
| selected | balanceado-4 | 0.769436 | 0.603165 | 0.198139 | 0.000000 |
| selected | rotado-45-5 | 0.749169 | 0.592095 | 0.149697 | 0.000000 |
| selected | intraestado-3 | 0.647705 | 0.484062 | -0.007403 | 0.000000 |

Cambios, selección por ajuste y modelos finales: [changes.json](changes.json).

Decisión: {'promotion_scope': 'exploratorio', 'activated': False, 'by_route': {}, 'reason': 'Elegibilidad separada de activación; conservar activa'}

Tiempo y memoria: [resources.json](artifacts/resources.json).

## Resultados por estado

| ruta | esquema | estado | n | RMSE | MAE | sesgo | MAE regional |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official | principal-5 | Hidalgo | 36 | 0.930932 | 0.836523 | 0.270568 | 0.935097 |
| selected | principal-5 | Hidalgo | 36 | 0.911757 | 0.817058 | 0.249345 | 0.935097 |
| official | principal-5 | Puebla | 71 | 0.620987 | 0.440104 | -0.135418 | 0.414921 |
| selected | principal-5 | Puebla | 71 | 0.619178 | 0.437114 | -0.126186 | 0.414921 |
| official | principal-5 | Tlaxcala | 31 | 0.810533 | 0.705649 | 0.703926 | 0.500000 |
| selected | principal-5 | Tlaxcala | 31 | 0.810533 | 0.705649 | 0.703926 | 0.500000 |
| official | balanceado-4 | Hidalgo | 36 | 0.979127 | 0.886319 | 0.233670 | 0.935097 |
| selected | balanceado-4 | Hidalgo | 36 | 0.979127 | 0.886319 | 0.233670 | 0.935097 |
| official | balanceado-4 | Puebla | 71 | 0.602578 | 0.408912 | -0.074500 | 0.415703 |
| selected | balanceado-4 | Puebla | 71 | 0.614935 | 0.415167 | -0.040395 | 0.415703 |
| official | balanceado-4 | Tlaxcala | 31 | 0.810002 | 0.704918 | 0.703195 | 0.500000 |
| selected | balanceado-4 | Tlaxcala | 31 | 0.810002 | 0.704918 | 0.703195 | 0.500000 |
| official | rotado-45-5 | Hidalgo | 36 | 0.830638 | 0.720852 | -0.040381 | 0.881243 |
| selected | rotado-45-5 | Hidalgo | 36 | 0.830638 | 0.720852 | -0.040381 | 0.881243 |
| official | rotado-45-5 | Puebla | 71 | 0.590842 | 0.410043 | -0.059519 | 0.377922 |
| selected | rotado-45-5 | Puebla | 71 | 0.590842 | 0.410043 | -0.059519 | 0.377922 |
| official | rotado-45-5 | Tlaxcala | 31 | 0.947472 | 0.859529 | 0.849603 | 1.274206 |
| selected | rotado-45-5 | Tlaxcala | 31 | 0.947472 | 0.859529 | 0.849603 | 1.274206 |
| official | intraestado-3 | Hidalgo | 36 | 0.882148 | 0.810623 | 0.016555 | 0.822222 |
| selected | intraestado-3 | Hidalgo | 36 | 0.882148 | 0.810623 | 0.016555 | 0.822222 |
| official | intraestado-3 | Puebla | 71 | 0.594842 | 0.394213 | -0.002828 | 0.384396 |
| selected | intraestado-3 | Puebla | 71 | 0.594842 | 0.394213 | -0.002828 | 0.384396 |
| official | intraestado-3 | Tlaxcala | 31 | 0.391723 | 0.310614 | -0.045703 | 0.292051 |
| selected | intraestado-3 | Tlaxcala | 31 | 0.391723 | 0.310614 | -0.045703 | 0.292051 |
