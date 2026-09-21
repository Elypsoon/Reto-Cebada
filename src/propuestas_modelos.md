# Propuestas de Modelado Predictivo para Rendimiento de Cebada Maltera (Reto AgroCebada 2026)

## 1. Introducción y Planteamiento Matemático del Problema

El objetivo fundamental consiste en estimar el rendimiento de grano de cebada (*Hordeum vulgare*, expresado en toneladas por hectárea, t/ha) correspondiente al ciclo Primavera-Verano (abril a octubre de 2025) en 59 parcelas no observadas del Altiplano Central Mexicano (estados de Puebla, Hidalgo y Tlaxcala), a partir de una muestra de calibración de 138 parcelas con rendimiento conocido.

Desde la perspectiva del aprendizaje automático, este desafío se clasifica como un problema de regresión supervisada bajo un régimen de escasez muestral frente a una potencial alta dimensionalidad ($N = 138$ observaciones de entrenamiento frente a más de 200 variables candidatas entre índices satelitales multiespectrales, covariables climáticas y orografía). En este régimen ($p \gg N$), los modelos complejos no restringidos o redes neuronales profundas sufren de memorización espuria y colapso de generalización.

Por tanto, el diseño analítico propuesto no se limita a un ajuste empírico de curvas, sino que se fundamenta rigurosamente en la ecofisiología del cultivo, la dinámica hidrológica de los suelos regionales, la reconstrucción de señales de teledetección y un esquema estricto de validación cruzada espacial.

---

## 2. Fundamentación Biofísica y Disparidad Regional

Los datos de calibración revelan una heterogeneidad espacial marcada que responde a un gradiente geofísico y edafoclimático específico:

1. **Chignahuapan, Puebla (71 parcelas de entrenamiento; promedio 4.48 t/ha, rango [2.15, 5.59])**:
   * Ubicación en sotavento de la Sierra Norte de Puebla, con influencia de humedad orográfica del Golfo de México (precipitaciones de 650 a 850 mm y bajo déficit de presión de vapor, VPD).
   * Suelos volcánicos dominantes (Andosoles mólicos y Phaeozoles eútricos) con baja densidad aparente (< 0.85 g/cm³), alto carbono orgánico (SOC > 3.0%) y capacidad de agua disponible (AWC > 20% vol.), lo cual permite amortiguar periodos de estiaje mayores a 14 días.

2. **Llanos de Apan y Singuilucan, Hidalgo (36 parcelas de entrenamiento; promedio 3.76 t/ha, rango [2.00, 4.87])**:
   * Cuencas intermontanas templadas a semiáridas con precipitación estival intermedia (450 a 550 mm).
   * Suelos Phaeozoles y Cambisoles con horizontes fértiles pero expuestos a vientos desecantes y canícula intraestival moderada.

3. **Calpulalpan y Nanacamilpa, Tlaxcala (31 parcelas de entrenamiento; promedio 2.98 t/ha, rango [2.50, 3.50])**:
   * Cuenca endorreica bajo sombra de lluvia (400 a 500 mm).
   * Suelos someros (Durisoles y Leptosoles) caracterizados por horizontes petrocálcicos y capas endurecidas de tepetate a profundidades de 25 a 40 cm.
   * Volumen de enraizamiento efectivo severamente restringido (< 40 cm) y capacidad de almacenamiento útil inferior a 45 mm. La canícula de julio-agosto de 2025, caracterizada por temperaturas máximas recurrentes superiores a 29 °C, indujo estrés hídrico y térmico en antesis, provocando un elevado aborto de espiguillas y truncando el potencial a menos de 3.5 t/ha.

---

## 3. Catálogo de Datos Externos para Enriquecimiento del Modelo

Para garantizar que el modelo capture los mecanismos causales del rendimiento y no dependa exclusivamente de reflectancias satelitales expuestas a nubosidad, se integran las siguientes fuentes de datos abiertos:

| Variable / Capa | Fuente | Resolución Espacial / Temporal | Mecanismo de Extracción | Relevancia en el Modelo |
| :--- | :--- | :--- | :--- | :--- |
| **Propiedades Hidrofísicas del Suelo** | SoilGrids v2.0 (ISRIC) | 250 m / Estático | API REST (`https://rest.isric.org/soilgrids/v2.0/properties/query`) | Contenido de arcilla, arena, limo, carbono orgánico (SOC), pH, densidad aparente y Capacidad de Agua Disponible (AWC = Capacidad de Campo - Punto de Marchitez Permanente en 0-30 cm). |
| **Unidades y Fases Edafológicas** | INEGI (Serie II y IV) | Escala 1:250,000 / Estático | Unión espacial vectorial (Cartas E14-2, E14-3, F14-11) | Identificación de fases físicas limitantes (fase lítica, pedregosa y presencia de tepetate/duripán). |
| **Radiación Solar y Déficit de Presión de Vapor** | NASA POWER Agroclimatology | 0.5° x 0.5° / Diario | API REST (`https://power.larc.nasa.gov/api/temporal/daily/point`) | Radiación solar incidente (ALLSKY_SFC_SW_DWN en MJ/m²/día), déficit de presión de vapor (VPD en kPa), humedad relativa y cálculo diario de Grados Día de Desarrollo (GDD). |
| **Humedad del Suelo en Estratos** | ERA5-Land (Copernicus CDS) | 0.1° (~9 km) / Diario | API cliente `cdsapi` | Humedad volumétrica del suelo en capas 0-7 cm y 7-28 cm, y evapotranspiración potencial. |
| **Límites Empíricos Históricos** | SIAP (SADER) | Nivel municipal / Anual (2018-2024) | Registros abiertos SIACON | Definición de cotas de plausibilidad agronómica (*priors*) por municipio para el régimen de temporal. |

---

## 4. Ingeniería de Variables y Preprocesamiento Espectral

### 4.1. Reconstrucción de Perfiles Temporales mediante Whittaker-Eilers
Durante los meses de mayor actividad fotosintética (junio a septiembre), la presencia recurrente de nubes en el Altiplano Central degrada las observaciones ópticas. Se implementa el filtro de Whittaker-Eilers con penalización de segundo orden ($d = 2$), resolviendo el sistema lineal simétrico:

$$(W + \lambda D^T D) z = W y$$

Donde:
* $y$ representa el vector de observaciones espectrales.
* $z$ es la trayectoria suavizada resultante.
* $D$ es la matriz de diferencias finitas de segundo orden.
* $\lambda$ es el parámetro de rugosidad, optimizado mediante validación cruzada espacial.
* $W$ es la matriz diagonal de pesos de calidad atmosférica, parametrizada a partir de `porcentaje_nubosidad`: $w_i = 1.0$ para cielos despejados (nubosidad = 0), $w_i = 0.5$ para aerosoles moderados y $w_i = 0.0$ para observaciones contaminadas (nubosidad > 20%), forzando la interpolación analítica a través de las observaciones válidas.

### 4.2. Extracción de Métricas Fenológicas Cuantitativas (*Pheno-metrics*)
A partir de las curvas reconstruidas de NDVI, EVI, NDWI y LAI, se derivan rasgos sintéticos con alta significancia biológica:
* **vPOS (Valor en el Pico)**: Máxima amplitud de vigor alcanzada por el dosel, correspondiente al momento de máxima área foliar fotosintéticamente activa.
* **POS (Fecha del Pico)**: Día del año (DOY) en que se alcanza el máximo vigor, asociado a la etapa de floración/antesis.
* **AUC_Llenado (Área Bajo la Curva en Llenado de Grano)**: Integral temporal del índice de vegetación desde la fecha del pico hasta el fin de la estación (madurez fisiológica). Cuantifica la capacidad fotosintética neta durante la translocación de asimilados al grano (*stay-green*).
* **Tasa de Senescencia**: Pendiente de caída del índice pos-antesis, indicativa de desecación forzada por estrés o maduración natural.
* **Amplitud Estacional Dinámica**: Diferencia entre el pico máximo y el nivel basal del suelo.

### 4.3. Estrategia de Fusión Multisenso
* **Armonización Sentinel-2 y Landsat 8/9**: Aplicación de los coeficientes de transformación espectral de la iniciativa HLS (Harmonized Landsat Sentinel-2) de NASA/USGS para proyectar las reflectancias de Landsat hacia el estándar de Sentinel-2 MSI, permitiendo unificarlas en una sola serie de 30 m de resolución.
* **Tratamiento Independiente de PlanetScope**: Dado que la constelación PlanetScope está conformada por múltiples nanosatélites CubeSat con dispersión radiométrica, sus datos no se mezclan directamente con Sentinel-2. Se procesan en una rama paralela dedicada exclusivamente a:
  1. Identificar la fecha exacta del pico (POS) gracias a su alta frecuencia temporal.
  2. Extraer métricas de variabilidad espacial intra-parcelaria (`ndvi_std` en el pico de floración) a resolución de 3 metros.

---

## 5. Selección de Características y Control de Dimensionalidad ($p \gg N$)

Para reducir el espacio de entrada desde más de 200 variables iniciales hasta un conjunto parsimonioso de 10 a 15 predictores, se aplica un protocolo jerárquico en dos fases:

1. **Filtro mRMR (Minimum Redundancy Maximum Relevance)**:
   * Maximiza la información mutua entre cada variable predictora y el rendimiento objetivo (`RENDIMIENTO_T_HA`).
   * Penaliza la correlación de Pearson inter-variable para descartar variables colineales redundantemente correlacionadas (por ejemplo, entre múltiples variantes de índices de vegetación o temperaturas medias adyacentes).
   * Reduce la dimensionalidad inicial a las 25 mejores candidatas.

2. **Confirmación Estadística con Boruta-SHAP**:
   * Se generan variables aleatorias permutadas (*shadow features*).
   * Se entrena un ensamble de árboles y se calculan los valores de importancia SHAP de cada característica real frente a la mejor variable sombra.
   * Únicamente se retienen aquellas variables cuya contribución supera estadísticamente ($p < 0.01$) a las variables artificiales de control.

---

## 6. Protocolo de Validación Cruzada Espacialmente Bloqueada

El uso de validación cruzada aleatoria clásica (*K-Fold* aleatorio) es metodológicamente inadmisible en datos geoespaciales debido a la autocorrelación espacial. Parcelas cercanas comparten idéntica geología, clima y suelo; una partición aleatoria genera fuga de información espacial (*spatial data leakage*), produciendo métricas de validación infladas artificialmente.

Se implementa un esquema de **GroupKFold Espacial** estructurado en 5 bloques geográficos independientes, complementado con una zona de amortiguamiento (*spatial buffer*) de 3.5 km:

* **Pliegue 1**: Validación en Chignahuapan Norte (Puebla); entrenamiento en Chignahuapan Sur, Hidalgo y Tlaxcala.
* **Pliegue 2**: Validación en Chignahuapan Sur (Puebla); entrenamiento en Chignahuapan Norte, Hidalgo y Tlaxcala.
* **Pliegue 3**: Validación en Llanos de Apan y Tepeapulco (Hidalgo); entrenamiento en Puebla, Tlaxcala y resto de Hidalgo.
* **Pliegue 4**: Validación en Singuilucan, Cuautepec y Almoloya (Hidalgo); entrenamiento en Puebla, Tlaxcala y Llanos de Apan.
* **Pliegue 5**: Validación en Calpulalpan y Nanacamilpa (Tlaxcala); entrenamiento en todas las parcelas de Puebla e Hidalgo.

Este esquema evalúa la capacidad real del sistema de transferir predicciones a subregiones no vistas durante el entrenamiento.

---

## 7. Propuestas de Modelos Predictivos

Se evalúan cuatro propuestas técnicas estructuradas de menor a mayor complejidad, priorizando algoritmos robustos ante muestras reducidas:

### Propuesta 1: Modelo Lineal Regularizado Robusto (ElasticNet / Bayesian Ridge)
* **Descripción**: Modelo lineal con penalización combinada de norma L1 (Lasso) y L2 (Ridge).
* **Mecanismo Matemático**:

$$\min_{w} \frac{1}{2N} ||y - Xw||_2^2 + \alpha \rho ||w||_1 + \frac{\alpha(1-\rho)}{2} ||w||_2^2$$

* **Justificación**: Proporciona una línea base de referencia inmune al sobreajuste si se sintonizan adecuadamente $\alpha$ y la relación de mezcla $\rho$. Identifica dependencias lineales globales y asigna coeficientes directamente interpretables.
* **Limitación**: No modela interacciones no lineales complejas ni efectos de umbral biofísico (como caídas abruptas de rendimiento ante temperaturas superiores a 29 °C).

### Propuesta 2: Regresión por Procesos Gaussianos con Kernel ARD (GPR)
* **Descripción**: Modelo probabilístico no paramétrico basado en inferencia bayesiana.
* **Estructura del Kernel**: Se especifica una función de covarianza Matérn 5/2 o Exponencial Cuadrática con Determinación Automática de Relevancia (ARD), combinada con un kernel de ruido blanco:

$$k(x, x') = \sigma_f^2 \exp\left(-\frac{1}{2} \sum_{m=1}^{p} \frac{(x_m - x'_m)^2}{\ell_m^2}\right) + \sigma_n^2 \delta_{x, x'}$$

* **Justificación**: Cada dimensión predictora posee su propia longitud de escala $\ell_m$. Si una variable carece de poder predictivo, la optimización por máxima verosimilitud marginal incrementa $\ell_m \to \infty$, desactivando automáticamente la variable.
* **Ventaja Clave**: Suministra de forma nativa la media condicional $\hat{y}$ y la varianza de incertidumbre epistémica $\sigma^2(x)$ para cada una de las 59 parcelas de prueba, permitiendo identificar aquellas estimaciones con menor confiabilidad.

### Propuesta 3: Potenciación de Gradiente Regularizada de Baja Profundidad (CatBoost Regressor)
* **Descripción**: Ensamble de árboles de decisión simétricos (*oblivious trees*) optimizado para prevenir el sobreajuste en conjuntos de datos pequeños.
* **Configuración de Hiperparámetros Restringidos**:
  * Profundidad máxima reducida: `depth = 3` (restringe combinaciones complejas a interacciones de máximo tercer orden).
  * Regularización L2 en hojas elevada: `l2_leaf_reg = 6.0`.
  * Tasa de aprendizaje conservadora: `learning_rate = 0.02 - 0.03`.
  * Submuestreo de características y muestras: `subsample = 0.8`, `colsample_bylevel = 0.7`.
* **Justificación**: Captura de manera eficiente relaciones no lineales críticas, tales como la penalización por estrés hídrico durante la canícula y las respuestas asintóticas del índice de área foliar.

### Propuesta 4: Ensamble por Apilamiento Jerárquico (Stacking Ensemble) - Enfoque Principal
* **Descripción**: Arquitectura en dos niveles que combina la estabilidad lineal de ElasticNet, la modelación de incertidumbre probabilística de GPR-ARD y la no linealidad de CatBoost.
* **Estructura Arquitectónica**:
  * **Nivel 0 (Estimadores Base)**:
    1. Estimador A: `ElasticNetCV` (optimizado sobre rejilla de $\alpha$ y $\rho$).
    2. Estimador B: `GaussianProcessRegressor` (Kernel Matérn con ARD y optimización de hiperparámetros por gradiente).
    3. Estimador C: `CatBoostRegressor` (hiperparámetros restringidos).
  * **Nivel 1 (Meta-Estimador)**:
    * Regresión lineal con restricciones no negativas (`RidgeCV` con `positive=True`), entrenada exclusivamente sobre las predicciones fuera de pliegue (*out-of-fold*) generadas durante la validación cruzada espacial.
* **Justificación**: Resuelve el compromiso sesgo-varianza. La predicción final es una combinación convexa de modelos con supuestos de aprendizaje complementarios, reduciendo la varianza del error sin incrementar la complejidad paramétrica.

---

## 8. Hipotesis Fundamentadas sobre Variables Criticas y Combinacion Optima

Como paso previo a la calibracion empirica de los modelos, se formulan tres hipotesis teoricas fundamentadas en la ecofisiologia de *Hordeum vulgare*, la literatura de percepcion remota en cereales de grano pequeno y la dinamica agroclimatica especifica del ciclo 2025 en el Altiplano Central:

### 8.1. ¿Que indice es mas importante en la prediccion?
* **Hipotesis teorica**: La metrica mas determinante no es una observacion espectral puntual aislada, sino la **integral temporal bajo la curva del Indice de Vegetacion Mejorado en la etapa de llenado de grano (`AUC_Llenado_EVI`)**, complementada por el **valor maximo en el pico de floracion (`vPOS_EVI`)**.
* **Justificacion biofisica y espectral**:
  1. *Fisiologia del rendimiento*: El rendimiento final de grano depende en mas de un 60-70 % de la fotosintesis activa durante las etapas posteriores a la antesis (Zadoks 70 a 89, dias 75 a 105 post-siembra), cuando los fotoasimilados de la hoja bandera y las aristas de la espiga se translocan activamente hacia el endospermo. La metrica `AUC_Llenado` cuantifica de manera directa el fenomeno biologico de permanencia verde (*stay-green*) y la duracion efectiva del area foliar activa.
  2. *Superioridad de EVI sobre NDVI*: En parcelas de alta productividad como las de Chignahuapan (Puebla), donde los rendimientos superan las 4.5 t/ha, el dosel foliar alcanza indices de area foliar (LAI) elevados (> 3.5 m2/m2). En estas condiciones, el NDVI tradicional sufre de saturacion asintotica en la banda roja, perdiendo sensibilidad ante incrementos adicionales de biomasa. El indice EVI (Enhanced Vegetation Index) incorpora la banda azul para desacoplar aerosoles residuales y reduce la influencia del fondo del suelo, manteniendo una respuesta lineal ante densidades foliares altas.
  3. *Indicador complementario de estres hidrico*: En momentos de canicula o sequia intraestival, indices basados en infrarrojo de onda corta como `NDWI` o `MSI` durante el encanado y espigado actuan como moduladores criticos de la viabilidad de espiguillas por espiga.

### 8.2. ¿Que variable climatica tiene mayor peso?
* **Hipotesis teorica**: La variable climatica con mayor peso predictivo es el **Deficit de Presion de Vapor atmosferico medio durante floracion y llenado de grano (`VPD_julio_agosto`)**, interactuando con la **frecuencia de dias con temperaturas maximas extremas ($T_{max} > 28\text{ }^\circ\text{C}$)** y el **balance hidrico acumulado durante la canicula ($P_{CHIRPS} - ET_0$)**.
* **Justificacion agroclimatica e historica (Ciclo 2025)**:
  1. *El desacoplamiento climatico en la canicula de 2025*: Durante junio de 2025, precipitaciones extraordinarias en todo el Altiplano Central favorecieron una emergencia y macollamiento homogeneos. La divergencia productiva regional observada (Puebla: 4.48 t/ha frente a Tlaxcala: 2.98 t/ha) se gesto a partir de julio y agosto.
  2. *Impacto fisiologico del VPD elevado*: El VPD cuantifica la demanda evaporativa que ejerce la atmosfera sobre el dosel vegetal. Cuando el VPD supera 1.8 a 2.0 kPa en horas diurnas (situacion registrada de forma recurrente en Calpulalpan y los Llanos de Apan en 2025), la planta induce el cierre estomatico preventivo para mitigar la cavitacion xilematica, deteniendo la fijacion fotosintetica de CO2 en plena fase productiva.
  3. *Choque termico en organos reproductivos*: Temperaturas diurnas superiores a 28 °C durante la antesis (Zadoks 60-69) deshidratan los granos de polen e inducen aborto floral masivo. Asimismo, temperaturas superiores a 30-32 °C en llenado de grano desactivan la enzima almidon sintetasa soluble, forzando una maduracion prematura con grano chupado de bajo peso. Mientras Chignahuapan se mantuvo bajo un regimen de nieblas, alta humedad y bajo VPD, Tlaxcala sufrio calor y sequia durante este intervalo decisivo.

### 8.3. ¿Que combinacion de variables funciona mejor?
* **Hipotesis teorica**: El mejor desempeno predictivo y generalizacion espacial se obtendra mediante una **triada biofisica sinergica de dimension reducida (10 a 14 variables seleccionadas)** estructurada en tres subsistemas interactuantes:
  1. *El subsistema edafico amortiguador (Suelo)*: Capacidad de Agua Disponible en el estrato radicular (`AWC_0_30cm` extraida de SoilGrids v2.0), contenido de carbono organico (`SOC`) y presencia de limitantes mecanicas o tepetates someros (`FRUDICA/Fase_Litica` de INEGI).
  2. *El subsistema de forzamiento atmosferico (Clima)*: Deficit de presion de vapor estival (`VPD_julio_agosto`), acumulacion termica en llenado (`GDD_Z70_Z89`) y deficit hidrico de canicula ($P_{CHIRPS} - ET_0$).
  3. *El subsistema de respuesta biologica integrada (Planta)*: Integral de llenado de grano (`AUC_Llenado_EVI`), valor maximo del pico de vigor (`vPOS_EVI`) y heterogeneidad espacial intra-parcelaria (`ndvi_std` de PlanetScope en antesis).
* **Justificacion de la interaccion sinergica**:
  * Ninguna familia de variables es suficiente por si sola:
    * Las senales satelitales reflejan el verdor aparente, pero carecen de informacion directa sobre si el suelo subyacente ha agotado su reserva util o si un episodio inminente de VPD forzara el cierre estomatico.
    * Las grillas climaticas describen la oferta macroambiental regional, pero no discriminan si una parcela se asienta sobre un Andosol de alta retencion de humedad (Puebla) o sobre un Durisol con tepetate a 30 cm incapaz de retener agua (Tlaxcala).
    * Las capas edaficas definen el techo de capacidad de soporte hidrico, pero requieren del monitoreo satelital para evaluar el vigor real, la densidad de poblacion y la fecha de siembra efectiva lograda por el agricultor.
  * La combinacion de esta triada en un modelo regularizado (como el ensamble por Stacking propuesto) resuelve la asimetria dimensional $p \gg N$ y permite atribuir causalidad fisica transparente a cada estimacion mediante valores SHAP.

---

## 9. Metricas de Evaluacion y Criterios de Aceptacion

El desempeno se evalua a traves de cuatro metricas complementarias calculadas estrictamente sobre las predicciones de validacion cruzada espacial (*out-of-fold*):

1. **Raiz del Error Cuadratico Medio (RMSE)**:

$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2}$$

Penaliza errores de gran magnitud en parcelas individuales. Criterio de aceptacion: $\text{RMSE} < 0.45\text{ t/ha}$.

2. **Error Absoluto Medio (MAE)**:

$$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |y_i - \hat{y}_i|$$

Representa la desviacion promedio esperada en unidades agronomicas directas. Criterio de aceptacion: $\text{MAE} < 0.35\text{ t/ha}$.

3. **Coeficiente de Determinacion ($R^2$)**:

$$R^2 = 1 - \frac{\sum_{i=1}^{N} (y_i - \hat{y}_i)^2}{\sum_{i=1}^{N} (y_i - \bar{y})^2}$$

Evalua la fraccion de varianza capturada frente al predictor nulo. Criterio de aceptacion en validacion espacial: $R^2 > 0.70$.

4. **Error Porcentual Absoluto Medio (MAPE)**:

$$\text{MAPE} = \frac{100\%}{N} \sum_{i=1}^{N} \left| \frac{y_i - \hat{y}_i}{y_i} \right|$$

Garantiza equidad predictiva en parcelas de bajo rendimiento (Tlaxcala: ~2.5 t/ha) y de alto rendimiento (Puebla: ~5.0 t/ha). Criterio de aceptacion: $\text{MAPE} < 10\%$.

---

## 10. Auditoria de Coherencia Biologica mediante Valores SHAP

Antes de validar cualquier modelo para inferencia final, se auditan las atribuciones de Shapley para garantizar que las predicciones obedezcan principios agronomicos solidos:

1. **Respuesta de la Integral de Llenado (`AUC_Llenado`)**: Debe exhibir una correlacion monotona positiva uniforme ($\frac{\partial \phi}{\partial \text{AUC}} > 0$). Mayor persistencia de biomasa activa pos-antesis debe traducirse invariablemente en mayores rendimientos.
2. **Respuesta al Deficit de Presion de Vapor (`VPD_julio_agosto`)**: Debe reflejar un comportamiento de umbral negativo. Valores de VPD superiores a 1.8 kPa durante las horas diurnas deben asociarse a penalizaciones severas ($\phi < 0$).
3. **Respuesta a Variables Edaficas (`AWC_0_30cm` y `SOC`)**: En las zonas de deficit hidrico (Tlaxcala e Hidalgo), la mayor retencion de humedad y contenido de materia organica deben registrar atribuciones positivas directas.
4. **Control de Coordenadas Geograficas Puras**: Si las variables de latitud o longitud presentan alta importancia individual desplazando a las variables funcionales (clima, suelo e indices espectrales), el modelo habra memorizado la geografia comarcal en lugar de aprender el proceso biofisico. En tal eventualidad, las coordenadas se excluyen de la matriz de predictores.

---

## 11. Plan de Ejecucion Inmediato

1. **Fase 1: Extraccion y Enriquecimiento de Datos Externos**:
   * Ejecutar la consulta automatizada a la API de SoilGrids v2.0 para los centroides de las 197 parcelas (calculo de texturas y AWC superficial).
   * Descargar las series diarias de radiacion (ALLSKY_SFC_SW_DWN), temperaturas y VPD de la API de NASA POWER para el periodo 01/04/2025 al 31/10/2025.
2. **Fase 2: Procesamiento Espectral y Filtrado Whittaker**:
   * Implementar la limpieza de nubes y el suavizado de Whittaker ponderado por calidad en las series Sentinel-2 / Landsat armonizadas.
   * Extraer las metricas fenologicas sinteticas (vPOS, POS, AUC_Llenado, tasa de senescencia).
3. **Fase 3: Seleccion de Caracteristicas y Entrenamiento**:
   * Aplicar el protocolo mRMR + Boruta-SHAP.
   * Entrenar y comparar los cuatro modelos propuestos bajo el esquema estricto de GroupKFold Espacial de 5 bloques.
4. **Fase 4: Inferencia Final y Reporte de Validacion**:
   * Generar las 59 estimaciones con intervalos de incertidumbre y verificacion contra las cotas historicas del SIAP.
