# Auditoría Forense de Parcelas Atípicas y Registro de Importancia por Estado (`F1`–`F5`)

## 1. ¿Por qué la Selección Global de Variables Omitió la Señal Intra-Estatal?
En las fases previas, el selector compacto (`CompactSelector`) ordenaba las variables por su **correlación global** con el rendimiento bruto $Y$ sobre las 138 parcelas combinadas. Debido a que el salto entre medias estatales ($\mu_{\text{Puebla}} = 4.48$, $\mu_{\text{Hidalgo}} = 3.76$, $\mu_{\text{Tlaxcala}} = 2.98\text{ t/ha}$) explica el $49.1\%$ de la varianza total, cualquier ranking global queda dominado por variables macro-climáticas (`climate_Tmean`, `nasa_vpd`, `elevation`) que distinguen a Puebla de Tlaxcala pero son prácticamente constantes dentro de Chignahuapan o Calpulalpan.

Al evaluar la correlación **dentro de cada estado** ([`feature-importance.csv`](../registry/feature-importance.csv) y [`feature-importance.json`](../registry/feature-importance.json)), descubrimos que cada región agroecológica está gobernada por mecanismos fisiológicos distintos:

### Impulsores Principales por Estado
| Estado | Top Variables Intra-Estatales | Correlación ($r$) | Interpretación Agronómica |
| --- | --- | :---: | --- |
| **Puebla** ($n=71$) | `slope`, `f2_fapar_early`, `f4_tillage_ndti_std_early`, `log_area`, `f3_fapar_min_early`, `f5_ndwi_q90_hist` | $+0.324$ a $-0.300$ | Drenaje por pendiente (`slope`), radiación absorbida temprana (`FAPAR`), uniformidad de labranza pre-siembra (`NDTI`/`STI`) y escala de manejo (`log_area`: lotes pequeños intensivos $<1.5\text{ ha}$ rinden $5.45\text{–}5.59\text{ t/ha}$ frente a lotes extensivos $>11\text{ ha}$). |
| **Hidalgo** ($n=36$) | `pl_evi_bw_min`, `pl_evi_bw_early`, `pl_msavi_bw_min`, `s2_evi_early`, `f2_savi_early`, `parcel_density_2km` | $+0.796$ a $-0.662$ | Establecimiento vegetativo temprano a resolución de $3\text{ m}$ (Planet EVI/MSAVI) y corrección de brillo de suelo (`SAVI`). |
| **Tlaxcala** ($n=31$) | `f3_damage_floor_early`, `landsat_vi6t_middle_diff_local1km`, `ls_vi6t_bw_senescence_drop`, `f3_srndi_min_sepoct` | $+0.473$ a $-0.406$ | Piso de daño por sequía/helada intraparcela (`ENDDI_min` + `NDDI_min`), contraste térmico/espectral de $1\text{ km}$ (`VI6T`) y caída de senescencia. |

---

## 2. Auditoría Forense de las 5 Parcelas Atípicas ([`forensic-outlier-audit.json`](../registry/forensic-outlier-audit.json))

| Parcela | Estado / Municipio | Rendimiento Real ($Y$) | Área (`ha`) | Vecino de Entrenamiento Más Cercano | Hallazgo Forense |
| --- | --- | :---: | :---: | --- | --- |
| **`AGC_171`** | Puebla / Chignahuapan | **$2.15\text{ t/ha}$** | $11.63\text{ ha}$ | `AGC_024` a **$299.6\text{ m}$** ($3.03\text{ t/ha}$, $11.53\text{ ha}$) | Forma un micro-clúster occidental en Chignahuapan junto con `AGC_024`: ambos son polígonos extensivos ($>11.5\text{ ha}$, $z_{\text{log\_area}} = +1.43$), en terreno más plano ($z_{\text{slope}} = -0.69$) y con colapso en el piso mínimo de radiación absorbida temprana (`f3_fapar_min_early` $z = -1.94$). |
| **`AGC_024`** | Puebla / Chignahuapan | **$3.03\text{ t/ha}$** | $11.53\text{ ha}$ | `AGC_171` a **$299.6\text{ m}$** ($2.15\text{ t/ha}$, $11.63\text{ ha}$) | Comparte exactamente la huella de lote extensivo plano ($z_{\text{slope}} = -1.01$) y bajo piso de `FAPAR` ($z = -1.24$), mientras que a $460\text{ m}$ se ubican parcelas de $4.57\text{ t/ha}$. El Kriging con similitud agronómica (`E04`/`E06`) vincula a `AGC_171` y `AGC_024` por su geometría y vigor temprano en vez de promediarlas ciegamente con lotes intensivos. |
| **`AGC_015`** | Puebla / Chignahuapan | **$2.64\text{ t/ha}$** | $1.97\text{ ha}$ | `AGC_092` a **$644.0\text{ m}$** ($4.57\text{ t/ha}$, $0.50\text{ ha}$) | Tuvo alto vigor inicial (`s2_evi_early` $z = +1.32$), pero presenta un déficit severo en su potencial hídrico histórico (`f5_ndwi_q90_hist` $z = -1.23$) y un piso mínimo de `FAPAR` deprimido ($z = -1.22$), consistente con un siniestro parcial focalizado que el promedio poligonal de NDVI ocultaba. |
| **`AGC_034`** | Hidalgo / Singuilucan | **$2.00\text{ t/ha}$** | $8.09\text{ ha}$ | `AGC_038` a **$544.5\text{ m}$** ($3.30\text{ t/ha}$, $3.28\text{ ha}$) | Presenta baja pendiente ($z = -0.69$) y caída marcada en vigor temprano tanto en Sentinel-2 (`s2_evi_early` $z = -0.71$) como en Planet $3\text{ m}$ (`pl_evi_bw_min` $z = -0.85$). |
| **`AGC_166`** | Hidalgo / Singuilucan | **$2.50\text{ t/ha}$** | $6.76\text{ ha}$ | `AGC_041` a **$368.6\text{ m}$** ($2.50\text{ t/ha}$, $25.13\text{ ha}$) | Su vecino inmediato a $368.6\text{ m}$ rinde exactamente $2.50\text{ t/ha}$ y comparte el déficit hídrico multianual (`f5_ndwi_q90_hist` $z = -1.65$) y bajo establecimiento temprano (`s2_evi_early` $z = -1.08$). |

---

## 3. Las 5 Familias de Características Destiladas (`F1`–`F5`)
Para evitar la maldición de la dimensionalidad ($p \gg n=110$ por pliegue), las 19 bandas satelitales no utilizadas y las estadísticas intrapolígono (`_min`, `_std`) se destilaron en **20 indicadores compuestos con significado biofísico directo**:
1. **`F1` — Alineación Fenológica Dinámica por Fecha Pico ($t_{\text{pico}}$)**: `f1_peak_biweek`, `f1_pre_peak_vigor`, `f1_peak_vigor`, `f1_grainfill_vigor`, `f1_senescence_drop`, `f1_msi_at_grainfill`.
2. **`F2` — Índices Fisiológicos y de Estrés Hídrico/Sanitario**: `f2_fapar_early`, `f2_fapar_mid`, `f2_lai_mid`, `f2_savi_early`, `f2_msi_grainfill`, `f2_dswi4_early`.
3. **`F3` — Piso de Daño y Heterogeneidad Intra-Parcela (`_min`, `_std`)**: `f3_fapar_min_early`, `f3_damage_floor_early`, `f3_srndi_min_sepoct`, `f3_evi_minratio_early`.
4. **`F4` — Labranza y Rastrojo Pre-Siembra (Abril–Mayo)**: `f4_tillage_ndti_std_early` (`NDTI_std` + `STI_std`).
5. **`F5` — Latente Auto-Supervisada sobre los 788 Ciclos Parcela × Año (2022–2025)**: `f5_ndwi_q90_hist`, `f5_pl_evi_q90_hist`, `f5_pl_evi_anom_2025`.

