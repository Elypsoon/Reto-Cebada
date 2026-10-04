# E07-v3-monthly_20_10: TabPFN-2.5 (monthly_20_10)

Configuración fija, referencia E00-v2; mismas 138 etiquetas. Sin activación ni incorporación a E08.

| esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- |
| principal-5 | 0.753740 | 0.569636 | 0.106107 | -0.002606 |
| balanceado-4 | 0.780706 | 0.591110 | 0.088676 | +0.016317 |
| rotado-45-5 | 0.663860 | 0.518503 | 0.091338 | -0.085308 |

59 consultas reproducidas en un proceso nuevo desde el contexto y desde un paquete independiente, tolerancia absoluta 1e-10.

[Cambios y contexto](changes.json). [Recursos](artifacts/resources.json). [Paquete recuperable](../../packages/recovery-E07-v3-monthly_20_10/manifest.json).

## Resultados por estado

| esquema | estado | n | MAE | sesgo | MAE media regional |
| --- | --- | --- | --- | --- | --- |
| principal-5 | Hidalgo | 36 | 0.977613 | 0.309634 | 0.935097 |
| principal-5 | Puebla | 71 | 0.407533 | -0.092524 | 0.414921 |
| principal-5 | Tlaxcala | 31 | 0.467125 | 0.324681 | 0.500000 |
| balanceado-4 | Hidalgo | 36 | 1.029514 | 0.257732 | 0.935097 |
| balanceado-4 | Puebla | 71 | 0.424273 | -0.098770 | 0.415703 |
| balanceado-4 | Tlaxcala | 31 | 0.464106 | 0.321663 | 0.500000 |
| rotado-45-5 | Hidalgo | 36 | 0.572669 | -0.138728 | 0.881243 |
| rotado-45-5 | Puebla | 71 | 0.408195 | -0.029329 | 0.377922 |
| rotado-45-5 | Tlaxcala | 31 | 0.708239 | 0.634881 | 1.274206 |
