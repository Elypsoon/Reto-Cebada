# Prediccion del Rendimiento Agricola de Cebada Maltera (Reto AgroCebada 2026)

**Dashboard interactivo:** [AgroCebada · Explorar parcelas](https://agrocebada-2026.leonforce033.workers.dev/). Código React, datos y recursos en [`frontend/`](frontend/README.md). Para ejecutarlo: `npm --prefix frontend ci` y `npm run dashboard`.

## Modelado Analitico con Percepcion Remota, Clima y Topografia

---

## 1. Resumen Ejecutivo y Objetivos del Proyecto

El Reto AgroCebada 2026 tiene como proposito principal el diseno, calibracion, validacion y despliegue de un sistema analitico predictivo basado en aprendizaje automatico supervisado para estimar con alta precision el rendimiento de grano de cebada maltera (*Hordeum vulgare*, expresado en toneladas por hectarea, t/ha). El estudio se focaliza en parcelas ubicadas en los estados de Puebla, Hidalgo y Tlaxcala, Mexico, correspondientes al ciclo agricola Primavera-Verano (abril a octubre de 2025).

### Metas Fundamentales
1. **Inferencia sobre el Conjunto de Prueba (30 %)**: Predecir con rigor cientifico el rendimiento de 59 parcelas no observadas a partir de una muestra de calibracion de 138 parcelas con rendimiento conocido (particion 70 % entrenamiento / 30 % evaluacion sobre un universo de 197 unidades de produccion).
2. **Integracion Multimodal de Datos**: Fusionar series temporales opticas multiespectrales de satelite (Sentinel-2, Landsat y PlanetScope), matrices climaticas continuas de reanalisis (CHIRPS y CHIRTS-ERA5), modelado topografico de alta resolucion (INEGI CEM 4.0) y propiedades edafologicas hidrofisicas externas.
3. **Generalizacion Geoespacial sin Fuga de Informacion**: Implementar protocolos de validacion cruzada espacialmente bloqueada que neutralicen el sobreajuste provocado por autocorrelacion geografica, asegurando que las estimaciones sean transferibles entre subregiones edafoclimaticas contrastantes.
4. **Sustentabilidad y Eficiencia Productiva**: Fomentar el uso de herramientas analiticas reproducibles para la optimizacion de insumos y la gestion integral del riesgo climatico en el sector cebadero nacional.

---

## 2. Estructura General del Repositorio

```text
Cebada/
├── README.md                                          # Documento maestro de arquitectura del proyecto
├── DataSet/                                           # Repositorio de datos crudos e insumos documentales
│   ├── Prediccion Rendimiento Cebada Maltera.pdf      # Reporte cientifico y estado del arte del modelado
│   ├── Descripcion_general_variables_DataSet.docx     # Especificacion institucional del conjunto de datos
│   ├── Diccionario_de_indices_satelitales.docx        # Definicion conceptual de indices espectrales
│   ├── Data/                                          # Archivos tabulares estructurados (CSV)
│   │   ├── ID_area_rendimiento_70_30_Reto_AgroCebada.csv   # Metadatos de parcelas y variable objetivo
│   │   ├── Conjunto_datos_BASICO_AgroCebada2026.csv        # Series Sentinel-2 y Landsat (2022-2025)
│   │   └── Conjunto_datos_PRO_AgroCebada.csv               # Series PlanetScope de alta frecuencia (2025)
│   ├── Parcelas_AGC_CONJUNTO_70_30/                   # Capa vectorial oficial de parcelas
│   │   ├── Parcelas_Reto_AGC_CONJUNTO.shp             # Geometrias poligonales (EPSG:4326)
│   │   ├── Parcelas_Reto_AGC_CONJUNTO.dbf             # Atributos (Cultivo, Municipio, Estado, Area, Conjunto)
│   │   ├── Parcelas_Reto_AGC_CONJUNTO.prj             # Proyeccion cartografica WGS84
│   │   ├── Parcelas_Reto_AGC_CONJUNTO.shx             # Indice posicional de formas
│   │   └── Parcelas_Reto_AGC_CONJUNTO.cpg             # Codificacion de caracteres
│   ├── CHIRPS_Precipitacion_2022_2025/                # Precipitacion mensual acumulada (GeoTIFF)
│   │   └── Precipitacion_mensual/                     # 48 archivos (2022 a 2025, 0.05 grados)
│   ├── Temperatura_2022_2025_RECORTADA_CHIRPS/        # Temperatura mensual de CHIRTS-ERA5 (GeoTIFF)
│   │   ├── Tmax/                                      # 48 archivos de temperatura maxima mensual
│   │   └── Tmin/                                      # 48 archivos de temperatura minima mensual
│   └── Topografia_INEGI_CEM4/                         # Modelo Digital de Elevacion del INEGI (120 m)
│       ├── Elevacion_INEGI_CEM4_120m.tif              # Altitud sobre el nivel del mar (m s.n.m.)
│       ├── Pendiente_INEGI_CEM4_120m_grados.tif       # Pendiente del terreno en grados sexagesimales
│       ├── inventario_topografia.csv                  # Estadisticas zonales de topografia
│       └── LEEME.txt                                  # Especificaciones tecnicas de INEGI
└── src/                                               # Codigo fuente e ingenieria analitica
    └── propuestas_modelos.md                          # Propuestas tecnicas de algoritmos y evaluacion
```

---

## 3. Inventario y Caracterizacion de Datos Disponibles

### 3.1. Parcelas y Variable Objetivo

El conjunto comprende 197 parcelas delimitadas espacialmente en los Valles Altos de Mexico:
* **Sistema de Coordenadas**: WGS 1984 (`EPSG:4326`).
* **Envolvente Espacial**: Longitud [-98.6130° O, -98.1967° O], Latitud [19.5238° N, 19.9844° N].
* **Conjunto de Calibracion (Entrenamiento)**: 138 parcelas (70.05 %) con rendimiento real medido (`RENDIMIENTO_T_HA`, t/ha).
* **Conjunto de Evaluacion (Prediccion)**: 59 parcelas (29.95 %) con rendimiento oculto para inferencia ciega.

#### Distribucion por Estado y Municipio

| Estado | Total Parcelas | Entrenamiento (70 %) | Prediccion (30 %) | Rendimiento Medio (t/ha) | Desv. Est. (t/ha) | Rango [Min, Max] (t/ha) | Municipios |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Puebla** | 100 | 71 | 29 | 4.48 | 0.58 | [2.15, 5.59] | Chignahuapan (100) |
| **Hidalgo** | 51 | 36 | 15 | 3.76 | 0.78 | [2.00, 4.87] | Singuilucan (23), Almoloya (14), Cuautepec (9), Emiliano Zapata (3), Tepeapulco (1), Apan (1) |
| **Tlaxcala** | 46 | 31 | 15 | 2.98 | 0.38 | [2.50, 3.50] | Calpulalpan (44), Nanacamilpa (2) |
| **Total** | 197 | 138 | 59 | 3.96 | 0.85 | [2.00, 5.59] | 9 municipios |

#### Distribucion de Superficie (`AREA_HA`)
* Minimo: 0.35 ha | Primer Cuartil (25 %): 2.30 ha | Mediana: 5.46 ha | Media: 6.60 ha | Tercer Cuartil (75 %): 8.09 ha | Maximo: 64.30 ha.

---

### 3.2. Monitoreo Satelital de Series Temporales

#### A. Conjunto de Datos Basico (`Conjunto_datos_BASICO_AgroCebada2026.csv`)
* Total de observaciones: 107,666 registros.
* Periodo temporal: 01/01/2022 al 31/12/2025.
* Plataformas: Sentinel-2 MSI (59,040 registros) y Landsat 8/9 OLI/TIRS (48,626 registros).
* Indices provistos (con estadisticos zonales `_promedio`, `_std`, `_max`, `_min` y `porcentaje_nubosidad`):
  * Vigor y estructura foliar: NDVI, EVI, LAI, FAPAR, SAVI, MRA.
  * Contenido hidrico y estres: NDWI, ENDWI, MSI, EMSI, DSWI2, DSWI3, DSWI4, DSWI5, NDDI, ENDDI.
  * Residuos de cosecha y labranza: CRC, MCRC, NDSVI, SRNDI, NDTI, STI.
  * Termico-espectral: VI6T (Landsat).

#### B. Conjunto de Datos PRO (`Conjunto_datos_PRO_AgroCebada.csv`)
* Total de observaciones: 47,804 registros.
* Periodo temporal: 01/01/2025 al 12/12/2025.
* Sensor: PlanetScope (~3 m de resolucion espacial, frecuencia cuasi-diaria).
* Indices incluidos: NDVI, EVI, LAI, MSAVI y porcentaje de nubosidad.

---

### 3.3. Insumos Climaticos y Topograficos

* **Precipitacion Mensual CHIRPS**: 48 rasters GeoTIFF (2022-2025) a resolucion de 0.05 grados (~5.5 km).
* **Temperatura Mensual CHIRTS-ERA5**: 96 rasters GeoTIFF (48 de Tmin y 48 de Tmax, 2022-2025) a resolucion de 0.05 grados.
* **Topografia INEGI CEM 4.0**:
  * `Elevacion_INEGI_CEM4_120m.tif`: Altitud del terreno (m s.n.m., EPSG:6372).
  * `Pendiente_INEGI_CEM4_120m_grados.tif`: Gradiente de pendiente en grados sexagesimales (Horn 3x3).

---

## 4. Hallazgos de la Investigacion Cientifica y Bases Biofisicas

De acuerdo con el analisis exhaustivo documentado en `DataSet/Prediccion Rendimiento Cebada Maltera.pdf`, la disparidad en los rendimientos observados se explica mediante mecanismos causales especificos:

1. **Puebla (Chignahuapan, 4.48 t/ha)**:
   * Emplazamiento en la ladera de sotavento de la Sierra Norte de Puebla, con flujo constante de humedad orografica del Golfo de Mexico (lluvia estival de 650 a 850 mm y bajo deficit de presion de vapor).
   * Suelos volcanicos profundos (Andosoles molicos) con densidad aparente reducida (< 0.85 g/cm³), carbono organico superior al 3.0 % y Capacidad de Agua Disponible (AWC) superior al 20 % volumetrico, capaces de amortiguar estiajes mayores a dos semanas.

2. **Hidalgo (Llanos de Apan y Singuilucan, 3.76 t/ha)**:
   * Valles intermontanos con precipitacion estival moderada (450 a 550 mm).
   * Suelos Phaeozoles y Cambisoles con fertilidad adecuada pero vulnerables a vientos desecantes y canicula intermedia.

3. **Tlaxcala (Calpulalpan y Nanacamilpa, 2.98 t/ha)**:
   * Cuenca endorreica bajo efecto de sombra de lluvia (400 a 500 mm).
   * Suelos someros (Durisoles y Leptosoles) con horizontes endurecidos de tepetate a 25-40 cm de profundidad, restringiendo el volumen radicular y limitando la reserva util de agua a menos de 45 mm.
   * Durante el ciclo 2025, una canicula severa en julio y agosto con temperaturas maximas recurrentes superiores a 29 °C coincidio con la antesis e inicio de llenado de grano, causando deshidratacion del polen, aborto de espiguillas y fijando el rendimiento por debajo de 3.5 t/ha.

---

## 5. Integracion de Fuentes de Datos Abiertos

Para reforzar la capacidad explicativa y predictiva del sistema, se integran las siguientes bases de datos de acceso publico mediante protocolos programaticos:

| Base de Datos | Entidad | Variables Extraidas | Metodo de Acceso |
| :--- | :--- | :--- | :--- |
| **SoilGrids v2.0** | ISRIC | Arcilla, arena, limo, carbono organico (SOC), pH, densidad aparente y Capacidad de Agua Disponible (AWC = Capacidad de Campo - Punto de Marchitez Permanente en 0-30 cm). | API REST (`https://rest.isric.org/soilgrids/v2.0/properties/query`) |
| **Edafologia Serie II y IV** | INEGI | Unidades WRB, textura y fases limitantes fisicas (tepetates, duripan, fase litica). | Descarga cartografica y union espacial vectorial (Cartas E14-2, E14-3, F14-11). |
| **NASA POWER Agroclimatology** | NASA Langley | Radiacion solar global incidente (ALLSKY_SFC_SW_DWN en MJ/m²/dia), deficit de presion de vapor (VPD en kPa), humedad relativa y Grados Dia de Desarrollo diarios (GDD). | API REST (`https://power.larc.nasa.gov/api/temporal/daily/point`) |
| **ERA5-Land** | ECMWF / Copernicus CDS | Humedad volumetrica del suelo en 4 capas (0-7, 7-28, 28-100, 100-289 cm) y evapotranspiracion potencial. | API cliente `cdsapi`. |
| **Estadisticas Agricolas SIAP** | SADER / SIAP | Rendimientos historicos municipales (2018-2024) para calibracion de limites de plausibilidad (*priors*). | Descargas abiertas SIACON. |

---

## 6. Pipeline Analitico y Procesamiento de Senales

```text
[Series Opticas Crudas] --------> [Filtro Whittaker-Eilers (QA)] ------> [Curvas Suaves]
[Rasters CHIRPS/CHIRTS] -------> [Extraccion Zonal por Parcela] -------> [Variables Climaticas]
[SoilGrids / INEGI / NASA] ----> [APIs / Enriquecimiento Edafico] ----> [Covariables Biofisicas]
                                                                                |
                                                                                v
                                                          [Extraccion de Pheno-Metrics: vPOS, AUC_Llenado]
                                                                                |
                                                                                v
                                                          [Seleccion de Variables: mRMR + Boruta-SHAP]
                                                                                |
                                                                                v
                                                          [GroupKFold Espacial (5 Bloques + Buffer 3.5 km)]
                                                                                |
                                                                                v
                                                          [Stacking Ensemble: ElasticNet + GPR + CatBoost]
                                                                                |
                                                                                v
                                                          [Predicciones de 59 Parcelas + Auditoria SHAP]
```

### 6.1. Reconstruccion Espectral con Whittaker-Eilers
Para mitigar la contaminacion por nubosidad recurrente en el temporal estival, se aplica el filtro de Whittaker-Eilers penalizado ($d=2$), resolviendo:

$$(W + \lambda D^T D) z = W y$$

Donde $W$ es la matriz de pesos basada en `porcentaje_nubosidad`: $w_i = 1.0$ para observaciones despejadas, $w_i = 0.5$ para aerosoles difusos y $w_i = 0.0$ para nubosidad > 20 %, asegurando perfiles continuos e interpolados de forma analitica.

### 6.2. Metricas Fenologicas Sinteticas (*Pheno-Metrics*)
Se derivan rasgos cuantitativos con alta correlacion con la biomasa final:
* **vPOS**: Magnitud maxima de vigor alcanzada en floracion.
* **POS**: Fecha del ano (DOY) de antesis.
* **AUC_Llenado**: Integral temporal bajo la curva del indice desde el pico hasta la senescencia (explica mas del 65 % de la varianza del rendimiento al cuantificar la duracion fotosintetica efectiva durante el llenado de grano).
* **Tasa de Senescencia**: Pendiente de declive post-antesis indicativa de estres por desecacion forzada.

### 6.3. Fusion Espectral Multisenso
* **Sentinel-2 y Landsat 8/9**: Armonizacion mediante coeficientes lineales HLS de NASA/USGS.
* **PlanetScope**: Rama paralela independiente para precision temporal del pico y textura intra-parcelaria (`ndvi_std`).

---

## 7. Estrategia de Modelado de Machine Learning

El diseno completo de los modelos propuestos se encuentra documentado en [propuestas_modelos.md](file:///d:/Dev/Ciencia%20de%20datos/Cebada/src/propuestas_modelos.md). Los puntos estructurales son:

1. **Reduccion Dimensional ($p \gg N$)**:
   * Filtro mRMR (Minimum Redundancy Maximum Relevance) para aislar las 25 variables con mayor informacion mutua con el rendimiento y minima redundancia entre si.
   * Confirmacion estadistica mediante Boruta-SHAP contra variables sombra (*shadow features*, $p < 0.01$), reteniendo entre 10 y 15 predictores biofisicos definitivos.
2. **Validacion Cruzada Espacialmente Bloqueada**:
   * Particion en 5 bloques territoriales mediante `GroupKFold` con zona de amortiguamiento de 3.5 km para evitar fuga de datos espaciales (*spatial data leakage*).
3. **Modelos Evaluados**:
   * **Propuesta 1 (Lineal Regularizado)**: ElasticNetCV / Bayesian Ridge.
   * **Propuesta 2 (Probabilistico No Parametrico)**: Regresion por Procesos Gaussianos (GPR) con kernel Matérn 5/2 y Determinacion Automatica de Relevancia (ARD), proporcionando media predicha e incertidumbre epistemica ($\sigma$).
   * **Propuesta 3 (Arboles de Decision)**: CatBoost Regressor con hiperparámetros estrictamente restringidos (`depth=3`, `l2_leaf_reg=6.0`).
   * **Propuesta 4 (Ensamble Principal Recomendado)**: Stacking Ensemble combinando ElasticNet, GPR-ARD y CatBoost en Nivel 0, integrados mediante un meta-regresor lineal no negativo (RidgeCV con restricciones positivas) en Nivel 1.
4. **Metricas de Aceptacion en Validacion Espacial**:
   * RMSE < 0.45 t/ha.
   * MAE < 0.35 t/ha.
   * $R^2$ > 0.70.
   * MAPE < 10 %.
5. **Auditoria de Coherencia Biologica (XAI con SHAP)**:
   * Validacion de relacion monotona positiva para `AUC_Llenado`.
   * Penalizacion por umbral critico en deficit de presion de vapor (`VPD` > 1.8 kPa en floracion).
   * Contribucion positiva de la capacidad de retencion hidrica (`AWC`) en las zonas deficitarias de Tlaxcala e Hidalgo.
   * Comprobacion de no dependencia exclusiva de coordenadas geograficas puras.

### 7.1. Hipotesis sobre Variables Criticas y Combinacion Optima

Con base en la investigacion agronomica y teledeteccion, se establecen tres hipotesis directrices:
* **Indice Espectral Mas Determinante**: La integral temporal del Indice de Vegetacion Mejorado en llenado de grano (`AUC_Llenado_EVI`) junto con el valor del pico (`vPOS_EVI`). EVI supera a NDVI al no saturarse en doseles densos (> 4.0 t/ha en Puebla) y capturar fielmente el efecto *stay-green* durante la sintesis de almidon.
* **Variable Climatica de Mayor Peso**: El Deficit de Presion de Vapor diurno en floracion y llenado (`VPD_julio_agosto`) en combinacion con dias de temperatura extrema ($T_{max} > 28\text{ }^\circ\text{C}$) y balance hidrico de canicula ($P_{CHIRPS} - ET_0$). El VPD elevado forzo el cierre estomatico y aborto floral en Tlaxcala, marcando la brecha frente a la humedad constante de Puebla.
* **Combinacion Optima de Variables**: Una triada biofisica sinergica (10 a 14 variables) compuesta por:
  1. *Suelo*: Capacidad de Agua Disponible (`AWC_0_30cm`) y presencia de limitantes/tepetates.
  2. *Clima*: Deficit de presion de vapor (`VPD_julio_agosto`) y acumulacion termica (`GDD`).
  3. *Planta*: Integral de llenado (`AUC_Llenado_EVI`), pico de vigor (`vPOS_EVI`) y variabilidad intra-parcelaria (`ndvi_std`).

---


## 8. Referencias Bibliograficas Oficiales

1. Funk, C., Peterson, P., Landsfeld, M., et al. (2015). *The climate hazards infrared precipitation with stations—A new environmental record for monitoring extremes*. Scientific Data, 2, 150066. https://doi.org/10.1038/sdata.2015.66
2. Climate Hazards Center (CHC). (2025). *CHIRTS-ERA5 Data Repository*. University of California, Santa Barbara. https://doi.org/10.15780/G2F08J.
3. Instituto Nacional de Estadistica y Geografia (INEGI). (2025). *Continuo de Elevaciones Mexicano 4.0 (CEM 4.0)*. Aguascalientes, Mexico.
4. ISRIC - World Soil Information. (2025). *SoilGrids v2.0: Global gridded soil information*. Wageningen, Paises Bajos. https://doi.org/10.5194/soil-7-217-2021
5. NASA Langley Research Center. (2025). *NASA Prediction of Worldwide Energy Resources (POWER) Agroclimatology Methodology*. https://power.larc.nasa.gov/
6. Claverie, M., Ju, J., Masek, J. G., et al. (2018). *The Harmonized Landsat and Sentinel-2 (HLS) product*. Remote Sensing of Environment, 219, 145-161. https://doi.org/10.1016/j.rse.2018.09.002
7. Eiler, P. H. C. (2003). *A perfect smoother*. Analytical Chemistry, 75(14), 3631-3636. https://doi.org/10.1021/ac034100m

## Implementación reproducible, experimentos y OpenSpec

El modelo, la aplicación Streamlit y el historial experimental están incorporados en esta rama. La fase de soporte regional completó 42/42 tareas y 68 pruebas. E08 obtiene RMSE principal 0.688 t/ha, pero no es elegible por protección de Puebla en el esquema rotado; la versión vigente se conserva. Los intervalos experimentales permanecen desactivados por cobertura insuficiente.

- [Guía de la solución](docs/solution-guide.md).
- [Resultados de E00–E08 y ambas configuraciones TabPFN](experiments/soporte-regional-20261003/docs/phase-results.md).
- [Historial por ejecución](experiments/soporte-regional-20261003/docs/experiment-history.md).
- [Especificaciones principales](openspec/specs) y [cambio archivado](openspec/changes/archive/2026-10-03-experimentos-trazables-con-soporte-regional/evidence.md).
- [Preparar este checkout y restaurar evidencia](docs/github-checkout.md).

La disponibilidad de etiquetas de otra campaña y de manejo verificable sigue pendiente. Los datos originales de `DataSet/` y la investigación previa se conservan.

## Actualización de experimentos de octubre de 2026

Se incorporan las fases de prioridades predictivas, ampliación CIMMYT, estrés hídrico y señal climática, junto con sus registros y cambios OpenSpec. Véanse [la guía del espacio de trabajo](docs/workspace-readme.md) y [la investigación de variables](docs/investigacion-variables-cebada-2026-10-12.md). Los registros JSON grandes se restauran con `python scripts/restore_github_evidence.py`. Los entornos, dependencias vendorizadas y pesos descargables `.ckpt` se conservan únicamente en el espacio local.
