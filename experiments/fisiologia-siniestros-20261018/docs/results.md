# Resultados Experimentales — Fase `fisiologia-siniestros-20261018`

## 1. Desempeño en el Esquema Oficial Estratificado (`estratificado-5` y 30 Sorteos 70/30)
Bajo el esquema de muestreo aleatorio estratificado 70/30 revelado por la Pregunta 5 de `PyR.pdf`, las nuevas arquitecturas rompen por primera vez la barrera de **`0.500 t/ha` de RMSE en validación cruzada** y **`0.490 t/ha` en sorteos 70/30**:

| Corrida | Arquitectura | RMSE (`estratificado-5`) | MAE (`estratificado-5`) | $R^2$ (`estratificado-5`) | RMSE Puebla | RMSE Hidalgo | RMSE Tlaxcala | Simulación 30× Holdout 70/30 (RMSE Media / Mediana) |
| --- | --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`B0`** | Media Estatal (`regional_mean`) | `0.6053` | `0.4415` | `0.4906` | `0.5897` | `0.7731` | `0.3747` | `0.5905` / `0.5992` |
| **`R08`** | Control Productivo Previo (`AdaptiveEAD`) | `0.5056` | `0.3547` | `0.6446` | `0.5923` | `0.3968` | `0.3890` | `0.4936` / `0.5161` |
| **`E01`** | Fenología Dinámica $t_{\text{pico}}$ (`F1`) + Fisiología FAPAR/LAI/MSI (`F2`) | `0.5123` | `0.3759` | `0.6351` | `0.6101` | **`0.3594`** | `0.4071` | `0.5055` / `0.5173` |
| **`E02`** | Piso de Daño `_min` (`F3`) + Labranza NDTI/STI (`F4`) | `0.5174` | `0.3712` | `0.6278` | `0.6113` | `0.3739` | `0.4163` | `0.5076` / `0.5234` |
| **`E03`** | Latente Auto-Supervisada 788 Ciclos 2022–2025 (`F5`) | `0.5295` | `0.3829` | `0.6102` | `0.6281` | `0.3816` | `0.4188` | `0.5198` / `0.5299` |
| **`E04`** | Kriging Multiescala con Similitud Agronómica | `0.5025` | `0.3564` | `0.6489` | `0.5816` | `0.4163` | `0.3851` | `0.4928` / `0.5110` |
| **`E05`** | Grafo Transductivo Laplaciano sobre las 197 Parcelas | `0.5039` | **`0.3507`** | `0.6469` | `0.5852` | `0.4148` | `0.3827` | `0.4929` / `0.5095` |
| **`E06`** | **Bi-Etapa (Kriging Agronómico + Corrector Residual Huber-Ridge)** | **`0.4935`** | `0.3572` | **`0.6613`** | **`0.5775`** ($R^2 = +0.009$) | `0.3872` | **`0.3825`** | **`0.4865`** / **`0.4988`** ($R^2 = 0.6561$) |
| **`E07`** | Ensamble Espectral Fisiológico-Multianual Puro (`F1`–`F5`) | `0.5107` | `0.3634` | `0.6374` | `0.5985` | `0.4050` | `0.3876` | `0.4983` / `0.5184` |
| **`E08`** | **Ensamble Maestro Adaptativo Agronómico-Espacial Bi-Etapa** | **`0.5026`** | **`0.3546`** | **`0.6488`** | **`0.5895`** | **`0.3922`** | **`0.3870`** | **`0.4917`** / **`0.5137`** (`MAE = 0.3510`) |

---

## 2. Desempeño en los 4 Esquemas de Validación (Estratificado + 3 Bloques Espaciales)
La tabla siguiente muestra cómo las familias espectrales fisiológicas y multianuales (`E01`, `E03`) logran récords históricos en extrapolación espacial estricta (`principal-5`, `balanceado-4`, `rotado-45-5`), mientras que `E05` y `E08` aprueban simultáneamente las compuertas de elegibilidad en **los 4 esquemas**:

| Corrida | `estratificado-5` (RMSE / $R^2$) | `principal-5` (RMSE / $R^2$) | `balanceado-4` (RMSE / $R^2$) | `rotado-45-5` (RMSE / $R^2$) | Elegible en los 4 Esquemas | Cobertura Conformal 90% |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`B0`** | `0.6053` / `0.4906` | `0.7440` / `0.2304` | `0.7442` / `0.2300` | `0.9119` / `-0.1563` | N/A | N/A |
| **`R08` (Control)** | `0.5056` / `0.6446` | `0.6596` / `0.3951` | `0.6718` / `0.3725` | `0.6836` / `0.3504` | **Sí (`4/4`)** | `93.5%` (`1.668 t/ha`) |
| **`E01` (F1+F2)** | `0.5123` / `0.6351` | `0.6381` / `0.4338` | `0.6442` / `0.4229` | **`0.6414`** / **`0.4280`** | No (`2/4`) | `94.2%` (`1.700 t/ha`) |
| **`E02` (F3+F4)** | `0.5174` / `0.6278` | `0.6864` / `0.3450` | `0.6955` / `0.3274` | `0.6518` / `0.4093` | No (`3/4`) | `93.5%` (`1.711 t/ha`) |
| **`E03` (F5 788-ciclos)** | `0.5295` / `0.6102` | **`0.6334`** / **`0.4423`** | **`0.6404`** / **`0.4299`** | `0.6491` / `0.4141` | No (`3/4`) | `92.8%` (`1.775 t/ha`) |
| **`E04` (Kriging Agro)** | `0.5025` / `0.6489` | `0.7420` / `0.2345` | `0.7428` / `0.2329` | `0.8627` / `-0.0347` | No (`2/4`) | `92.8%` (`1.644 t/ha`) |
| **`E05` (Grafo 197)** | `0.5039` / `0.6469` | `0.6828` / `0.3518` | `0.6930` / `0.3323` | `0.7182` / `0.2829` | **Sí (`4/4`)** | `93.5%` (`1.690 t/ha`) |
| **`E06` (Bi-Etapa Huber)** | **`0.4935`** / **`0.6613`** | `0.7383` / `0.2420` | `0.7393` / `0.2400` | `0.8556` / `-0.0178` | Sí en Estratificado | `94.2%` (**`1.632 t/ha`**) |
| **`E07` (Espectral Agro)** | `0.5107` / `0.6374` | `0.6590` / `0.3962` | `0.6706` / `0.3748` | `0.6841` / `0.3493` | **Sí (`4/4`)** | `94.2%` (`1.737 t/ha`) |
| **`E08` (Maestro EAD)** | **`0.5026`** / **`0.6488`** | **`0.6580`** / **`0.3979`** | **`0.6690`** / **`0.3777`** | `0.6849` / `0.3479` | **Sí (`4/4`)** | **`94.9%`** (`1.673 t/ha`) |

