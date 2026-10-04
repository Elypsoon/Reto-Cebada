# E01b: Atenuación gradual por tamaño estatal

Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.

Control: E00-v2.

| ruta | esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- | --- |
| official | principal-5 | 0.889789 | 0.721320 | 0.263987 | 0.133443 |
| official | balanceado-4 | 0.891325 | 0.716169 | 0.283496 | 0.126935 |
| official | rotado-45-5 | 0.760997 | 0.609724 | 0.137030 | 0.011828 |

Cambios, selección por ajuste y modelos finales: [changes.json](changes.json).

Decisión: {'promotion_scope': 'exploratorio', 'activated': False, 'by_route': {}, 'reason': 'Elegibilidad separada de activación; conservar activa'}

Tiempo y memoria: [resources.json](artifacts/resources.json).

## Resultados por estado

| ruta | esquema | estado | n | RMSE | MAE | sesgo | MAE regional |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official | principal-5 | Hidalgo | 36 | 0.943539 | 0.851898 | 0.234827 | 0.935097 |
| official | principal-5 | Puebla | 71 | 0.601873 | 0.431958 | -0.144061 | 0.414921 |
| official | principal-5 | Tlaxcala | 31 | 1.288768 | 1.232413 | 1.232413 | 0.500000 |
| official | balanceado-4 | Hidalgo | 36 | 0.957966 | 0.866484 | 0.220241 | 0.935097 |
| official | balanceado-4 | Puebla | 71 | 0.594917 | 0.414776 | -0.098522 | 0.415703 |
| official | balanceado-4 | Tlaxcala | 31 | 1.288529 | 1.231898 | 1.231898 | 0.500000 |
| official | rotado-45-5 | Hidalgo | 36 | 0.850728 | 0.726267 | -0.032807 | 0.881243 |
| official | rotado-45-5 | Puebla | 71 | 0.605545 | 0.441562 | -0.087979 | 0.377922 |
| official | rotado-45-5 | Tlaxcala | 31 | 0.947472 | 0.859529 | 0.849603 | 1.274206 |
