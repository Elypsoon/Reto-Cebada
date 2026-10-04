# E08: Combinación predeclarada E01a+E02+E04a

Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.

Control: E00-v2.

| ruta | esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- | --- |
| official | principal-5 | 0.688201 | 0.541857 | -0.131352 | -0.068145 |
| official | balanceado-4 | 0.760462 | 0.578175 | -0.064957 | -0.003927 |
| official | rotado-45-5 | 0.748305 | 0.590162 | 0.157431 | -0.000863 |
| official | intraestado-3 | 0.652265 | 0.477867 | 0.000482 | 0.004560 |
| selected | principal-5 | 0.687622 | 0.541033 | -0.126662 | -0.061836 |
| selected | balanceado-4 | 0.761172 | 0.580065 | -0.063509 | -0.008264 |
| selected | rotado-45-5 | 0.748305 | 0.590162 | 0.157431 | -0.000863 |
| selected | intraestado-3 | 0.652265 | 0.477867 | 0.000482 | 0.004560 |

Cambios, selección por ajuste y modelos finales: [changes.json](changes.json).

Decisión: {'promotion_scope': 'E08', 'activated': False, 'by_route': {'official': {'promote': False, 'checks': {'three_valid_schemes': True, 'principal_gain_2pct': True, 'at_least_two_gains': True, 'mean_ratio_098': True, 'none_above_105': True, 'regional_protection': False, 'verification': True}, 'ratios': {'principal-5': 0.9250310412448863, 'balanceado-4': 1.0219118409948236, 'rotado-45-5': 0.8205634294032911}, 'mean_ratio': 0.9225021038810004, 'invalid': [], 'regional_failures': [{'scheme': 'rotado-45-5', 'state': 'Puebla', 'n': 71, 'selected': {'rmse': 0.6012395780706254, 'mae': 0.42426526747441046, 'r2': -0.07360141802648035}, 'official': {'rmse': 0.6012395780706254, 'mae': 0.42426526747441046, 'r2': -0.07360141802648035}, 'regional_mean': {'rmse': 0.5879313769791714, 'mae': 0.37792164303387904, 'r2': -0.02659993064948485}}], 'eligible': False, 'activated': False}, 'selected': {'promote': False, 'checks': {'three_valid_schemes': True, 'principal_gain_2pct': True, 'at_least_two_gains': True, 'mean_ratio_098': True, 'none_above_105': True, 'regional_protection': False, 'verification': True}, 'ratios': {'principal-5': 0.9242537134293746, 'balanceado-4': 1.0228660000033327, 'rotado-45-5': 0.8205634294032911}, 'mean_ratio': 0.9225610476119995, 'invalid': [], 'regional_failures': [{'scheme': 'rotado-45-5', 'state': 'Puebla', 'n': 71, 'selected': {'rmse': 0.6012395780706254, 'mae': 0.42426526747441046, 'r2': -0.07360141802648035}, 'official': {'rmse': 0.6012395780706254, 'mae': 0.42426526747441046, 'r2': -0.07360141802648035}, 'regional_mean': {'rmse': 0.5879313769791714, 'mae': 0.37792164303387904, 'r2': -0.02659993064948485}}], 'eligible': False, 'activated': False}}, 'reason': 'Elegibilidad separada de activación; conservar activa'}

Tiempo y memoria: [resources.json](artifacts/resources.json).

## Resultados por estado

| ruta | esquema | estado | n | RMSE | MAE | sesgo | MAE regional |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official | principal-5 | Hidalgo | 36 | 0.867614 | 0.763773 | 0.184928 | 0.935097 |
| selected | principal-5 | Hidalgo | 36 | 0.867614 | 0.763773 | 0.184928 | 0.935097 |
| official | principal-5 | Puebla | 71 | 0.609225 | 0.445654 | -0.146804 | 0.414921 |
| selected | principal-5 | Puebla | 71 | 0.607954 | 0.444052 | -0.137689 | 0.414921 |
| official | principal-5 | Tlaxcala | 31 | 0.619793 | 0.504487 | -0.463255 | 0.500000 |
| selected | principal-5 | Tlaxcala | 31 | 0.619793 | 0.504487 | -0.463255 | 0.500000 |
| official | balanceado-4 | Hidalgo | 36 | 1.076771 | 0.971789 | 0.267102 | 0.935097 |
| selected | balanceado-4 | Hidalgo | 36 | 1.076771 | 0.971789 | 0.267102 | 0.935097 |
| official | balanceado-4 | Puebla | 71 | 0.608667 | 0.412557 | -0.057634 | 0.415703 |
| selected | balanceado-4 | Puebla | 71 | 0.610390 | 0.416230 | -0.054819 | 0.415703 |
| official | balanceado-4 | Tlaxcala | 31 | 0.615980 | 0.500394 | -0.467348 | 0.500000 |
| selected | balanceado-4 | Tlaxcala | 31 | 0.615980 | 0.500394 | -0.467348 | 0.500000 |
| official | rotado-45-5 | Hidalgo | 36 | 0.812747 | 0.685393 | 0.004924 | 0.881243 |
| selected | rotado-45-5 | Hidalgo | 36 | 0.812747 | 0.685393 | 0.004924 | 0.881243 |
| official | rotado-45-5 | Puebla | 71 | 0.601240 | 0.424265 | -0.067457 | 0.377922 |
| selected | rotado-45-5 | Puebla | 71 | 0.601240 | 0.424265 | -0.067457 | 0.377922 |
| official | rotado-45-5 | Tlaxcala | 31 | 0.947472 | 0.859529 | 0.849603 | 1.274206 |
| selected | rotado-45-5 | Tlaxcala | 31 | 0.947472 | 0.859529 | 0.849603 | 1.274206 |
| official | intraestado-3 | Hidalgo | 36 | 0.899580 | 0.822222 | -0.000000 | 0.822222 |
| selected | intraestado-3 | Hidalgo | 36 | 0.899580 | 0.822222 | -0.000000 | 0.822222 |
| official | intraestado-3 | Puebla | 71 | 0.595745 | 0.384396 | 0.001122 | 0.384396 |
| selected | intraestado-3 | Puebla | 71 | 0.595745 | 0.384396 | 0.001122 | 0.384396 |
| official | intraestado-3 | Tlaxcala | 31 | 0.375906 | 0.292051 | -0.000422 | 0.292051 |
| selected | intraestado-3 | Tlaxcala | 31 | 0.375906 | 0.292051 | -0.000422 | 0.292051 |
