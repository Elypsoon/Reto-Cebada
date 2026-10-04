# E07-v3-whittaker_20_10: TabPFN-2.5 (whittaker_20_10)

Configuración fija, referencia E00-v2; mismas 138 etiquetas. Sin activación ni incorporación a E08.

| esquema | RMSE | MAE | sesgo | cambio RMSE |
| --- | --- | --- | --- | --- |
| principal-5 | 0.747715 | 0.569805 | 0.095444 | -0.008631 |
| balanceado-4 | 0.772652 | 0.589668 | 0.074234 | +0.008262 |
| rotado-45-5 | 0.665158 | 0.522753 | 0.081451 | -0.084011 |

59 consultas reproducidas en un proceso nuevo desde el contexto y desde un paquete independiente, tolerancia absoluta 1e-10.

[Cambios y contexto](changes.json). [Recursos](artifacts/resources.json). [Paquete recuperable](../../packages/recovery-E07-v3-whittaker_20_10/manifest.json).

## Resultados por estado

| esquema | estado | n | MAE | sesgo | MAE media regional |
| --- | --- | --- | --- | --- | --- |
| principal-5 | Hidalgo | 36 | 0.952459 | 0.307993 | 0.935097 |
| principal-5 | Puebla | 71 | 0.423471 | -0.110181 | 0.414921 |
| principal-5 | Tlaxcala | 31 | 0.460584 | 0.319563 | 0.500000 |
| balanceado-4 | Hidalgo | 36 | 0.997570 | 0.262882 | 0.935097 |
| balanceado-4 | Puebla | 71 | 0.440813 | -0.126927 | 0.415703 |
| balanceado-4 | Tlaxcala | 31 | 0.456901 | 0.315880 | 0.500000 |
| rotado-45-5 | Hidalgo | 36 | 0.585046 | -0.128166 | 0.881243 |
| rotado-45-5 | Puebla | 71 | 0.416603 | -0.042415 | 0.377922 |
| rotado-45-5 | Tlaxcala | 31 | 0.693529 | 0.608569 | 1.274206 |
