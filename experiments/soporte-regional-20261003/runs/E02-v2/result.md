# E02: Centrado de predictores y selección dentro del estado

Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.

Control: E00-v2.

| ruta | esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- | --- |
| official | principal-5 | 0.756346 | 0.603169 | 0.159040 | 0.000000 |
| official | balanceado-4 | 0.765028 | 0.599796 | 0.189262 | 0.000638 |
| official | rotado-45-5 | 0.749169 | 0.592095 | 0.149697 | 0.000000 |

Cambios, selección por ajuste y modelos finales: [changes.json](changes.json).

Decisión: {'promotion_scope': 'exploratorio', 'activated': False, 'by_route': {}, 'reason': 'Elegibilidad separada de activación; conservar activa'}

Tiempo y memoria: [resources.json](artifacts/resources.json).

## Resultados por estado

| ruta | esquema | estado | n | RMSE | MAE | sesgo | MAE regional |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official | principal-5 | Hidalgo | 36 | 0.930932 | 0.836523 | 0.270568 | 0.935097 |
| official | principal-5 | Puebla | 71 | 0.620987 | 0.440104 | -0.135418 | 0.414921 |
| official | principal-5 | Tlaxcala | 31 | 0.810533 | 0.705649 | 0.703926 | 0.500000 |
| official | balanceado-4 | Hidalgo | 36 | 0.972758 | 0.870181 | 0.319252 | 0.935097 |
| official | balanceado-4 | Puebla | 71 | 0.608169 | 0.415642 | -0.102201 | 0.415703 |
| official | balanceado-4 | Tlaxcala | 31 | 0.812024 | 0.707571 | 0.705848 | 0.500000 |
| official | rotado-45-5 | Hidalgo | 36 | 0.830638 | 0.720852 | -0.040381 | 0.881243 |
| official | rotado-45-5 | Puebla | 71 | 0.590842 | 0.410043 | -0.059519 | 0.377922 |
| official | rotado-45-5 | Tlaxcala | 31 | 0.947472 | 0.859529 | 0.849603 | 1.274206 |
