# E03: Sustitución de Whittaker nube 20 por nube 40

Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.

Control: E00-v2.

| ruta | esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- | --- |
| official | principal-5 | 0.754529 | 0.600804 | 0.160473 | -0.001817 |
| official | balanceado-4 | 0.764656 | 0.596446 | 0.184982 | 0.000266 |
| official | rotado-45-5 | 0.726224 | 0.572100 | 0.140786 | -0.022944 |

Cambios, selección por ajuste y modelos finales: [changes.json](changes.json).

Decisión: {'promotion_scope': 'exploratorio', 'activated': False, 'by_route': {}, 'reason': 'Elegibilidad separada de activación; conservar activa'}

Tiempo y memoria: [resources.json](artifacts/resources.json).

## Resultados por estado

| ruta | esquema | estado | n | RMSE | MAE | sesgo | MAE regional |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official | principal-5 | Hidalgo | 36 | 0.921515 | 0.825520 | 0.281571 | 0.935097 |
| official | principal-5 | Puebla | 71 | 0.623264 | 0.440539 | -0.138757 | 0.414921 |
| official | principal-5 | Tlaxcala | 31 | 0.811488 | 0.706900 | 0.705178 | 0.500000 |
| official | balanceado-4 | Hidalgo | 36 | 0.979127 | 0.886319 | 0.233670 | 0.935097 |
| official | balanceado-4 | Puebla | 71 | 0.603234 | 0.402107 | -0.065967 | 0.415703 |
| official | balanceado-4 | Tlaxcala | 31 | 0.810002 | 0.704918 | 0.703195 | 0.500000 |
| official | rotado-45-5 | Hidalgo | 36 | 0.795852 | 0.691744 | -0.063689 | 0.881243 |
| official | rotado-45-5 | Puebla | 71 | 0.586504 | 0.404028 | -0.045616 | 0.377922 |
| official | rotado-45-5 | Tlaxcala | 31 | 0.907971 | 0.818097 | 0.805159 | 1.274206 |
