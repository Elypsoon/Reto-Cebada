# Conclusiones y Recomendación de Promoción — Fase `estratificacion-pyr-20261018`

## 1. Síntesis científica: lo que cambió gracias a `PyR.pdf`

1. **Alineación entre el mecanismo generador de la partición y el protocolo de evaluación (Pregunta 5 de `PyR.pdf`)**:
   - Las fases previas del repositorio evaluaban los modelos exclusivamente mediante bloques espaciales disjuntos (`principal-5`, `balanceado-4`, `rotado-45-5`), donde cada bloque de validación está separado varios kilómetros de los datos de entrenamiento.
   - Sin embargo, la respuesta oficial de la **Pregunta 5 de `PyR.pdf`** confirmó que la partición 70/30 (`138` parcelas de entrenamiento y `59` de prueba) se realizó por **muestreo aleatorio estratificado** dentro de los mismos estados y municipios.
   - Nuestra auditoría geométrica ([`pyr-split-audit.json`](../registry/pyr-split-audit.json)) demostró que el **76.3 %** de las 59 parcelas objetivo tiene una parcela de entrenamiento a **menos de 600 metros** (mediana: **350.4 m**), lo que hace físicamente legítimo combinar señales espectrales y topográficas con priors espaciales locales de corto alcance.

2. **Eliminación del sobreajuste por selección anidada (`R00` vs. modelo activo `selected`)**:
   - El selector interno de 81 configuraciones del modelo activo (`selected`) elegía distintos hiperparámetros por pliegue y degradaba el RMSE estratificado a `0.6010 t/ha` y el espacial a `0.7641 t/ha`.
   - Fijar la arquitectura `control_gpr` sin búsqueda anidada ruidosa (`R00`) redujo el RMSE a **`0.5222 t/ha`** en `estratificado-5` y **`0.6398 t/ha`** en `principal-5`.

3. **Desbloqueo del poder predictivo en Hidalgo mediante contraste local de 1 km y anomalías multianuales (`R03`)**:
   - Al incorporar trayectorias quincenales (14 días) de Sentinel-2, Planet y Landsat (`vi6t`), anomalías históricas 2025 vs. 2022–2024 de la propia parcela y el contraste espectral/topográfico respecto al vecindario gaussiano de 1 km ($\Delta X_i = X_i - \bar{X}_{1\text{km}}$, calculado sin usar `Y`), la corrida `R03` se convirtió en el **único modelo de todo el proyecto con $R^2$ intra-estatal positivo en Hidalgo bajo validación por bloques espaciales (`principal-5`: $R^2 = +0.0998$, RMSE = `0.7275 t/ha`)** y obtuvo el mejor RMSE global en `balanceado-4` (**`0.6437 t/ha`**).

4. **Corrección de la cuantización de Tlaxcala mediante Empirical Bayes Shrinkage (`R06`, `R07`, `R08` — Pregunta 3 de `PyR.pdf`)**:
   - La **Pregunta 3 de `PyR.pdf`** reveló que el target mezcla pesajes continuos de báscula comercial en Puebla/Hidalgo con reportes redondeados por el productor en Tlaxcala ($\{2.5, 3.0, 3.5\}\text{ t/ha}$).
   - Aplicar encogimiento empírico de Bayes por estado ($\gamma_{\text{Tlaxcala}} = 0.72$) estabilizó las predicciones en Tlaxcala y permitió que **`R06`, `R07` y `R08` superaran por primera vez en el proyecto los 4 esquemas de validación de forma simultánea** (`passes_all_4_schemes = true` en [`eligibility-evaluation.json`](../registry/eligibility-evaluation.json)), venciendo a la media regional `B0` en los 3 estados bajo `estratificado-5`.

## 2. Comparativa de los 3 modelos elegibles (`R06`, `R07`, `R08`) frente al baseline y al modelo activo

| Modelo | Rol | Holdout 70/30 (`30x`) RMSE | `estratificado-5` RMSE | `estratificado-5` MAE | `estratificado-5` $R^2$ | `principal-5` RMSE | `balanceado-4` RMSE | `rotado-45-5` RMSE | Pasa los 4 esquemas |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| `selected` (activo raíz) | Baseline código actual | `0.6010`* | `0.6010` | `0.4322` | `0.4979` | `0.7641` | `0.7793` | `0.8199` | No |
| `B0` (`regional_mean`) | Baseline regional | `0.5905 ± 0.0501` | `0.6053` | `0.4415` | `0.4906` | `0.7440` | `0.7662` | `0.7734` | Baseline |
| **`R06`** (`spectral_geo_ensemble`) | Ensamble espectral-geográfico puro | `0.4976 ± 0.0613` | `0.5114` | `0.3641` | `0.6363` | **`0.6416`** | **`0.6540`** | **`0.6648`** | **Sí** |
| **`R07`** (`hybrid_kriging_spectral`) | Híbrido 50/50 Kriging + Espectral | **`0.4920 ± 0.0565`** | **`0.5042`** | **`0.3535`** | **`0.6465`** | `0.6897` | `0.6889` | `0.6929` | **Sí** |
| **`R08`** (`adaptive_ead`) | Híbrido adaptativo por distancia | `0.4936 ± 0.0586` | `0.5056` | `0.3547` | `0.6446` | `0.6596` | `0.6718` | `0.6836` | **Sí** |

## 3. Interpretación productiva y económica (Pregunta 7 de `PyR.pdf`)

- Con un **MAE de `0.3516–0.3547 t/ha`** sobre un rendimiento medio de `2.86 t/ha` (**~12.3 % de error absoluto medio relativo**):
  - En **Hidalgo** (`MAE = 0.285 t/ha`, $R^2 = 0.759$) y **Tlaxcala** (`MAE = 0.289 t/ha`), el error promedio equivale a menos de **0.30 toneladas por hectárea**, lo que permite planificar acopio por municipio, detectar parcelas rezagadas antes de la cosecha y priorizar visitas de asistencia técnica agronómica.
  - En **Puebla** (`MAE = 0.415 t/ha`, `RMSE = 0.588 t/ha`), donde existe la mayor dispersión de manejo hídrico y altitudinal, la calibración conformal escalada por estado ([`interval-calibration.json`](../registry/interval-calibration.json)) acota la incertidumbre al 90 % en **$\pm 0.995\text{ t/ha}$** (frente a $\pm 1.468\text{ t/ha}$ del modelo activo), mientras que en Hidalgo y Tlaxcala los intervalos al 90 % se estrechan a **$\pm 0.669\text{ t/ha}$** y **$\pm 0.656\text{ t/ha}$** respectivamente, logrando una cobertura empírica real de **93.48 %** y una reducción del **43.2 %** en la anchura total de las bandas de incertidumbre.

## 4. Recomendación operativa

1. **Para estimar con máxima precisión el 30 % de parcelas faltantes (59 parcelas de prueba)**:
   - Se recomienda **`R08` (`adaptive_ead`)** (o **`R07` (`hybrid_kriging_spectral`)**, cuyas predicciones en las 59 parcelas tienen correlación $r > 0.995$ con `R08`). `R08` ofrece la ventaja arquitectónica de ponderar automáticamente el prior de kriging según la distancia real al vecino más cercano ($d_{\min}$): aprovecha la interpolación local cuando la parcela objetivo está dentro de un clúster denso ($d_{\min} \approx 350\text{ m}$) y delega suavemente al ensamble espectral-geográfico (`R06`) cuando la parcela está aislada o en un bloque nuevo ($d_{\min} > 1.2\text{ km}$).
2. **Para proyecciones en regiones o municipios sin muestras cercanas de cosecha**:
   - El componente base **`R06` (`spectral_geo_ensemble`)** o **`R03` (`biweekly_contrast`)** se activa automáticamente cuando $w(d_{\min}) \to 0$, garantizando robustez espacial en los 3 esquemas por bloques (`RMSE = 0.6416–0.6648 t/ha`).

