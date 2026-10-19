# Resultados Experimentales: Fase `estratificacion-pyr-20261018`

**Fecha de ejecución:** 18 de octubre de 2026  
**Semilla fija:** `2026` | **Corte temporal:** `2025-10-31`  
**Población:** $197$ parcelas ($138$ entrenamiento / $59$ prueba ciega)  
**Registros de respaldo:** [`registry/summary.csv`](file:///d:/Dev/Ciencia%20de%20datos/Cebada/experiments/estratificacion-pyr-20261018/registry/summary.csv), [`registry/holdout-70-30-simulation.json`](file:///d:/Dev/Ciencia%20de%20datos/Cebada/experiments/estratificacion-pyr-20261018/registry/holdout-70-30-simulation.json), [`registry/eligibility-evaluation.json`](file:///d:/Dev/Ciencia%20de%20datos/Cebada/experiments/estratificacion-pyr-20261018/registry/eligibility-evaluation.json)

---

## 1. Catálogo de Corridas Evaluadas (`B0` y `R00`–`R08`)

| ID | Nombre Técnico | Familia / Mecanismo | Hipótesis derivada de `PyR.pdf` |
| :---: | :--- | :--- | :--- |
| **`B0`** | `B0_regional_mean` | Línea Base Estatal | Promedio simple del estado dentro del subconjunto de entrenamiento. |
| **`R00`** | `R00_control_gpr` | Control `GPR` (`geo=False`) | Modelo activo (`whittaker_40_10` + `nasa`, `GPR` Matérn 2.5 top-10) sin el ruido del selector interno de 81 candidatos. |
| **`R01`** | `R01_gpr_geo` | `GPR` + Coordenadas UTM | Incorpora explícitamente `location_x, location_y` (UTM 14N) para capturar gradientes locales intra-municipales (P5). |
| **`R02`** | `R02_catboost_geo` | `CatBoost` + Coordenadas UTM | Árboles potenciados (`depth=3`, `l2_leaf_reg=10`, $k=20$) con contexto geográfico explícito. |
| **`R03`** | `R03_biweekly_contrast` | Quincenal 14d + Contraste $1\text{ km}$ + Histórico | Reconstrucción espectral quincenal de 14 días (recupera $161/197$ parcelas en junio–julio), anomalías 2025 vs 2022–2024 y contraste espectral vecinal en radio de $1\text{ km}$. |
| **`R04`** | `R04_extratrees_geo` | `ExtraTrees` Regularizado | Ensamble de 300 árboles extremadamente aleatorizados (`max_depth=6`, `min_samples_leaf=3`) con coordenadas UTM. |
| **`R05`** | `R05_spatial_kriging` | Kriging Espacial Multiescala | Interpolación gaussiana multiescala ($\ell_1 = 600\text{ m}$, $\ell_2 = 1,500\text{ m}$) dentro del mismo estado con encogimiento hacia la media municipal/estatal (aprovecha mediana de $350.4\text{ m}$ entre train y test, P5). |
| **`R06`** | `R06_spectral_geo_ensemble` | Ensamble Espectral + Shrinkage EB | Combinación convexa (`R01` + `R02` + `R03` + `R04` + `GPR` escalado) con **encogimiento empírico de Bayes por varianza estatal** ($\gamma_s$) para mitigar la cuantización de Tlaxcala (P3). |
| **`R07`** | `R07_hybrid_kriging_spectral` | Híbrido Kriging-Espectral 50/50 + EB | Fusión 50/50 entre el Prior Espacial Multiescala (`R05`) y el Ensamble Espectral (`R06`) con amortiguamiento de varianza estatal (óptimo para muestreo estratificado 70/30). |
| **`R08`** | `R08_adaptive_ead` | **Ensamble Adaptativo por Distancia (EAD)** | Pondera dinámicamente entre `R05` y la rama espectral (`R01` + `R03` + `R06`) según la densidad de vecinos de entrenamiento a $<600\text{ m}$, más encogimiento empírico de Bayes por estado. |

---

## 2. Resultados en el Esquema Oficial Estratificado (`estratificado-5` y 30 Sorteos 70/30)

| ID | Modelo | RMSE `estratificado-5` ($\text{t/ha}$) ↓ | MAE `estratificado-5` ($\text{t/ha}$) ↓ | $R^2$ `estratificado-5` ↑ | RMSE 30 Sorteos 70/30 ($\mu \pm \sigma$) ↓ | MAE 30 Sorteos 70/30 ↓ | $R^2$ 30 Sorteos 70/30 ↑ |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`R05`** | `R05_spatial_kriging` | **$0.5021$** | $0.3589$ | **$0.6495$** | $0.4937 \pm 0.0523$ | $0.3604$ | $0.6464$ |
| **`R07`** | `R07_hybrid_kriging_spectral` | **$0.5042$** | **$0.3535$** | **$0.6465$** | **$0.4920 \pm 0.0565$** | $0.3521$ | **$0.6505$** |
| **`R08`** | `R08_adaptive_ead` | **$0.5056$** | **$0.3547$** | **$0.6446$** | **$0.4936 \pm 0.0586$** | **$0.3516$** | **$0.6481$** |
| **`R06`** | `R06_spectral_geo_ensemble` | **$0.5114$** | $0.3641$ | $0.6363$ | $0.4976 \pm 0.0613$ | $0.3565$ | $0.6427$ |
| **`R04`** | `R04_extratrees_geo` | $0.5152$ | $0.3741$ | $0.6309$ | $0.5027 \pm 0.0676$ | $0.3671$ | $0.6333$ |
| **`R02`** | `R02_catboost_geo` | $0.5206$ | $0.3802$ | $0.6232$ | $0.5096 \pm 0.0670$ | $0.3720$ | $0.6258$ |
| **`R00`** | `R00_control_gpr` | $0.5222$ | $0.3812$ | $0.6208$ | $0.5198 \pm 0.0662$ | $0.3821$ | $0.6077$ |
| **`R03`** | `R03_biweekly_contrast` | $0.5254$ | $0.3827$ | $0.6161$ | $0.5119 \pm 0.0637$ | $0.3731$ | $0.6210$ |
| **`R01`** | `R01_gpr_geo` | $0.5278$ | $0.3837$ | $0.6127$ | $0.5165 \pm 0.0663$ | $0.3796$ | $0.6125$ |
| *Ref.* | *Selector Anidado Vigente (`selected`)* | *$0.6010$* | *$0.4322$* | *$0.4979$* | — | — | — |
| **`B0`** | `B0_regional_mean` | $0.6053$ | $0.4415$ | $0.4906$ | $0.5905 \pm 0.0501$ | $0.4419$ | $0.4989$ |

---

## 3. Desempeño por Estado bajo `estratificado-5` ($N = 138$)

| ID | Puebla RMSE / MAE ($n=71$) | **Hidalgo RMSE / MAE ($n=36$)** | **Hidalgo $R^2$** | **Tlaxcala RMSE / MAE ($n=31$)** | Cumple Compuerta MAE $\le 110\,\%$ `B0` |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **`B0`** (`regional_mean`) | $0.5897\text{ / }0.4278$ | $0.7731\text{ / }0.6311$ | $-0.0167$ | $0.3747\text{ / }0.3001$ | Referencia ($100\,\%$) |
| *Activo (`selected` espacial)* | *$0.6068\text{ / }0.4409$* | *$1.1014\text{ / }0.9827$* | *$-1.0633$* | *$0.5889\text{ / }0.4873$* | No |
| **`R00`** (`control_gpr`) | $0.6108\text{ / }0.4410$ | $0.3754\text{ / }0.2869$ | **$+0.7603$** | $0.4428\text{ / }0.3536$ | No (Tlaxcala $>0.330$) |
| **`R06`** (`spectral_geo_ensemble`) | $0.5966\text{ / }0.4241$ | $0.3910\text{ / }0.2991$ | **$+0.7399$** | **$0.3824\text{ / }0.3023$** | **SÍ (en los 3 estados)** |
| **`R07`** (`hybrid_kriging_spectral`) | **$0.5877\text{ / }0.4143$** | $0.3849\text{ / }0.2899$ | **$+0.7480$** | **$0.3775\text{ / }0.2881$** | **SÍ (mejora los 3 estados vs `B0`)** |
| **`R08`** (`adaptive_ead`) | $0.5924\text{ / }0.4184$ | **$0.3765\text{ / }0.2849$** | **$+0.7589$** | **$0.3812\text{ / }0.2900$** | **SÍ (mejora los 3 estados vs `B0`)** |

---

## 4. Robustez Multiesquema: Comparación en los 4 Esquemas de Validación

| ID | `estratificado-5` (RMSE / $R^2$) | `principal-5` (RMSE / $R^2$) | `balanceado-4` (RMSE / $R^2$) | `rotado-45-5` (RMSE / $R^2$) | ¿Elegible en los 4 Esquemas? |
| :---: | :---: | :---: | :---: | :---: | :---: |
| *Activo (`selected`)* | $0.6010\text{ / }0.4979$ | $0.7641\text{ / }0.1883$ | $0.7510\text{ / }0.2159$ | $0.7609\text{ / }0.1951$ | No |
| **`B0`** (`regional_mean`) | $0.6053\text{ / }0.4906$ | $0.7440\text{ / }0.2304$ | $0.7442\text{ / }0.2300$ | $0.9119\text{ / }-0.1563$ | Referencia |
| **`R00`** (`control_gpr`) | $0.5222\text{ / }0.6208$ | $0.6398\text{ / }0.4309$ | $0.6533\text{ / }0.4067$ | $0.6585\text{ / }0.3970$ | No |
| **`R01`** (`gpr_geo`) | $0.5278\text{ / }0.6127$ | **$0.6308\text{ / }0.4467$** | $0.6494\text{ / }0.4137$ | **$0.6322\text{ / }0.4443$** | Parcial (2/4 por Tlaxcala) |
| **`R03`** (`biweekly_contrast`) | $0.5254\text{ / }0.6161$ | $0.6347\text{ / }0.4399$ | **$0.6437\text{ / }0.4239$** | $0.6386\text{ / }0.4329$ | Parcial (logra $R^2 > 0$ en Hidalgo espacial) |
| **`R06`** (`spectral_geo_ensemble`) | $0.5114\text{ / }0.6363$ | $0.6730\text{ / }0.3702$ | $0.6867\text{ / }0.3443$ | $0.7037\text{ / }0.3115$ | **SÍ (4 de 4 esquemas)** |
| **`R07`** (`hybrid_kriging_spectral`) | **$0.5042\text{ / }0.6465$** | $0.7008\text{ / }0.3172$ | $0.7098\text{ / }0.2995$ | $0.7735\text{ / }0.1680$ | **SÍ (4 de 4 esquemas)** |
| **`R08`** (`adaptive_ead`) | **$0.5056\text{ / }0.6446$** | **$0.6596\text{ / }0.3951$** | **$0.6718\text{ / }0.3725$** | **$0.6836\text{ / }0.3504$** | **SÍ (4 de 4 esquemas)** |

---

## 5. Calibración Conformal de Intervalos de Predicción al 90 %

Al calibrar los intervalos de predicción al $90\,\%$ escalados por estado ([`registry/interval-calibration.json`](file:///d:/Dev/Ciencia%20de%20datos/Cebada/experiments/estratificacion-pyr-20261018/registry/interval-calibration.json)):

| Modelo | Cobertura Nominal | Cobertura Empírica OOF | Anchura Media ($\text{t/ha}$) ↓ | Radio Puebla ($\pm\text{t/ha}$) | Radio Hidalgo ($\pm\text{t/ha}$) | Radio Tlaxcala ($\pm\text{t/ha}$) | Reducción de Anchura vs Activo ($2.935\text{ t/ha}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| *Modelo Activo Vigente (`selected`)* | $90.0\,\%$ | $92.03\,\%$ | $2.9350$ | $\pm 1.4675$ | $\pm 1.4675$ | $\pm 1.4675$ | Referencia |
| **`R06`** (`spectral_geo_ensemble`) | $90.0\,\%$ | **$94.20\,\%$** | $1.7475$ | $\pm 0.996$ | $\pm 0.752$ | $\pm 0.742$ | **$-40.5\,\%$** |
| **`R07`** (`hybrid_kriging_spectral`) | $90.0\,\%$ | **$93.48\,\%$** | $1.6743$ | $\pm 0.999$ | $\pm 0.673$ | $\pm 0.654$ | **$-43.0\,\%$** |
| **`R08`** (`adaptive_ead`) | $90.0\,\%$ | **$93.48\,\%$** | **$1.6682$** | $\pm 0.995$ | $\pm 0.669$ | $\pm 0.656$ | **$-43.2\,\%$** |

