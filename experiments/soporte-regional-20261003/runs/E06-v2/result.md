# E06: Ruido GPR y optimización acotada

Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.

Control: E00-v2.

| ruta | esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- | --- |
| official | principal-5 | 0.757375 | 0.605847 | 0.154338 | 0.001029 |
| official | balanceado-4 | 0.735315 | 0.566803 | 0.102512 | -0.029075 |
| official | rotado-45-5 | 0.751434 | 0.593622 | 0.149900 | 0.002265 |

Cambios, selección por ajuste y modelos finales: [changes.json](changes.json).

Decisión: {'promotion_scope': 'exploratorio', 'activated': False, 'by_route': {}, 'reason': 'Elegibilidad separada de activación; conservar activa'}

Tiempo y memoria: [resources.json](artifacts/resources.json).

## Resultados por estado

| ruta | esquema | estado | n | RMSE | MAE | sesgo | MAE regional |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official | principal-5 | Hidalgo | 36 | 0.930932 | 0.836523 | 0.270568 | 0.935097 |
| official | principal-5 | Puebla | 71 | 0.623421 | 0.445310 | -0.144558 | 0.414921 |
| official | principal-5 | Tlaxcala | 31 | 0.810533 | 0.705649 | 0.703926 | 0.500000 |
| official | balanceado-4 | Hidalgo | 36 | 1.014239 | 0.908899 | 0.178412 | 0.935097 |
| official | balanceado-4 | Puebla | 71 | 0.615651 | 0.423116 | -0.071751 | 0.415703 |
| official | balanceado-4 | Tlaxcala | 31 | 0.586724 | 0.498620 | 0.413487 | 0.500000 |
| official | rotado-45-5 | Hidalgo | 36 | 0.837380 | 0.724892 | -0.036341 | 0.881243 |
| official | rotado-45-5 | Puebla | 71 | 0.591607 | 0.410963 | -0.061172 | 0.377922 |
| official | rotado-45-5 | Tlaxcala | 31 | 0.947472 | 0.859529 | 0.849603 | 1.274206 |
