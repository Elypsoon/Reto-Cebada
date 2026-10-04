# Estrategia óptima de modelado predictivo del rendimiento de cebada maltera para AgroCebada 2026

## Síntesis ejecutiva y diagnóstico del problema

El reto, tal como está planteado, **no es principalmente un problema de elegir “el mejor algoritmo”**. Es un problema de construir una representación agronómica compacta y correcta a partir de decenas de miles de observaciones temporales, evitando tres riesgos que dominan con : **sobreajuste por alta dimensionalidad, fuga espacial y confusión entre región y rendimiento**. Con 138 parcelas de entrenamiento, cualquier pipeline que entregue centenares de variables directamente a XGBoost, LightGBM o Random Forest probablemente producirá una validación aparente excelente y una generalización mucho más débil.

La señal regional del conjunto de entrenamiento es extraordinariamente fuerte: Puebla/Chignahuapan promedia 4.48 t/ha, Hidalgo 3.76 t/ha y Tlaxcala 2.98 t/ha. Esto significa que ESTADO, coordenadas, municipio, suelo, precipitación, elevación y hasta ciertos patrones satelitales pueden actuar como **proxies mutuamente correlacionados de una “identidad regional”**. Esa estructura puede ser real —clima, suelo, manejo, germoplasma—, pero también puede inducir un modelo a memorizar regiones. La literatura de validación espacial demuestra que ignorar esta dependencia conduce a una subestimación sistemática del error predictivo. [\[1\]](https://findanexpert.unimelb.edu.au/scholarlywork/1186691-cross-validation-strategies-for-data-with-temporal--spatial--hierarchical--or-phylogenetic-structure)

La arquitectura que recomiendo para AgroCebada es, por tanto:

| Componente | Recomendación |
| --- | --- |
| Unidad de modelado | Una fila por parcela |
| --- | --- |
| Series satelitales | Convertirlas a **fenometrics y métricas de estrés**, no usar observaciones fecha×índice crudas |
| Fenología | Alinear por **fases fenológicas/GDD**, no solamente por mes calendario |
| Sentinel-2 | Rama propia a 10 m |
| Landsat | Rama propia o HLS como rama secundaria |
| Planet | **Rama independiente**, sin mezclar valores crudos con S2/Landsat |
| Clima | Variables diarias agregadas por fenofase: GDD, lluvia, VPD, radiación, , extremos térmicos |
| Suelo | SoilGrids/OpenLandMap + INEGI; priorizar AWC, textura, SOC, pH y densidad |
| Dimensionalidad final | Aproximadamente 20–40 variables fuertes por modelo, no cientos |
| Selección | Filtro agronómico → redundancia → mRMR/ElasticNet-estabilidad; Boruta-SHAP sólo como análisis complementario |
| Validación primaria | Spatial/Group K-fold de 5 bloques geográficos |
| Validación extrema | Leave-one-state-out Puebla/Hidalgo/Tlaxcala |
| Modelos prioritarios | ElasticNet/Bayesian Ridge + SVR + CatBoost/XGBoost regularizados |
| GPR | Muy interesante si se reduce previamente a variables |
| Ensemble | Convex blend de 2–3 modelos basado **exclusivamente en predicciones out-of-fold espaciales** |
| XAI | SHAP fold-wise + pruebas de congruencia fisiológica |
| Métricas | RMSE y MAE primarias; y MAPE secundarias |

Hay además una oportunidad que considero especialmente importante: **conectar las variables directamente con la identidad fisiológica del rendimiento**. En primera aproximación,

Por ejemplo, espigas/m² × granos/espiga × g de PMG ≈ t/ha. El objetivo de la ingeniería de variables debería ser reconstruir indirectamente esos tres componentes: **capacidad de macollamiento/supervivencia de tallos, establecimiento reproductivo y capacidad de llenado del grano**. La literatura sobre cebada confirma que sequía y temperatura pueden modificar simultáneamente número de tallos/espigas, fertilidad y peso final del grano. [\[2\]](https://hal.science/hal-00886257v1/document)

Un resultado metodológico importante es que los datos de Planet 2025 probablemente sean su **mejor sensor para reconstruir fenología**, especialmente en las parcelas pequeñas, mientras que Sentinel-2 aporta una excelente combinación entre resolución espacial, red-edge y series multianuales; Landsat tiene mucho menor número de píxeles puros en las parcelas más pequeñas. Una parcela de 0.35 ha contiene teóricamente sólo unas cuatro celdas Landsat de 30 m antes de descontar bordes, frente a unas 35 celdas Sentinel-2 de 10 m y cientos de píxeles Planet de aproximadamente 3 m. Por ello, la confiabilidad de una observación debe depender también del **número efectivo de píxeles válidos y de la fracción de borde**, no sólo de porcentaje\_nubosidad.

La estrategia final que considero con mayor probabilidad de generalizar es un **ensamble pequeño entre un modelo lineal regularizado, un boosting fuertemente regularizado y SVR/GPR**, alimentado con 20–40 variables de alta calidad. Un ensamble de baja complejidad suele ser preferible aquí a un stacking profundo porque sólo existen 138 etiquetas; la complejidad debe invertirse en la representación agronómica, no en el meta-modelo.

## Fenología, formación del rendimiento y ventanas críticas

La escala Zadoks proporciona una forma mucho más robusta de organizar la cebada que los meses del calendario. En un ciclo Primavera–Verano de abril–octubre en el altiplano mexicano, las fechas absolutas variarán por fecha de siembra, cultivar, humedad y temperatura; por ello no aconsejo codificar, por ejemplo, “julio = encañado” de forma rígida. El modelo debe inferir o aproximar las etapas individualmente mediante GDD y las curvas Planet/Sentinel-2. Los modelos de cultivo como CERES-Barley simulan precisamente el desarrollo mediante acumulación térmica y estados fenológicos, no simplemente mediante fecha juliana. [\[3\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.655406/full?utm_source=chatgpt.com)

| Fase | Zadoks aproximado | Proceso fisiológico dominante | Variables que conviene modelar |
| --- | --- | --- | --- |
| Siembra–emergencia | Z00–Z19 | Germinación, establecimiento | humedad inicial, precipitación, GDD, NDVI basal |
| --- | --- | --- | --- |
| Macollamiento | Z20–Z29 | Formación de tallos | LAI/NDVI ascendente, tasa de crecimiento, lluvia/AWC |
| Encañado | Z30–Z39 | Elongación, crecimiento rápido, desarrollo de espiga | pendiente NDVI/LAI, radiación, VPD, agua |
| Embuche–espigado | Z40–Z59 | Meiosis, supervivencia floral, emergencia de espiga | Tmax, Tmin, VPD, AWC, NDVI/LAI máximo |
| Antesis | Z60–Z69 | Polinización/fertilización | calor, helada, déficit hídrico |
| Llenado | Z70–Z89 | Acumulación de almidón y peso de grano | radiación, temperatura, agua, senescencia |
| Madurez | Z90+ | Pérdida de humedad / cosecha | velocidad de senescencia, EOS |

En cebada, la antesis está muy próxima al espigado y puede iniciarse incluso antes de que la espiga haya emergido completamente, característica que hace particularmente vulnerable el período de embuche–espigado. Experimentalmente se ha observado que temperaturas elevadas desde iniciación de espiga hasta antesis reducen número de espiguillas y granos, mientras que calor durante llenado reduce peso y calidad del grano. [\[4\]](https://pmc.ncbi.nlm.nih.gov/articles/PMC11314375/)

**Número de espigas por metro cuadrado.** Se origina en el macollamiento, pero el número final de espigas productivas depende tanto de cuántos macollos se forman como de cuántos sobreviven hasta encañado/embuche. Por ello, una señal vigorosa de NDVI/LAI durante macollamiento que posteriormente colapsa no equivale necesariamente a un alto número final de espigas. La sequía durante crecimiento temprano y elongación puede reducir macollos, biomasa y posteriormente espigas. [\[5\]](https://link.springer.com/article/10.1186/s12870-025-07504-8)

**Número de granos por espiga.** El potencial empieza a determinarse desde iniciación de la espiga y desarrollo de espiguillas, pero el componente que interesa al rendimiento queda definido esencialmente durante el período crítico preantesis–antesis por supervivencia de floretes, meiosis y fertilización. En cebada se ha documentado sensibilidad térmica desde semanas antes del espigado; temperaturas superiores a aproximadamente 20 °C durante desarrollo reproductivo aceleran la fenología y pueden reducir espiguillas/granos. [\[6\]](https://pmc.ncbi.nlm.nih.gov/articles/PMC11314375/)

**Peso de mil granos.** Aunque el potencial de tamaño de grano tiene determinantes preantesis, el PMG realizado se construye predominantemente después de la fecundación, durante llenado. La combinación peligrosa es **alta temperatura + alto VPD + agotamiento de agua del suelo**, porque acelera senescencia y acorta el período efectivo de llenado. Experimentos de cebada muestran que temperaturas sostenidas superiores a 30 °C durante floración/desarrollo de grano constituyen estrés crónico, mientras que exposiciones por encima de 35 °C se consideran eventos agudos de calor. [\[7\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.858652/full)

### Temperatura térmica efectiva

Aquí es importante evitar una falsa precisión. **No existe una única tripleta universal válida para todas las variedades y todas las fases de cebada**. En CERES-Barley se utiliza y la tasa de desarrollo aumenta hasta un óptimo cercano a ; por encima del óptimo, la formulación del desarrollo fenológico puede mantener la tasa máxima en lugar de imponer inmediatamente una reducción. En otras palabras, la “temperatura máxima cardinal” depende del modelo y no debe confundirse con la temperatura de daño térmico. [\[8\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.655406/full?utm_source=chatgpt.com)

Para AgroCebada recomiendo comenzar con:

y un GDD diario simple:

donde

Así se impide que un día extremadamente caliente aporte “desarrollo beneficioso” ilimitado. El calor por encima de 26–30 °C debe entrar **por variables de estrés independientes**, no como GDD extra. CERES-Barley y estudios de respuesta térmica apoyan el uso de como base y un óptimo cercano a 26 °C. [\[9\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.655406/full?utm_source=chatgpt.com)

Por tanto, mi recomendación práctica para el reto no es imponer una dudosa tripleta 0/26/35 como si fuese una constante fisiológica. Sería:

con **26 °C como techo de acumulación de GDD**, y variables separadas:

calculadas dentro de booting\_anthesis y grain\_fill. La evidencia experimental distingue estrés crónico alrededor de y daño agudo alrededor de durante floración/llenado. [\[10\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.858652/full)

### Estrés hídrico

No aconsejo establecer un umbral de “X milímetros de lluvia” porque el mismo evento tiene efectos distintos según textura, profundidad radical, ET atmosférica y humedad precedente. Una formulación físicamente mejor es el balance de agua disponible de FAO-56:

donde es agua total disponible en mm, profundidad de raíces en metros, humedad a capacidad de campo y humedad al punto de marchitez.

El agua fácilmente aprovechable es

y cuando el agotamiento excede , puede emplearse:

Para el modelo, más que intentar reconstruir un balance perfectamente mecanístico, conviene obtener indicadores como water\_deficit\_boot, water\_deficit\_anthesis, water\_deficit\_fill, número de días y déficit acumulado . La cebada puede tolerar déficit vegetativo moderado, pero sequía alrededor de elongación, espigado/antesis e inicio del desarrollo del grano afecta simultáneamente espigas, granos y peso individual. [\[11\]](https://hal.science/hal-00886257v1/document)

### Heladas y calor

La mayor susceptibilidad a helada ocurre desde embuche hasta floración. Fuentes agronómicas de extensión reportan daño reproductivo en cebada alrededor de , aproximadamente , especialmente porque la cebada puede florecer mientras la espiga aún está parcialmente protegida por la vaina. [\[12\]](https://www.ndsu.edu/agriculture/ag-hub/ag-topics/crop-production/crops/barley/small-grain-damage-frost-dependent-many-factors)

Para los Valles Altos construiría, por fenofase:

No deben interpretarse como fronteras absolutas: temperatura del dosel, duración del evento, viento, humedad y topografía cambian mucho el daño real. Las parcelas bajas o depresiones pueden presentar temperaturas de dosel inferiores a la estación meteorológica.

El riesgo agronómico esperado puede resumirse así:

| Ventana | Amenaza | Componente afectado |
| --- | --- | --- |
| Emergencia–macollamiento | sequía | establecimiento y macollos |
| --- | --- | --- |
| Encañado | sequía / calor | biomasa y supervivencia de tallos |
| Embuche–antesis | **helada, calor, VPD alto** | fertilidad y granos/espiga |
| Antesis–grano lechoso | sequía + calor | número final y comienzo de llenado |
| Grano lechoso–pastoso | calor / déficit hídrico | PMG |
| Madurez | lluvia excesiva | secado, acame, enfermedad/calidad |

La ventaja de organizar las variables de esta forma es que SHAP podrá posteriormente responder preguntas fisiológicas: “¿el modelo penaliza realmente tres días >32 °C durante llenado?” en lugar de la mucho menos interpretable “¿julio Tmax tuvo importancia?”.

## Disparidad regional, agroecología y señal climática de 2025

La diferencia Puebla–Hidalgo–Tlaxcala debe tratarse como una **hipótesis causal por descomponer**, no como una etiqueta que el modelo deba aprender ciegamente. Los Llanos de Apan constituyen una región histórica de producción de cebada maltera y el cultivo tiene gran importancia económica en Hidalgo; documentación gubernamental mexicana identifica a Apan como una zona central de esta cadena productiva. [\[13\]](https://www.gob.mx/agricultura/hidalgo/articulos/cebada-maltera-en-la-region-de-apan-hidalgo?idiom=es&utm_source=chatgpt.com)

A partir de los datos del reto, la diferencia entre Chignahuapan y Calpulalpan es de aproximadamente **1.50 t/ha**, casi 50 % del rendimiento medio de Tlaxcala. Es demasiado grande para asumir de entrada que proviene de una sola variable climática. En términos conceptuales,

La producción mexicana de cebada también está expuesta a enfermedades como royas, de modo que una temporada húmeda puede simultáneamente favorecer crecimiento vegetativo y aumentar presión de enfermedad; por eso “más lluvia = más rendimiento” no debe imponerse como una relación monotónica. [\[14\]](https://www.scielo.org.mx/article_plus.php?lng=es&pid=S2007-09342016000100159&tlng=es&utm_source=chatgpt.com)

**Chignahuapan.** Bajo el contexto geográfico descrito para el reto —zona elevada asociada a Sierra Norte y mayor influencia orográfica— la hipótesis principal es un sistema con **menor probabilidad de déficit hídrico terminal**, mayor persistencia de área foliar y potencialmente mayor disponibilidad de agua durante encañado–llenado. Si los suelos además presentan mayor almacenamiento efectivo, el cultivo puede mantener LAI y fotosíntesis durante el período crítico. Pero la misma humedad puede elevar nubosidad, reducir radiación efectiva o favorecer enfermedades; esas relaciones deben verificarse, no asumirse.

**Apan/Singuilucan y el corredor de Hidalgo.** Es esperable mayor exposición de los cultivos a la combinación de viento, demanda atmosférica y variabilidad de lluvias característica de una planicie alta. Agronómicamente, un ambiente así puede sostener rendimientos altos cuando lluvia y fertilidad coinciden con las ventanas críticas, pero castigar con rapidez la supervivencia de macollos y el llenado bajo déficit hídrico. La gran dispersión de Hidalgo en el conjunto de entrenamiento —0.78 t/ha— es consistente con una población ambiental y de manejo más heterogénea que Chignahuapan o Tlaxcala, aunque esa interpretación debe validarse con los covariables.

**Calpulalpan/Nanacamilpa.** Su promedio de 2.98 t/ha y desviación de sólo 0.38 t/ha sugiere algo más que “mal clima”: podría existir un techo relativamente uniforme asociado a manejo, germoplasma, disponibilidad de N, suelo, fecha de siembra o incluso al procedimiento con el que se reportó el rendimiento. Antes de modelar, conviene comprobar el número de valores únicos y el redondeo de RENDIMIENTO\_T\_HA; un grado de cuantización distinto entre estados puede aparecer engañosamente como una señal biológica.

Un diagnóstico muy revelador será comparar, por estado, las curvas promedio de 2025:

y particularmente separar cuatro mecanismos:

Si Puebla no sólo tiene NDVI máximo superior, sino además mayor AUC posespigado y senescencia más lenta, existiría evidencia remota de una ventaja en **duración fotosintética durante llenado**. Si el pico es similar pero Tlaxcala cae antes, la explicación cambiaría hacia estrés terminal. Los estudios de fenología satelital de cereales muestran que incorporar fechas, amplitudes e integrales de la curva mejora la relación con rendimiento frente al uso de una única imagen. [\[15\]](https://www.mdpi.com/1424-8220/21/4/1406)

### Qué puede afirmarse sobre 2025

Sería metodológicamente incorrecto declarar, sin procesar sus rasters o una serie meteorológica local, que “Calpulalpan sufrió X % de sequía” o “Chignahuapan recibió Y mm más que lo normal”. El hecho de que 2025 ocurriera en un contexto global excepcionalmente cálido —la OMM posteriormente confirmó 2025 entre los años más cálidos observados— **no demuestra por sí solo una anomalía con el mismo signo en cada municipio del altiplano**. [\[16\]](https://wmo.int/es/media/news/la-organizacion-meteorologica-mundial-advierte-de-la-creciente-probabilidad-de-formacion-de-un)

Sus propios datos permiten responderlo de forma mucho más rigurosa, pero hay que extender el período climatológico. **2022–2024 no constituye una climatología suficiente.** Recomiendo descargar CHIRPS/CHIRTS o ERA5-Land para 1991–2020 y calcular, para cada celda/parcela:

y

Para precipitación, es mejor todavía trabajar diariamente y calcular:

además de lluvia acumulada por fenofase. Así se distingue una temporada con precipitación total “normal” pero distribuida en pocos aguaceros de otra con lluvias agronómicamente útiles y regulares.

El diagnóstico que recomiendo ejecutar antes de entrenar el modelo es:

| Región | Variables a comparar 2025 vs. climatología |
| --- | --- |
| Chignahuapan | lluvia acumulada encañado–llenado, CDD, radiación, VPD, Tmax >30 |
| --- | --- |
| Apan/Singuilucan | CDD, VPD, , heladas tempranas/tardías, lluvia preantesis |
| Calpulalpan | déficit hídrico reproductivo, CDD, Tmin extremas, senescencia Planet |
| Todas | GDD, fecha de pico NDVI, AUC pospico, Tmax >30/35, Tmin <0/−2 |

Finalmente, la explicación regional debe comprobarse mediante una **descomposición estadística**. Entrenaría sucesivamente modelos con: sólo región; región+topografía; +suelo; +clima; +satélite. Si el RMSE cae fuertemente al incorporar AWC y estrés hídrico y simultáneamente disminuye la importancia SHAP de ESTADO, entonces se habrá reemplazado un proxy administrativo por mecanismos agroecológicos reales.

## Datos externos públicos e integración geoespacial

### Suelo y edafología

**SoilGrids** es probablemente la incorporación externa con mayor relación beneficio/costo. ISRIC ofrece predicciones globales de propiedades del suelo a aproximadamente 250 m y seis profundidades estándar: 0–5, 5–15, 15–30, 30–60, 60–100 y 100–200 cm. Incluye arcilla, arena, limo, SOC, pH, densidad aparente, CEC, N y variables de contenido de agua, además de cuantiles de incertidumbre. [\[17\]](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs.html?utm_source=chatgpt.com)

| Fuente | Resolución | Variables recomendadas | Acceso |
| --- | --- | --- | --- |
| SoilGrids/ISRIC | 250 m; 6 profundidades | clay, sand, silt, SOC, pH, bulk density, CEC, water content | WCS, WebDAV, GEE |
| --- | --- | --- | --- |
| OpenLandMap | típicamente 250 m | textura, SOC, pH, bulk density, agua a tensiones especificadas | Google Earth Engine |
| INEGI Edafología Serie II | 1:250 000 | grupo/unidad de suelo, textura y fases edáficas | vectorial nacional |
| CHIRPS | 0.05° | precipitación diaria/mensual histórica | GeoTIFF/NetCDF |
| NASA POWER | rejilla global, dependiente del parámetro | radiación, T, RH/dew point, viento, P | REST JSON/CSV/NetCDF |
| ERA5-Land | 0.1° distribuido; ~9 km nativo | T, Td, lluvia, radiación, viento, suelo, ET | CDS API, GRIB/NetCDF |
| SMN/CONAGUA | estaciones | T, RH, radiación, viento, presión, lluvia | lista/KMZ/red de estaciones |
| SIAP | municipio/año | superficie, producción, rendimiento, modalidad | portal de cierre agrícola |

SoilGrids publica servicios WMS/WCS en https://maps.isric.org y descargas en https://files.isric.org/soilgrids/latest/data/; ISRIC mantiene además documentación y ejemplos para Google Earth Engine. [\[18\]](https://docs.isric.org/globaldata/soilgrids/wms_from_qgis_arcmap.html?utm_source=chatgpt.com)

Una consulta WCS puede construirse conceptualmente como:

https://maps.isric.org/mapserv?
map=/map/clay.map&
SERVICE=WCS&
VERSION=2.0.1&
REQUEST=GetCoverage&
COVERAGEID=clay\_0-5cm\_mean&
FORMAT=image/tiff&
SUBSET=long(-98.613,-98.1967)&
SUBSET=lat(19.5238,19.9844)

Conviene comprobar DescribeCoverage antes de automatizar porque los identificadores exactos dependen de propiedad, profundidad y estadístico. La documentación WCS oficial muestra esta estructura de cobertura. [\[19\]](https://docs.isric.org/globaldata/soilgrids/wcs.html?utm_source=chatgpt.com)

Para Google Earth Engine, la documentación de ISRIC proporciona los scripts de exportación; el catálogo SoilGrids contiene las propiedades y profundidades correspondientes. [\[20\]](https://docs.isric.org/globaldata/soilgrids/access_on_gee.html?utm_source=chatgpt.com)

Para agua disponible, las capas de contenido volumétrico permiten aproximar:

donde es el espesor de capa en mm. Sumando:

SoilGrids ofrece contenidos de agua a varias tensiones (wv0033, wv1500, etc.), por lo que puede construirse AWC directamente después de aplicar los factores de escala indicados en la documentación de ISRIC. [\[21\]](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html?utm_source=chatgpt.com)

Yo extraería para cada parcela:

más AWC\_0\_60 × precip\_fill y AWC\_0\_60 × VPD\_fill. Los **interacciones suelo×clima** son probablemente más útiles que la textura por sí sola.

OpenLandMap también es accesible mediante Earth Engine. El catálogo contiene capas nominalmente a ~250 m; por ejemplo, la clasificación de textura USDA puede consultarse mediante:

ee.Image("OpenLandMap/SOL/SOL\_TEXTURE-CLASS\_USDA-TT\_M/v02")

y el catálogo incluye productos de arcilla, arena, densidad aparente, SOC, pH y contenido de agua. [\[22\]](https://developers.google.com/earth-engine/datasets/catalog/OpenLandMap_SOL_SOL_TEXTURE-CLASS_USDA-TT_M_v02?utm_source=chatgpt.com)

No aconsejo duplicar SoilGrids y OpenLandMap indiscriminadamente. Extraiga ambas fuentes, compare correlaciones y conserve la de mayor consistencia local, o use el desacuerdo entre productos como indicador de incertidumbre.

Para México, la capa nacional que pude verificar oficialmente es **Conjunto de Datos Vectorial Edafológico, escala 1:250 000, Serie II, Continuo Nacional** de INEGI. INEGI ofrece la ficha nacional y CONABIO documenta cobertura para las 32 entidades. [\[23\]](https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551131916)

Ficha oficial:

https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551131916

Una precisión importante: **no asumiría que existe una “Serie IV de Edafología” equivalente a las series de Uso del Suelo y Vegetación sin verificar la ficha oficial**. La referencia nacional edafológica que pude confirmar es Serie II. Para el reto, descargue el continuo nacional, recórtelo con la envolvente y haga spatial join de cada parcela con la unidad edáfica dominante.

Con , no conviene generar decenas de one-hot de unidades taxonómicas raras. Agrupe en variables agronómicas interpretables: suelo dominante, textura, presencia de fase física/química y, preferentemente, complemente con las variables continuas SoilGrids.

### Radiación, VPD y evapotranspiración

NASA POWER ofrece una API REST diaria para datos solares y meteorológicos. La API permite consultas puntuales, entrega JSON/CSV/NetCDF y permite solicitar múltiples parámetros; la documentación advierte que se trata de productos de rejilla global, por lo que un punto no equivale a una estación dentro de la parcela. [\[24\]](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)

Ejemplo:

https://power.larc.nasa.gov/api/temporal/daily/point
?parameters=ALLSKY\_SFC\_SW\_DWN,T2M,T2M\_MAX,T2M\_MIN,RH2M,WS2M,PS,PRECTOTCORR
&community=AG
&longitude=-98.45
&latitude=19.71
&start=20250401
&end=20251031
&format=JSON

Documentación:

https://power.larc.nasa.gov/docs/services/api/temporal/daily/

API:

https://power.larc.nasa.gov/api/temporal/daily/point

POWER mantiene un catálogo específico para la comunidad Agroclimatology y dispone de datos diarios desde principios de los años ochenta hasta fechas próximas al presente. [\[25\]](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)

No asumiría que VPD o existen siempre como parámetros nativos con el nombre que uno espera en la versión actual de POWER. Es más reproducible descargar los componentes y calcularlos.

Para presión de vapor de saturación:

y

Si se dispone de punto de rocío:

Para evapotranspiración de referencia FAO-56:

En POWER, ALLSKY\_SFC\_SW\_DWN proporciona irradiación solar descendente; hay que respetar la unidad indicada por el servicio y convertir a MJ m d cuando se use FAO-56. La documentación de POWER permite solicitar esos parámetros directamente en la API diaria. [\[26\]](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)

NASA POWER es excelente para **contexto y extremos atmosféricos**, pero su rejilla es demasiado gruesa para explicar diferencias entre parcelas vecinas. No duplique una misma celda climatológica y la trate como cientos de mediciones independientes.

ERA5-Land es más potente si se necesita el balance hidroclimático completo. Copernicus lo distribuye a 0.1° sobre una rejilla regular, con resolución nativa de aproximadamente 9 km, frecuencia horaria y cobertura desde 1950 hasta casi el presente. También incorpora cuatro capas de suelo de 0–7, 7–28, 28–100 y 100–289 cm. [\[27\]](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview)

Dataset:

https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land

Variables que descargaría:

2m\_temperature
2m\_dewpoint\_temperature
total\_precipitation
surface\_solar\_radiation\_downwards
10m\_u\_component\_of\_wind
10m\_v\_component\_of\_wind
surface\_pressure
evaporation
potential\_evaporation
volumetric\_soil\_water\_layer\_1
volumetric\_soil\_water\_layer\_2

El acceso se automatiza con cdsapi; el producto oficial admite GRIB y/o NetCDF según la petición. [\[27\]](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview)

Mi jerarquía sería: **CHIRPS para precipitación**, ERA5-Land o estación para temperatura/humedad/radiación/viento, y NASA POWER como alternativa o variable de comprobación. No agregaría los tres como predictores duplicados de temperatura.

### Estaciones SMN/CONAGUA

El portal oficial del Servicio Meteorológico Nacional ofrece un **KMZ y una lista descargable de EMAs**, y especifica que los sensores básicos incluyen velocidad/dirección del viento, presión, temperatura, humedad relativa, radiación solar y precipitación. [\[28\]](https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s)

Portal:

https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s

Para Chignahuapan, Calpulalpan, Apan y Tulancingo, no recomiendo codificar de memoria un nombre de estación: **la condición operativa y la red pueden cambiar**. El procedimiento reproducible es descargar el KMZ/lista vigente, cargarlo como puntos, proyectar parcelas a UTM 14N y seleccionar estaciones activas por distancia y diferencia altitudinal. La página de normales climatológicas del SMN, por ejemplo, registra estaciones dentro del municipio de Calpulalpan, pero una estación climatológica convencional no debe confundirse automáticamente con una EMA activa. [\[29\]](https://smn.conagua.gob.mx/es/climatologia/informacion-climatologica/normales-climatologicas-por-estado?estado=tlax)

### SIAP como prior agronómico

El producto que interesa es **Cierre de la Producción Agrícola** de SIAP/SADER:

https://nube.siap.gob.mx/cierre\_agricola/

El portal debe consultarse por:

Años: 2018–2024
Cultivo: Cebada grano
Estados: Puebla, Hidalgo, Tlaxcala
Municipio:
Chignahuapan
Singuilucan
Almoloya
Cuautepec de Hinojosa
Emiliano Zapata
Tepeapulco
Apan
Calpulalpan
Nanacamilpa de Mariano Arista
Modalidad:
Temporal
Riego
Ciclo:
Primavera–Verano

La importancia de separar temporal y riego es alta: mezclar ambos generaría un prior que no representa el régimen hídrico de las parcelas. Fuentes oficiales mexicanas confirman la importancia de la cebada maltera en el corredor de Apan/Hidalgo y el uso de estadísticas oficiales de superficie y producción para caracterizar esa región. [\[13\]](https://www.gob.mx/agricultura/hidalgo/articulos/cebada-maltera-en-la-region-de-apan-hidalgo?idiom=es&utm_source=chatgpt.com)

No incluyo aquí una tabla numérica 2018–2024 porque el portal SIAP no fue accesible mediante el crawler de esta investigación y sería incorrecto inventar cifras. El uso correcto de esos datos en ML sería construir, **únicamente con 2018–2024**:

además de mediana, pendiente temporal y diferencia respecto a la media estatal. No utilice datos SIAP 2025: un agregado municipal del mismo año objetivo constituiría una fuente potencial de leakage.

Tampoco impondría los rendimientos SIAP como límites rígidos. “Cebada grano” no necesariamente representa exclusivamente cebada maltera con el mismo manejo que el reto. Úselos como **covariable histórica o prior débil**, no como verdad parcela por parcela.

## Ingeniería de variables, nubes, fenometría y fusión de sensores

El error más costoso sería transformar los 107,666 registros básicos y los 47,804 Planet en centenares de variables del tipo NDVI\_julio\_03, NDVI\_julio\_08, NDVI\_julio\_15, etc. Con 138 etiquetas, eso produciría una matriz extremadamente inestable.

La meta debe ser:

### Filtrado y suavizado

Primero debe realizarse **QA físico del píxel**, luego detección de outliers y finalmente reconstrucción temporal. No suavice primero y filtre nubes después.

Para Sentinel-2 conviene emplear máscara de nubes/sombras a nivel de píxel —SCL y/o probabilidad de nube—; para Landsat, QA\_PIXEL/CFMask; para Planet, su máscara de calidad UDM/UDM2 cuando esté disponible. El porcentaje de nubosidad de la escena o de la parcela debe conservarse además como peso de confianza, pero no sustituye la máscara pixel-wise. La armonización HLS de NASA también integra corrección atmosférica, máscara de nubes/sombras, registro espacial, normalización BRDF y ajuste del bandpass espectral precisamente porque una simple concatenación de Landsat y Sentinel no garantiza equivalencia radiométrica. [\[30\]](https://modis.gsfc.nasa.gov/sci_team/pubs/abstract_new.php?id=27008)

Después del QA, usaría un detector robusto tipo Hampel/MAD local:

y marcaría como potencial outlier observaciones con desviación excesiva respecto a la mediana temporal local, especialmente caídas instantáneas de NDVI incompatibles con observaciones inmediatamente anterior/posterior.

Entre los métodos de reconstrucción evaluados en la literatura destacan Savitzky–Golay, Whittaker, funciones gaussianas/asimétricas, doble logística y Fourier. Comparaciones sistemáticas muestran que no existe un único ganador universal; el método óptimo depende de frecuencia de observación, ruido, gaps y forma de la temporada. [\[31\]](https://www.sciencedirect.com/science/article/abs/pii/S0034425715302443)

Para este reto priorizaría **Whittaker ponderado**, cuya formulación es:

Los pesos permiten utilizar directamente nubosidad, fracción de píxeles válidos y calidad del sensor. Esto es una ventaja enorme en junio–septiembre.

Orden recomendado:

| Método | Papel en AgroCebada |
| --- | --- |
| Whittaker ponderado | **Primario** |
| --- | --- |
| Savitzky–Golay | Sensibilidad/benchmark sobre series regulares |
| Doble logística Beck | Excelente cuando existe una temporada unimodal clara |
| Armónicos/Fourier | Útil para series largas 2022–2025; menor prioridad para evento agrícola corto |
| Interpolación lineal | Sólo gaps pequeños |
| Spline cúbico | Con cautela; puede crear sobreoscilaciones |

La doble logística de Beck es especialmente útil para estimar inicio/fin de temporada mediante funciones suaves de green-up y senescencia. [\[32\]](https://www.sciencedirect.com/science/article/abs/pii/S0034425705003640)

En Python:

scipy.signal.savgol\_filter -> Savitzky–Golay
scipy.optimize.curve\_fit -> doble logística
pybaselines -> Whittaker / penalized smoothers
statsmodels / numpy.linalg -> regresión armónica
scipy.interpolate -> interpolación/splines

Una alternativa muy madura es TIMESAT; si se acepta una etapa fuera de Python, continúa siendo referencia en extracción fenológica. Para reproducibilidad completa en Python, Whittaker + scipy.optimize es suficiente.

### Fenometrics que deben extraerse

Sea una curva suavizada de NDVI, EVI, LAI o NDWI.

Defina:

Entonces el inicio de temporada puede definirse, por ejemplo, al 20 % de amplitud:

Análogamente:

y:

La integral temporal:

o discretamente:

Las variables que extraería por índice son:

| Familia | Métrica |
| --- | --- |
| Nivel | máximo, P90, mediana |
| --- | --- |
| Tiempo | SOS, fecha pico, EOS, duración |
| Amplitud | máximo − baseline |
| Crecimiento | pendiente green-up |
| Producción integrada | AUC total |
| Reproducción | AUC pre-pico / alrededor del pico |
| Llenado | **AUC pospico** |
| Senescencia | pendiente pospico |
| Estrés | caídas abruptas, mínimos NDWI, máximos MSI/NDDI |
| Calidad | número observaciones, gap máximo, nube media |

La literatura de predicción de cereal indica que métricas fenológicas, integrales y señal alrededor de espigado/llenado suelen contener más información de rendimiento que una observación NDVI única. [\[15\]](https://www.mdpi.com/1424-8220/21/4/1406)

Especialmente importantes para cebada:

y

Una senescencia pospico muy rápida debería, en igualdad de condiciones, asociarse a menor período de llenado y menor PMG. El calor durante llenado puede acortar fuertemente esa duración. [\[10\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.858652/full)

Para NDWI/MSI/NDDI no me limitaría al valor máximo. Más útiles podrían resultar:

NDWI\_min\_boot\_anthesis
NDWI\_mean\_grainfill
NDWI\_drop\_peak\_to\_fill
MSI\_max\_grainfill
NDDI\_max\_boot
stress\_duration\_NDWI

porque capturan **momento del estrés**, no sólo intensidad.

### Integración climática por fenofase

Después de estimar SOS/pico/EOS, usaría las fechas satelitales para construir ventanas dinámicas. Por ejemplo:

vegetative = SOS → peak - 15 d
reproductive = peak - 15 d → peak + 10 d
grain\_fill = peak + 10 d → EOS

y simultáneamente una versión basada en GDD. La intersección entre ambas aumenta robustez cuando no se dispone de fecha de siembra.

Dentro de cada ventana:

Esto convierte clima diario en aproximadamente 10–20 predictores fisiológicamente significativos.

### Fusión Sentinel-2, Landsat y Planet

No recomendaría concatenar directamente:

Planet\_NDVI = 0.78
Sentinel\_NDVI = 0.78
Landsat\_NDVI = 0.78

como si representaran mediciones idénticas. Las respuestas espectrales, PSF, resolución espacial, correcciones atmosféricas, geometría y mezcla de píxeles son distintas. NASA tuvo que desarrollar HLS específicamente para resolver parte de esos problemas entre Landsat y Sentinel-2 mediante co-registro, normalización BRDF y ajuste de banda espectral. [\[33\]](https://modis.gsfc.nasa.gov/sci_team/pubs/abstract_new.php?id=27008)

Claverie et al. documentan HLS como una armonización explícita de OLI y MSI; no incluye Planet. DOI: **10.1016/j.rse.2018.09.002**. [\[34\]](https://www.sciencedirect.com/science/article/pii/S0034425718304139)

Mi arquitectura sería:

Pero cada contiene **fenometrics propias**, no las observaciones brutas.

Por ejemplo:

planet\_ndvi\_peak
planet\_ndvi\_auc
planet\_lai\_auc\_fill
planet\_senescence\_rate

s2\_ndvi\_peak
s2\_evi\_auc
s2\_ndwi\_fill

landsat\_ndvi\_peak
landsat\_msi\_fill

Esto constituye una **fusión tardía de rasgos** y es, para , mucho más segura.

Z-score por sensor:

puede ayudar con anomalías relativas, pero **no armoniza físicamente** sensores. Elimina offset y escala lineal, pero no corrige diferencias no lineales ni mezcla espacial.

Una opción mejor cuando existen observaciones casi simultáneas es estimar:

con pares de fechas separadas, por ejemplo, días y baja nubosidad. Esta calibración debe hacerse por índice y comprobar residuos.

Para Sentinel-2/Landsat puede probarse HLS, pero hay una decisión específica del reto: HLS a 30 m mejora consistencia temporal a costa de perder la ventaja espacial de Sentinel-2 en parcelas muy pequeñas. Por tanto, mantendría **S2 a 10 m como rama primaria** y usaría HLS como experimento secundario, particularmente en parcelas grandes. HLS está diseñado precisamente para producir series temporalmente coherentes entre OLI y MSI. [\[35\]](https://modis.gsfc.nasa.gov/sci_team/pubs/abstract_new.php?id=27008)

### Efecto de tamaño de parcela

Debe añadirse:

y, para cada sensor:

Idealmente se elimina un buffer interior para reducir contaminación de bordes. Para Planet pueden bastar pocos metros; para Sentinel-2 podría probarse 10 m; en Landsat un buffer de 30 m destruiría prácticamente las parcelas pequeñas, por lo que conviene, en esos casos, usar todos los píxeles con pesos por pureza o aceptar que Landsat aporta una señal regional, no estrictamente intraparcelaria.

Además del promedio zonal, conservaría:

o al menos \_promedio + \_std. La heterogeneidad intraparcelaria puede ser una señal productiva real, pero cuatro estadísticas de cada índice×fecha crearían nuevamente alta dimensionalidad; deben condensarse temporalmente.

## Modelado, reducción dimensional y validación espacial

### Cómo resolver

El primer paso de selección no debe ser Boruta. Debe ser la **biología**.

Partiría de unas 60–80 variables candidatas distribuidas aproximadamente así:

| Familia | Presupuesto inicial |
| --- | --- |
| Fenología Planet | 12–15 |
| --- | --- |
| Sentinel-2 | 10–12 |
| Landsat/HLS | 5–8 |
| Clima/GDD/estrés | 12–15 |
| Suelo | 8–10 |
| Topografía/geometría | 5–7 |
| Historia 2022–2024 | 5–8 |
| SIAP | 3–5 |

Posteriormente:

**Filtrado de calidad.** Eliminar variables casi constantes, con demasiados faltantes o sin significado agronómico.

**Redundancia.** Si

conservar sólo una de las variables salvo que exista una razón fisiológica para mantener ambas. Para relaciones no lineales puede usarse Spearman.

**mRMR.** Maximum Relevance Minimum Redundancy intenta maximizar información respecto a y minimizar redundancia:

Es particularmente útil aquí para reducir 60–80 variables a, por ejemplo, 25–40. El método clásico fue formalizado por Peng et al., DOI **10.1109/TPAMI.2005.159**.

**ElasticNet.** Para regresión:

El componente L1 selecciona y el L2 estabiliza predictores altamente correlacionados, precisamente la situación esperable entre NDVI, EVI, LAI y múltiples métricas climáticas. DOI de Zou & Hastie: **10.1111/j.1467-9868.2005.00503.x**.

No elegiría variables porque su coeficiente sea distinto de cero una sola vez. Calcularía **frecuencia de selección en las particiones espaciales**:

Una variable seleccionada en 5/5 folds es mucho más confiable que una elegida una sola vez.

Boruta/Boruta-SHAP es útil como auditoría no lineal, pero con 138 muestras y muchos predictores correlacionados puede ser inestable. Lo utilizaría únicamente **dentro del fold de entrenamiento**, nunca una vez sobre los 138 datos antes de validación. El Boruta original: DOI **10.18637/jss.v036.i11**.

La regla fundamental es:

Si se hace mRMR o ElasticNet sobre los 138 ejemplos antes de CV, la validación deja de ser independiente.

### Modelos recomendados

| Modelo | Idoneidad con N=138 | Comentario |
| --- | --- | --- |
| ElasticNet | **Muy alta** | benchmark obligatorio; estable e interpretable |
| --- | --- | --- |
| Bayesian Ridge | Alta | excelente referencia para pocos datos |
| SVR-RBF | **Muy alta** | buena flexibilidad con muestras pequeñas |
| GPR | Alta tras reducción | incertidumbre natural; sensible a escala y dimensión |
| CatBoost | **Alta** | árboles poco profundos y fuerte regularización |
| XGBoost | Alta | muy competitivo si profundidad 2–4 |
| Random Forest | Media–alta | robusto baseline, pero puede diluir señal con muchos rasgos |
| LightGBM | Media | muy potente, pero fácil de sobreajustar con 138 filas |
| Stacking profundo | Baja | demasiados grados de libertad |
| Blend de 2–3 modelos | **Muy alta** | preferible al stacking complejo |

**ElasticNet/Bayesian Ridge** deben ser benchmarks obligatorios. Si CatBoost aparentemente supera por 30–40 % a ElasticNet en un K-fold aleatorio pero sólo marginalmente en CV espacial, sospecharía que aprovechó proxies geográficos.

Para XGBoost probaría algo como:

max\_depth: 2–4
learning\_rate: 0.01–0.05
min\_child\_weight: 3–15
subsample: 0.60–0.90
colsample\_bytree: 0.50–0.90
reg\_lambda: 5–50
reg\_alpha: 0–5
n\_estimators: 200–1200 con early stopping

Para CatBoost:

depth: 3–5
learning\_rate: 0.01–0.05
l2\_leaf\_reg: 5–50
iterations: 300–1200

No usaría profundidad 8–10 con este N.

Random Forest:

n\_estimators: 500–1500
max\_depth: 3–8
min\_samples\_leaf: 5–15
max\_features: 0.3–0.7

El min\_samples\_leaf relativamente alto es más importante aquí que aumentar miles de árboles.

Para SVR, todos los predictores deben estandarizarse:

Buscaría:

kernel = RBF
C = 0.1 – 100
epsilon = 0.05 – 0.40
gamma = scale + búsqueda log

GPR sería especialmente atractivo después de una reducción a aproximadamente 10–15 variables con kernel Matérn o :

más WhiteKernel para absorber error de reporte de rendimiento.

Con 138 observaciones, GPR no tiene un problema computacional; el problema es **estadístico** si se permite un length-scale independiente para 60 variables.

### Validación espacial exacta

La validación aleatoria clásica supone que train y validation son aproximadamente independientes. Aquí eso falla porque parcelas vecinas comparten:

Roberts et al. demuestran que ignorar estructuras espaciales, temporales o jerárquicas puede subestimar seriamente el error predictivo. DOI **10.1111/ecog.02881**. [\[36\]](https://findanexpert.unimelb.edu.au/scholarlywork/1186691-cross-validation-strategies-for-data-with-temporal--spatial--hierarchical--or-phylogenetic-structure)

Proyectaría centroides desde EPSG:4326 a **UTM 14N, EPSG:32614** y formaría grupos geográficos.

No usaría municipio como única validación primaria. Existe un problema grave de desequilibrio: Chignahuapan contiene 71 de las 138 parcelas de entrenamiento; un LeaveOneMunicipalityOut dejaría en un fold más de la mitad de la muestra.

Mi diseño recomendado:

**Validación primaria: cinco bloques geográficos.**

Crear 5 clusters de coordenadas mediante k-means espacial o agrupamiento jerárquico, intentando que cada bloque contenga aproximadamente 20–35 parcelas y que parcelas muy próximas no queden a ambos lados del límite.

Posteriormente:

GroupKFold(n\_splits=5)
groups = spatial\_cluster\_id

La literatura de blockCV formaliza precisamente la construcción de folds espacialmente separados; referencia: Valavi et al. (2019), DOI **10.1111/2041-210X.13107**. La literatura reciente vuelve a remarcar que tamaño y geometría de los bloques modifican sustancialmente la estimación del error. [\[37\]](https://www.frontiersin.org/journals/remote-sensing/articles/10.3389/frsen.2025.1531097/full)

Una versión aún mejor es estimar primero el rango de autocorrelación de rendimiento o residuos mediante variograma y elegir bloques cuyo diámetro sea comparable o mayor que ese rango.

**Tuning interno:**

en los cuatro bloques restantes.

Esta es una validación anidada. Hyperparameters, selección de variables y ensemble weights se ajustan exclusivamente dentro del outer-train.

**Stress test regional: leave-one-state-out.**

Tres experimentos:

train Hidalgo + Tlaxcala → test Puebla
train Puebla + Tlaxcala → test Hidalgo
train Puebla + Hidalgo → test Tlaxcala

No representan exactamente el test oculto —porque éste contiene los tres estados—, pero son extremadamente útiles para detectar un modelo que únicamente aprendió “Puebla alto / Tlaxcala bajo”.

Mi criterio de selección sería combinar:

con

y dispersión entre folds. Preferiría un modelo con RMSE 0.50 t/ha estable en todos los folds frente a uno con 0.40 t/ha medio pero 0.25–0.90 dependiendo de la región.

También compararía dos versiones:

Si mejora drásticamente K-fold local pero colapsa leave-state-out, el incremento es probablemente un atajo geográfico.

### Métricas

RMSE:

Es especialmente apropiado si errores grandes son muy costosos.

MAE:

Es más robusto ante outliers/errores extremos de reporte.

Coeficiente de determinación:

En validación espacial puede ser negativo; eso no es un bug: significa que el modelo es peor que predecir la media del conjunto validado.

MAPE:

Aquí el problema de división por cero no existe porque los rendimientos observados son ≥2 t/ha, pero MAPE da proporcionalmente más peso a parcelas de menor rendimiento. Por eso lo emplearía como métrica secundaria.

Muy importante: calcularía RMSE, MAE y sobre el **vector OOF completo**:

y no promediaría entre folds pequeños.

Además reportaría errores por estado:

RMSE\_Puebla
RMSE\_Hidalgo
RMSE\_Tlaxcala

y por tercil de superficie. Un buen score global podría ocultar errores sistemáticos precisamente en Tlaxcala.

## Arquitectura final, XAI, control biológico y referencias prioritarias

La implementación que considero óptima puede resumirse como el siguiente flujo:

Polígonos
│
├── Geometría / CEM
├── SoilGrids + INEGI
├── CHIRPS + ERA5-Land / POWER / SMN
│
├── Planet 2025 ── QA ── smoothing ── phenometrics
├── Sentinel-2 ─── QA ── smoothing ── phenometrics
└── Landsat ────── QA ── smoothing ── phenometrics
│
▼
tabla 1 fila / parcela
│
~60–80 variables candidatas
│
spatial outer CV
│
┌────────────────┴────────────────┐
│ │
filtro + mRMR selección ElasticNet
│ │
└─────────── 20–40 features ──────┘
│
┌──────────────┼───────────────┐
▼ ▼ ▼
ElasticNet SVR/GPR CatBoost/XGB
│ │ │
└───────── OOF predictions ────┘
│
convex weighted blend
│
▼
rendimiento t/ha + intervalo

El ensamble puede calcularse como:

con:

y los pesos escogidos para minimizar RMSE **exclusivamente sobre predicciones OOF espaciales**. Con 138 parcelas, esta restricción convexa es preferible a entrenar un meta-modelo complejo.

Una combinación inicial razonable a probar, no a fijar a priori, sería que el modelo lineal aporte estabilidad, CatBoost/XGBoost las interacciones no lineales suelo×clima y SVR/GPR la respuesta continua suave.

### Auditoría SHAP

SHAP permite descomponer:

donde representa la contribución del predictor a la predicción de la parcela . Para árboles, TreeSHAP permite una implementación eficiente y con propiedades consistentes; Lundberg et al. formalizaron su uso para interpretabilidad de modelos de árboles. DOI **10.1038/s42256-019-0138-9**.

No calcularía SHAP únicamente sobre el modelo final entrenado con los 138 ejemplos. Calcularía también **SHAP sobre cada fold validado** y comprobaría estabilidad de signos.

La auditoría agronómica debería exigir aproximadamente:

| Predictor | Relación esperable | Bandera roja |
| --- | --- | --- |
| AUC NDVI/LAI llenado | positiva hasta saturación | gran efecto negativo sin explicación |
| --- | --- | --- |
| senescence\_rate rápida | negativa | fuerte efecto positivo |
| NDWI en reproducción | generalmente positiva | monotonicidad negativa universal |
| días Tmax >35 °C en llenado | negativa | efecto consistentemente positivo |
| heladas en embuche/antesis | negativa | efecto positivo |
| radiación útil llenado | positiva si agua adecuada | efecto incondicional enorme |
| AWC | positiva bajo déficit; posible saturación | señal extrema sin interacción |
| nube media | debería tener poco efecto | predictor principal |
| ESTADO | residual/moderado | predictor dominante absoluto |
| área | posible efecto pequeño | domina NDVI/clima |
| pixel\_count | calidad, no productividad | gran predictor de rendimiento |

Una dependencia SHAP razonable para temperatura podría ser no lineal:

La literatura de cebada respalda precisamente el deterioro reproductivo y de llenado bajo temperaturas elevadas. [\[4\]](https://pmc.ncbi.nlm.nih.gov/articles/PMC11314375/)

El chequeo más poderoso sería reconstruir implícitamente la identidad del rendimiento. Si SHAP indica:

más macollamiento/vigor temprano
\+ persistencia LAI
\+ agua durante reproducción
\+ AUC de llenado
\- calor
\- senescencia prematura
→ mayor rendimiento

el modelo es biológicamente coherente.

Si, en cambio:

estado=Puebla
\+ longitud
\+ ID de municipio
\+ porcentaje de nube
→ mayor rendimiento

aunque tenga un CV aleatorio espectacular, no es un modelo que deba considerarse robusto.

### Variables finales que probablemente merezcan entrar

Una configuración final compacta podría contener, aproximadamente:

planet\_ndvi\_peak
planet\_peak\_doy
planet\_ndvi\_auc\_total
planet\_ndvi\_auc\_postpeak
planet\_lai\_peak
planet\_lai\_auc\_fill
planet\_ndwi\_fill
planet\_senescence\_rate
planet\_growth\_rate

s2\_ndvi\_peak
s2\_evi\_auc
s2\_ndwi\_min\_reproductive
s2\_lai\_peak

landsat\_msi\_fill
landsat\_nddi\_peak

gdd\_sos\_peak
gdd\_peak\_eos
precip\_vegetative
precip\_reproductive
precip\_fill
cdd\_reproductive
vpd\_reproductive
vpd\_fill
radiation\_fill
et0\_minus\_p\_fill
days\_tmax30\_reproductive
days\_tmax35\_fill
days\_tmin0\_reproductive
days\_tmin\_minus2\_reproductive

awc\_0\_30
awc\_0\_60
clay\_0\_30
soc\_0\_30
ph\_0\_30
bulk\_density\_0\_30

elevation
slope
log\_area
effective\_s2\_pixels
effective\_landsat\_pixels

historical\_peak\_ndvi\_2022\_2024
historical\_auc\_cv
siap\_yield\_median\_2018\_2024

No todos deben sobrevivir. Son **candidatos** para selección nested-CV.

Particularmente útiles pueden ser las interacciones:

Los árboles pueden aprenderlas implícitamente; para ElasticNet/SVR vale la pena construir sólo unas pocas interacciones con justificación fisiológica.

### Cómo usar 2022–2024 sin inducir ruido

Las series antiguas son valiosas como “firma productiva del sitio”, pero sólo si se interpretan correctamente. Si no se conoce qué cultivo ocupó cada polígono en 2022–2024, no debería compararse directamente un NDVI\_2023\_julio con la cebada 2025.

Construiría rasgos robustos:

y 2025\_anomaly = AUC\_2025 - historical\_median, siempre que las curvas antiguas demuestren una temporada agrícola comparable.

Eso permite que el modelo distinga una parcela intrínsecamente productiva de un año excepcional.

### Orden práctico de experimentación

En lugar de correr decenas de algoritmos desde el principio, utilizaría una escalera de ablation experiments:

| Experimento | Features | Pregunta |
| --- | --- | --- |
| Baseline | media global | dificultad mínima |
| --- | --- | --- |
| Regional | estado/municipio | cuánto rendimiento explica geografía |
| Topo+suelo | CEM + SoilGrids | capacidad edáfica |
| Climate | \+ GDD/agua/calor | efecto meteorológico |
| Satellite S2 | \+ fenología S2 | señal de cultivo |
| Planet | \+ fenología Planet | valor de alta frecuencia/resolución |
| Full bio | todo excepto administración | generalización fisiológica |
| Full geo | full bio + estado/coords | valor incremental de ubicación |
| Ensemble | mejores 2–3 | estabilidad final |

El resultado decisivo será la diferencia entre Full bio y Full geo. Mi objetivo sería que **Full bio explique la mayor parte de la brecha regional**, dejando a estado/coordenadas sólo un residuo.

Finalmente, no impondría:

sólo porque ése sea el rango de entrenamiento. El test puede legítimamente contener un rendimiento fuera del rango observado. Si se utiliza clipping, debería ser un límite agronómico amplio y validado, no min/max(train).

### Fuentes y referencias bibliográficas prioritarias

| Referencia | Utilidad | DOI / repositorio |
| --- | --- | --- |
| Cammarano et al. (2021), modelado de cebada / CERES-Barley | desarrollo térmico y manejo | **10.3389/fpls.2021.655406** [\[38\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.655406/full?utm_source=chatgpt.com) |
| --- | --- | --- |
| Shirdelmoghanloo et al. (2022), _Frontiers in Plant Science_ | calor y llenado/calidad del grano | **10.3389/fpls.2022.858652** [\[10\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.858652/full) |
| Samarah (2005), sequía en cebada | componentes de rendimiento | **10.1051/agro:2004064** [\[39\]](https://hal.science/hal-00886257v1/document) |
| Beck et al. (2006), Remote Sensing of Environment | doble logística fenológica | **10.1016/j.rse.2005.10.021** [\[32\]](https://www.sciencedirect.com/science/article/abs/pii/S0034425705003640) |
| Cai et al. (2017), _Remote Sensing_ | comparación de smoothing | **10.3390/rs9121271** [\[40\]](https://www.mdpi.com/2072-4292/9/12/1271) |
| Eilers (2003), _Analytical Chemistry_ | Whittaker smoothing | **10.1021/ac034173t** |
| Ji et al. (2021), _Sensors_ | phenometrics para yield | **10.3390/s21041406** [\[41\]](https://www.mdpi.com/1424-8220/21/4/1406) |
| Claverie et al. (2018), RSE | armonización Landsat/Sentinel-2 | **10.1016/j.rse.2018.09.002** [\[42\]](https://modis.gsfc.nasa.gov/sci_team/pubs/abstract_new.php?id=27008) |
| Roberts et al. (2017), _Ecography_ | spatial CV | **10.1111/ecog.02881** [\[36\]](https://findanexpert.unimelb.edu.au/scholarlywork/1186691-cross-validation-strategies-for-data-with-temporal--spatial--hierarchical--or-phylogenetic-structure) |
| Valavi et al. (2019), _Methods Ecol. Evol._ | spatial blocking | **10.1111/2041-210X.13107** [\[43\]](https://github.com/xarray-contrib/xbatcher/discussions/78) |
| Poggio et al. (2021), _SOIL_ | SoilGrids 2.0 | **10.5194/soil-7-217-2021** [\[44\]](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs.html?utm_source=chatgpt.com) |
| Muñoz-Sabater et al. (2021), ESSD | ERA5-Land | **10.5194/essd-13-4349-2021** [\[27\]](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview) |
| Funk et al. (2015), _Scientific Data_ | CHIRPS | **10.1038/sdata.2015.66** |
| Zou & Hastie (2005) | ElasticNet | **10.1111/j.1467-9868.2005.00503.x** |
| Peng et al. (2005) | mRMR | **10.1109/TPAMI.2005.159** |
| Kursa & Rudnicki (2010) | Boruta | **10.18637/jss.v036.i11** |
| Lundberg et al. (2020), _Nature Machine Intelligence_ | TreeSHAP | **10.1038/s42256-019-0138-9** |

Repositorios operativos prioritarios:

**SoilGrids / ISRIC:**
https://soilgrids.org/
https://maps.isric.org/
https://files.isric.org/soilgrids/latest/data/
La documentación oficial confirma la resolución de 250 m, las profundidades y las propiedades disponibles. [\[45\]](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html?utm_source=chatgpt.com)

**OpenLandMap / Google Earth Engine:**
https://developers.google.com/earth-engine/datasets/tags/openlandmap
El catálogo incluye productos edáficos globales, en gran parte a 250 m. [\[46\]](https://developers.google.com/earth-engine/datasets/tags/openlandmap?utm_source=chatgpt.com)

**INEGI Edafología Serie II, Continuo Nacional 1:250 000:**
https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551131916 [\[47\]](https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551131916)

**NASA POWER:**
https://power.larc.nasa.gov/api/temporal/daily/point
https://power.larc.nasa.gov/docs/services/api/temporal/daily/ [\[24\]](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)

**ERA5-Land / Copernicus CDS:**
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land [\[27\]](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview)

**CONAGUA / SMN – EMAs:**
https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s [\[28\]](https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s)

**SIAP / SADER – Cierre agrícola:**
https://nube.siap.gob.mx/cierre\_agricola/

La conclusión técnica central es que el mejor modelo para AgroCebada 2026 no debería “predecir Puebla, Hidalgo o Tlaxcala”. Debe aprender una cadena causal aproximada:

y utilizar la información espacial sólo para completar, no reemplazar, esa explicación. Con apenas 138 etiquetas, la ganancia de precisión más probable no vendrá de añadir más capas indiscriminadamente, sino de **reducir miles de observaciones a unas pocas métricas fenológicas y de estrés de alta calidad, validar espacialmente y exigir que la explicación SHAP sea compatible con la fisiología de la cebada**.

[\[1\]](https://findanexpert.unimelb.edu.au/scholarlywork/1186691-cross-validation-strategies-for-data-with-temporal--spatial--hierarchical--or-phylogenetic-structure) [\[36\]](https://findanexpert.unimelb.edu.au/scholarlywork/1186691-cross-validation-strategies-for-data-with-temporal--spatial--hierarchical--or-phylogenetic-structure) https://findanexpert.unimelb.edu.au/scholarlywork/1186691-cross-validation-strategies-for-data-with-temporal--spatial--hierarchical--or-phylogenetic-structure

[https://findanexpert.unimelb.edu.au/scholarlywork/1186691-cross-validation-strategies-for-data-with-temporal--spatial--hierarchical--or-phylogenetic-structure](https://findanexpert.unimelb.edu.au/scholarlywork/1186691-cross-validation-strategies-for-data-with-temporal--spatial--hierarchical--or-phylogenetic-structure)

[\[2\]](https://hal.science/hal-00886257v1/document) [\[11\]](https://hal.science/hal-00886257v1/document) [\[39\]](https://hal.science/hal-00886257v1/document) https://hal.science/hal-00886257v1/document

[https://hal.science/hal-00886257v1/document](https://hal.science/hal-00886257v1/document)

[\[3\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.655406/full?utm_source=chatgpt.com) [\[8\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.655406/full?utm_source=chatgpt.com) [\[9\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.655406/full?utm_source=chatgpt.com) [\[38\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.655406/full?utm_source=chatgpt.com) Genetic and Management Effects on Barley Yield ...

[https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.655406/full?utm\_source=chatgpt.com](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.655406/full?utm_source=chatgpt.com)

[\[4\]](https://pmc.ncbi.nlm.nih.gov/articles/PMC11314375/) [\[6\]](https://pmc.ncbi.nlm.nih.gov/articles/PMC11314375/) https://pmc.ncbi.nlm.nih.gov/articles/PMC11314375/

[https://pmc.ncbi.nlm.nih.gov/articles/PMC11314375/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11314375/)

[\[5\]](https://link.springer.com/article/10.1186/s12870-025-07504-8) https://link.springer.com/article/10.1186/s12870-025-07504-8

[https://link.springer.com/article/10.1186/s12870-025-07504-8](https://link.springer.com/article/10.1186/s12870-025-07504-8)

[\[7\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.858652/full) [\[10\]](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.858652/full) https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.858652/full

[https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.858652/full](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.858652/full)

[\[12\]](https://www.ndsu.edu/agriculture/ag-hub/ag-topics/crop-production/crops/barley/small-grain-damage-frost-dependent-many-factors) https://www.ndsu.edu/agriculture/ag-hub/ag-topics/crop-production/crops/barley/small-grain-damage-frost-dependent-many-factors

[https://www.ndsu.edu/agriculture/ag-hub/ag-topics/crop-production/crops/barley/small-grain-damage-frost-dependent-many-factors](https://www.ndsu.edu/agriculture/ag-hub/ag-topics/crop-production/crops/barley/small-grain-damage-frost-dependent-many-factors)

[\[13\]](https://www.gob.mx/agricultura/hidalgo/articulos/cebada-maltera-en-la-region-de-apan-hidalgo?idiom=es&utm_source=chatgpt.com) Cebada maltera en la región de Apan, Hidalgo.

[https://www.gob.mx/agricultura/hidalgo/articulos/cebada-maltera-en-la-region-de-apan-hidalgo?idiom=es&utm\_source=chatgpt.com](https://www.gob.mx/agricultura/hidalgo/articulos/cebada-maltera-en-la-region-de-apan-hidalgo?idiom=es&utm_source=chatgpt.com)

[\[14\]](https://www.scielo.org.mx/article_plus.php?lng=es&pid=S2007-09342016000100159&tlng=es&utm_source=chatgpt.com) Evaluación agronómica y física en líneas avanzadas de cebada ...

[https://www.scielo.org.mx/article\_plus.php?lng=es&pid=S2007-09342016000100159&tlng=es&utm\_source=chatgpt.com](https://www.scielo.org.mx/article_plus.php?lng=es&pid=S2007-09342016000100159&tlng=es&utm_source=chatgpt.com)

[\[15\]](https://www.mdpi.com/1424-8220/21/4/1406) [\[41\]](https://www.mdpi.com/1424-8220/21/4/1406) https://www.mdpi.com/1424-8220/21/4/1406

[https://www.mdpi.com/1424-8220/21/4/1406](https://www.mdpi.com/1424-8220/21/4/1406)

[\[16\]](https://wmo.int/es/media/news/la-organizacion-meteorologica-mundial-advierte-de-la-creciente-probabilidad-de-formacion-de-un) https://wmo.int/es/media/news/la-organizacion-meteorologica-mundial-advierte-de-la-creciente-probabilidad-de-formacion-de-un

[https://wmo.int/es/media/news/la-organizacion-meteorologica-mundial-advierte-de-la-creciente-probabilidad-de-formacion-de-un](https://wmo.int/es/media/news/la-organizacion-meteorologica-mundial-advierte-de-la-creciente-probabilidad-de-formacion-de-un)

[\[17\]](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs.html?utm_source=chatgpt.com) [\[44\]](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs.html?utm_source=chatgpt.com) SoilGrids Documentation

[https://docs.isric.org/globaldata/soilgrids/SoilGrids\_faqs.html?utm\_source=chatgpt.com](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs.html?utm_source=chatgpt.com)

[\[18\]](https://docs.isric.org/globaldata/soilgrids/wms_from_qgis_arcmap.html?utm_source=chatgpt.com) Access WMS with ArcMap and QGIS – SoilGrids ...

[https://docs.isric.org/globaldata/soilgrids/wms\_from\_qgis\_arcmap.html?utm\_source=chatgpt.com](https://docs.isric.org/globaldata/soilgrids/wms_from_qgis_arcmap.html?utm_source=chatgpt.com)

[\[19\]](https://docs.isric.org/globaldata/soilgrids/wcs.html?utm_source=chatgpt.com) WCS - SoilGrids Documentation

[https://docs.isric.org/globaldata/soilgrids/wcs.html?utm\_source=chatgpt.com](https://docs.isric.org/globaldata/soilgrids/wcs.html?utm_source=chatgpt.com)

[\[20\]](https://docs.isric.org/globaldata/soilgrids/access_on_gee.html?utm_source=chatgpt.com) SoilGrids on Google Earth Engine (GEE)

[https://docs.isric.org/globaldata/soilgrids/access\_on\_gee.html?utm\_source=chatgpt.com](https://docs.isric.org/globaldata/soilgrids/access_on_gee.html?utm_source=chatgpt.com)

[\[21\]](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html?utm_source=chatgpt.com) [\[45\]](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html?utm_source=chatgpt.com) SoilGrids layers

[https://docs.isric.org/globaldata/soilgrids/SoilGrids\_faqs\_01.html?utm\_source=chatgpt.com](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html?utm_source=chatgpt.com)

[\[22\]](https://developers.google.com/earth-engine/datasets/catalog/OpenLandMap_SOL_SOL_TEXTURE-CLASS_USDA-TT_M_v02?utm_source=chatgpt.com) OpenLandMap Soil Texture Class (USDA System)

[https://developers.google.com/earth-engine/datasets/catalog/OpenLandMap\_SOL\_SOL\_TEXTURE-CLASS\_USDA-TT\_M\_v02?utm\_source=chatgpt.com](https://developers.google.com/earth-engine/datasets/catalog/OpenLandMap_SOL_SOL_TEXTURE-CLASS_USDA-TT_M_v02?utm_source=chatgpt.com)

[\[23\]](https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551131916) [\[47\]](https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551131916) https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551131916

[https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551131916](https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551131916)

[\[24\]](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) [\[25\]](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) [\[26\]](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) https://power.larc.nasa.gov/docs/services/api/temporal/daily/

[https://power.larc.nasa.gov/docs/services/api/temporal/daily/](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)

[\[27\]](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview) https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview

[https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview)

[\[28\]](https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s) https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s

[https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s](https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s)

[\[29\]](https://smn.conagua.gob.mx/es/climatologia/informacion-climatologica/normales-climatologicas-por-estado?estado=tlax) https://smn.conagua.gob.mx/es/climatologia/informacion-climatologica/normales-climatologicas-por-estado?estado=tlax

[https://smn.conagua.gob.mx/es/climatologia/informacion-climatologica/normales-climatologicas-por-estado?estado=tlax](https://smn.conagua.gob.mx/es/climatologia/informacion-climatologica/normales-climatologicas-por-estado?estado=tlax)

[\[30\]](https://modis.gsfc.nasa.gov/sci_team/pubs/abstract_new.php?id=27008) [\[33\]](https://modis.gsfc.nasa.gov/sci_team/pubs/abstract_new.php?id=27008) [\[35\]](https://modis.gsfc.nasa.gov/sci_team/pubs/abstract_new.php?id=27008) [\[42\]](https://modis.gsfc.nasa.gov/sci_team/pubs/abstract_new.php?id=27008) https://modis.gsfc.nasa.gov/sci\_team/pubs/abstract\_new.php?id=27008

[https://modis.gsfc.nasa.gov/sci\_team/pubs/abstract\_new.php?id=27008](https://modis.gsfc.nasa.gov/sci_team/pubs/abstract_new.php?id=27008)

[\[31\]](https://www.sciencedirect.com/science/article/abs/pii/S0034425715302443) https://www.sciencedirect.com/science/article/abs/pii/S0034425715302443

[https://www.sciencedirect.com/science/article/abs/pii/S0034425715302443](https://www.sciencedirect.com/science/article/abs/pii/S0034425715302443)

[\[32\]](https://www.sciencedirect.com/science/article/abs/pii/S0034425705003640) https://www.sciencedirect.com/science/article/abs/pii/S0034425705003640

[https://www.sciencedirect.com/science/article/abs/pii/S0034425705003640](https://www.sciencedirect.com/science/article/abs/pii/S0034425705003640)

[\[34\]](https://www.sciencedirect.com/science/article/pii/S0034425718304139) https://www.sciencedirect.com/science/article/pii/S0034425718304139

[https://www.sciencedirect.com/science/article/pii/S0034425718304139](https://www.sciencedirect.com/science/article/pii/S0034425718304139)

[\[37\]](https://www.frontiersin.org/journals/remote-sensing/articles/10.3389/frsen.2025.1531097/full) https://www.frontiersin.org/journals/remote-sensing/articles/10.3389/frsen.2025.1531097/full

[https://www.frontiersin.org/journals/remote-sensing/articles/10.3389/frsen.2025.1531097/full](https://www.frontiersin.org/journals/remote-sensing/articles/10.3389/frsen.2025.1531097/full)

[\[40\]](https://www.mdpi.com/2072-4292/9/12/1271) https://www.mdpi.com/2072-4292/9/12/1271

[https://www.mdpi.com/2072-4292/9/12/1271](https://www.mdpi.com/2072-4292/9/12/1271)

[\[43\]](https://github.com/xarray-contrib/xbatcher/discussions/78) https://github.com/xarray-contrib/xbatcher/discussions/78

[https://github.com/xarray-contrib/xbatcher/discussions/78](https://github.com/xarray-contrib/xbatcher/discussions/78)

[\[46\]](https://developers.google.com/earth-engine/datasets/tags/openlandmap?utm_source=chatgpt.com) Datasets tagged openlandmap in Earth Engine

[https://developers.google.com/earth-engine/datasets/tags/openlandmap?utm\_source=chatgpt.com](https://developers.google.com/earth-engine/datasets/tags/openlandmap?utm_source=chatgpt.com)
