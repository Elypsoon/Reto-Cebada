# E01a: Atenuación dura con menos de diez etiquetas estatales

Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.

Control: E00-v2.

| ruta | esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- | --- |
| official | principal-5 | 0.683994 | 0.539156 | -0.128960 | -0.072352 |
| official | balanceado-4 | 0.757338 | 0.581546 | -0.072409 | -0.007051 |
| official | rotado-45-5 | 0.748971 | 0.597005 | 0.152267 | -0.000198 |

Cambios, selección por ajuste y modelos finales: [changes.json](changes.json).

Decisión: {'promotion_scope': 'exploratorio', 'activated': False, 'by_route': {}, 'reason': 'Elegibilidad separada de activación; conservar activa'}

Tiempo y memoria: [resources.json](artifacts/resources.json).

## Resultados por estado

| ruta | esquema | estado | n | RMSE | MAE | sesgo | MAE regional |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official | principal-5 | Hidalgo | 36 | 0.854587 | 0.751524 | 0.197177 | 0.935097 |
| official | principal-5 | Puebla | 71 | 0.609488 | 0.446742 | -0.148237 | 0.414921 |
| official | principal-5 | Tlaxcala | 31 | 0.619490 | 0.504191 | -0.463551 | 0.500000 |
| official | balanceado-4 | Hidalgo | 36 | 1.059588 | 0.968806 | 0.215974 | 0.935097 |
| official | balanceado-4 | Puebla | 71 | 0.616163 | 0.420414 | -0.046400 | 0.415703 |
| official | balanceado-4 | Tlaxcala | 31 | 0.616380 | 0.500869 | -0.466873 | 0.500000 |
| official | rotado-45-5 | Hidalgo | 36 | 0.817321 | 0.693735 | -0.003453 | 0.881243 |
| official | rotado-45-5 | Puebla | 71 | 0.599704 | 0.433336 | -0.073248 | 0.377922 |
| official | rotado-45-5 | Tlaxcala | 31 | 0.947472 | 0.859529 | 0.849603 | 1.274206 |
