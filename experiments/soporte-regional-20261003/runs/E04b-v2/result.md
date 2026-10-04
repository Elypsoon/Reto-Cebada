# E04b: AUC respaldada EVI/MSAVI

Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.

Control: E04a-v2.

| ruta | esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- | --- |
| official | principal-5 | 0.756386 | 0.602347 | 0.161938 | 0.000000 |
| official | balanceado-4 | 0.763580 | 0.598653 | 0.185710 | 0.000000 |
| official | rotado-45-5 | 0.751552 | 0.592156 | 0.148767 | 0.002682 |

Cambios, selección por ajuste y modelos finales: [changes.json](changes.json).

Decisión: {'promotion_scope': 'exploratorio', 'activated': False, 'by_route': {}, 'reason': 'Elegibilidad separada de activación; conservar activa'}

Tiempo y memoria: [resources.json](artifacts/resources.json).

## Resultados por estado

| ruta | esquema | estado | n | RMSE | MAE | sesgo | MAE regional |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official | principal-5 | Hidalgo | 36 | 0.936296 | 0.840919 | 0.266172 | 0.935097 |
| official | principal-5 | Puebla | 71 | 0.616423 | 0.435721 | -0.128112 | 0.414921 |
| official | principal-5 | Tlaxcala | 31 | 0.811505 | 0.706922 | 0.705199 | 0.500000 |
| official | balanceado-4 | Hidalgo | 36 | 0.979127 | 0.886319 | 0.233670 | 0.935097 |
| official | balanceado-4 | Puebla | 71 | 0.600579 | 0.406397 | -0.064552 | 0.415703 |
| official | balanceado-4 | Tlaxcala | 31 | 0.810002 | 0.704918 | 0.703195 | 0.500000 |
| official | rotado-45-5 | Hidalgo | 36 | 0.835055 | 0.724283 | -0.041668 | 0.881243 |
| official | rotado-45-5 | Puebla | 71 | 0.593562 | 0.408421 | -0.060674 | 0.377922 |
| official | rotado-45-5 | Tlaxcala | 31 | 0.947472 | 0.859529 | 0.849603 | 1.274206 |
