# E05: Ablación de sensores y conteos de adquisición

Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.

Control: E00-v2.

| ruta | esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- | --- |
| official | principal-5 | 0.733562 | 0.583391 | 0.157990 | -0.022784 |
| official | balanceado-4 | 0.769155 | 0.605830 | 0.184200 | 0.004766 |
| official | rotado-45-5 | 0.738939 | 0.582674 | 0.144866 | -0.010230 |

Cambios, selección por ajuste y modelos finales: [changes.json](changes.json).

Decisión: {'promotion_scope': 'exploratorio', 'activated': False, 'by_route': {}, 'reason': 'Elegibilidad separada de activación; conservar activa'}

Tiempo y memoria: [resources.json](artifacts/resources.json).

## Resultados por estado

| ruta | esquema | estado | n | RMSE | MAE | sesgo | MAE regional |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official | principal-5 | Hidalgo | 36 | 0.913873 | 0.813169 | 0.272568 | 0.935097 |
| official | principal-5 | Puebla | 71 | 0.600564 | 0.420933 | -0.117094 | 0.414921 |
| official | principal-5 | Tlaxcala | 31 | 0.774299 | 0.688632 | 0.654964 | 0.500000 |
| official | balanceado-4 | Hidalgo | 36 | 1.027885 | 0.917955 | 0.280273 | 0.935097 |
| official | balanceado-4 | Puebla | 71 | 0.593926 | 0.411724 | -0.069750 | 0.415703 |
| official | balanceado-4 | Tlaxcala | 31 | 0.773764 | 0.687927 | 0.654259 | 0.500000 |
| official | rotado-45-5 | Hidalgo | 36 | 0.792695 | 0.681739 | -0.096600 | 0.881243 |
| official | rotado-45-5 | Puebla | 71 | 0.589541 | 0.409857 | -0.033107 | 0.377922 |
| official | rotado-45-5 | Tlaxcala | 31 | 0.951307 | 0.863436 | 0.832895 | 1.274206 |
