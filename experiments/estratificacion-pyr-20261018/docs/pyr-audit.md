# Auditoría del Documento Oficial `PyR.pdf` y Geometría de la Partición 70/30

**Fase:** `estratificacion-pyr-20261018`  
**Fuente auditada:** [`DataSet/PyR.pdf`](file:///d:/Dev/Ciencia%20de%20datos/Cebada/DataSet/PyR.pdf) (*"Documento de apoyo para integrantes del jurado — Reto AgroCebada FIRA 2026"*)  
**Recibo criptográfico:** [`registry/pyr-split-audit.json`](file:///d:/Dev/Ciencia%20de%20datos/Cebada/experiments/estratificacion-pyr-20261018/registry/pyr-split-audit.json)

---

## 1. Síntesis de las 8 Precisiones Oficiales del Jurado

| Pregunta | Determinación Oficial (`PyR.pdf`) | Implicación Analítica Directa |
| :---: | :--- | :--- |
| **P1** | `AREA_HA` es la superficie del polígono georreferenciado y es el denominador de `RENDIMIENTO_T_HA` en las 197 parcelas sin excepciones. | Valida la conversión exacta $\text{Producción (t)} = \widehat{y}_{\text{t/ha}} \times \text{AREA\_HA}$. |
| **P2** | Las métricas principales son **RMSE, MAE y $R^2$ a nivel de `ID_POLIGONO` sin ponderar por superficie**, junto con la robustez metodológica. | Confirma la función de pérdida no ponderada por área ($1/59$ por polígono). |
| **P3** | Los rendimientos provienen principalmente de la **comercializadora** (pesaje en báscula **sin ajustar por humedad, impurezas ni mermas**) y en menor proporción **directamente de productores**. | Explica tanto la cuantización en Tlaxcala ($\{2.5, 3.0, 3.5\}\text{ t/ha}$) como el piso físico de ruido de báscula ($\sim 5-12\,\%$ por variación de humedad/mermas). Justifica el **encogimiento empírico de Bayes por varianza estatal** implementado en `R06`–`R08`. |
| **P4** | No se entregará qué `ID_POLIGONO` proviene de comercializadora y cuál de productor; ambos forman una sola variable objetivo. | El modelo debe adaptarse automáticamente a la varianza de cada régimen estatal sin requerir una etiqueta de fuente externa. |
| **P5** | **La división 70/30 (138 entrenamiento / 59 predicción) se realizó mediante muestreo aleatorio estratificado** para mantener representación comparable. | **Hallazgo central:** Las 59 parcelas de prueba no son bloques geográficos aislados, sino parcelas intercaladas en los mismos estados y municipios que las 138 de entrenamiento. |
| **P6** | No hay fecha de corte obligatoria para datos satelitales o climáticos del ciclo 2025; se permite información pública adicional. Si se propone uso pre-cosecha, debe declararse la fecha de corte. | Respalda el corte al 31 de octubre de 2025 para las 59 predicciones oficiales y motiva documentar la disponibilidad por ventana fenológica. |
| **P7** | No hay un umbral fijo de error en $\text{t/ha}$; **se valorará especialmente interpretar qué implica una desviación en $\text{t/ha}$ en términos productivos para el productor y sus limitaciones reales**. | El informe y el tablero deben traducir el MAE/RMSE a toneladas por parcela media ($6.6\text{ ha}$), ingreso bruto y cobertura de costos/crédito. |
| **P8** | La evaluación oficial se realizará **exclusivamente con las 59 parcelas reservadas del conjunto de 197 parcelas actuales** (sin campañas adicionales). | Descarta contaminar el entrenamiento con campañas externas heterogéneas (como CIMMYT 2012–2022) y prioriza maximizar la precisión sobre la cohorte 2025. |

---

## 2. Verificación Empírica del Muestreo Estratificado 70/30

### 2.1. Distribución por Estado y Municipio

| Estado | Municipio | Entrenamiento (`70 %`) | Predicción (`30 %`) | Total | Proporción Test (`%`) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Puebla** | Chignahuapan | $71$ | $29$ | $100$ | $29.0\,\%$ |
| **Hidalgo** | Singuilucan | $16$ | $7$ | $23$ | $30.4\,\%$ |
| **Hidalgo** | Almoloya | $10$ | $4$ | $14$ | $28.6\,\%$ |
| **Hidalgo** | Cuautepec de Hinojosa | $5$ | $4$ | $9$ | $44.4\,\%$ |
| **Hidalgo** | Emiliano Zapata / Apan / Tepeapulco | $5$ | $0$ | $5$ | $0.0\,\%$ |
| **Tlaxcala** | Calpulalpan | $30$ | $14$ | $44$ | $31.8\,\%$ |
| **Tlaxcala** | Nanacamilpa de Mariano Arista | $1$ | $1$ | $2$ | $50.0\,\%$ |
| **Total Global** | **9 municipios** | **$138$** | **$59$** | **$197$** | **$29.95\,\%$** |

### 2.2. Proximidad Espacial entre las 59 Parcelas de Prueba y las 138 de Entrenamiento (`EPSG:32614`)

Al calcular la distancia euclidiana en metros desde el centroide de cada una de las 59 parcelas de `PREDICCION` hacia su parcela de `ENTRENAMIENTO` más cercana:

* **Distancia mínima:** $66.8\text{ m}$
* **Percentil 25 %:** $225.9\text{ m}$
* **Mediana (Percentil 50 %):** **$350.4\text{ m}$**
* **Media:** $494.5\text{ m}$ ($\pm 401.8\text{ m}$)
* **Percentil 75 %:** $563.2\text{ m}$
* **Distancia máxima:** $1,915.0\text{ m}$ ($1.91\text{ km}$)
* **Proporción de parcelas de prueba con vecino de entrenamiento a $\le 600\text{ m}$:** **$76.3\,\%$** ($45\text{ de }59$)
* **Proporción de parcelas de prueba con vecino de entrenamiento a $\le 1,000\text{ m}$:** **$86.4\,\%$** ($51\text{ de }59$)

