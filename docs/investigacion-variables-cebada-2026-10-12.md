# Investigación de datos y variables para mejorar AgroCebada

Fecha de consulta: 12 de octubre de 2026. Ámbito: parcelas de cebada de Hidalgo, Tlaxcala y Puebla; estimación retrospectiva abril–octubre de 2025.

La prioridad propuesta es recuperar calendario y manejo parcelarios, comprobar una señal hídrica vegetal y contrastar clima local con las fuentes regionales existentes. Las prioridades son una recomendación de investigación, no una importancia de variables demostrada por nuestro modelo. La literatura respalda hipótesis agronómicas; la ganancia predictiva requiere una comparación nueva.

## 1. Evidencia del proyecto y alcance de esta revisión

La fase hídrica terminó sin promover W05. Su RMSE principal fue 0.925988 t/ha frente a 0.764053 t/ha de la ruta activa seleccionada W00. La receta experimental cambió también familias y selección: esa diferencia no identifica por sí sola el efecto de una variable nueva. Suelo quedó excluido por integridad insuficiente del recorte; estrés compuesto, por desconocer las bandas y fórmula del NDWI entregado.

La auditoría no encontró variedad, siembra ni riego vinculados a los IDs oficiales. Las cuatro series NASA revisadas no presentaron mínimas diarias bajo cero; eso no demuestra ausencia de heladas parcelarias.

Una lectura del archivo oficial de áreas, sin utilizar rendimientos, confirmó 197 parcelas: mínimo 0.35 ha, mediana 5.46 ha y máximo 64.3 ha. Hay 118 parcelas menores que 6.25 ha, superficie de una celda de 250 × 250 m. Todas son menores que las 100 ha de una celda de 1 km. La forma y ubicación de cada parcela también determinan su soporte real.

Evidencia local: [resultados](../experiments/hidrica-estres-20261009/docs/results.md), [auditoría agronómica](../experiments/hidrica-estres-20261009/registry/agronomic-metadata-audit.json), [auditoría espectral](../experiments/hidrica-estres-20261009/registry/spectral-audit.json), [intento de adquisición de suelo](../experiments/hidrica-estres-20261009/registry/soil-acquisition.json) y [áreas oficiales](../Reto-Cebada/DataSet/Data/ID_area_rendimiento_70_30_Reto_AgroCebada.csv).

Se revisaron documentación de proveedores, publicaciones científicas y materiales agronómicos oficiales. Se comprobó la existencia de portales y listados; no se adquirieron nuevas series ni se verificó cobertura completa de 2025 para cada polígono. Algunas páginas gob.mx y PDF no permitieron apertura directa: sus afirmaciones se limitaron al contenido indexado disponible. No se modificaron modelos ni protocolos congelados.

## 2. Calendario y variedad: primera solicitud a productores

INIFAP describe variedades para los Valles Altos con madurez de 95–125 días y diferencias de adaptación entre Esmeralda y Adabella. Esto respalda registrar variedad y fechas reales; no permite asignar una variedad a una parcela por municipio o recomendación. La publicación es de 2022 y tampoco verifica cuáles se sembraron en 2025. [INIFAP: variedades recomendadas](https://www.gob.mx/inifap/articulos/materiales-de-cebada-recomendados-por-el-inifap).

La FAO explica que la respuesta de la cebada al déficit depende del momento, duración e intensidad, por lo que el acumulado de toda la temporada puede ocultar exposiciones relevantes. [FAO, Crop yield response to water, sección de cebada](https://www.fao.org/4/i2800e/i2800e.pdf).

Solicitar por ID y campaña: variedad, siembra, emergencia, espigamiento, floración, madurez y cosecha. Construir días desde siembra y exposiciones por etapa solo donde estén respaldados. Una fecha satelital aproximada debe conservarse como estimación; un pico de verdor no es una observación de floración. Grados día son una opción posterior, con temperatura base y límites documentados para el material y condiciones pertinentes.

## 3. Retención y humedad del suelo son datos distintos

La capacidad de almacenamiento disponible se aproxima mediante la diferencia entre humedad a capacidad de campo y al punto de marchitez, integrada por espesor. Para un estrato homogéneo:

`capacidad_mm = 1000 × (theta_CC − theta_PM) × espesor_m`

Las theta deben estar en m³/m³. La humedad actual exige una observación o estimación fechada; no se obtiene de un mapa estático de capacidad. [FAO-56, disponibilidad de agua y balance del suelo](https://www.fao.org/4/X0490E/x0490e0e.htm).

Los 10 o 33 kPa son aproximaciones alternativas al límite superior, según material y método; se debe documentar la elección y evaluar su sensibilidad. [GlobalSoilMap: especificación de capacidad de agua disponible](https://www.isric.org/sites/default/files/GlobalSoilMap_specifications_december_2015_2.pdf).

**Ruta preferida:** muestras parcelarias con textura, densidad, fragmentos gruesos, profundidad y retención; sensores o muestreos repetidos para humedad. El carbono orgánico y el pH aportarían caracterización adicional, sin sustituir mediciones de retención.

**Ruta cartográfica:** SoilGrids documenta retención a distintas presiones, seis estratos y unidades escaladas. No se debe confundir convertir a porcentaje con convertir a fracción volumétrica; hay que verificar también la denominación del servicio, que no siempre coincide literalmente con la tabla. [Capas y unidades de SoilGrids](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html).

ISRIC advierte expresamente que su modelo global se adapta mejor a análisis amplios y desaconseja usarlo a escala local o de finca. Por tanto, proponemos solo una hipótesis de contexto regional, contrastada con muestras locales. [Limitaciones oficiales](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_04.html).

Encontré una vía adicional al WCS fallido: listados oficiales de medias agregadas a 1 km para [retención a 33 kPa](https://files.isric.org/soilgrids/latest/data_aggregated/1000m/wv0033/) y [1500 kPa](https://files.isric.org/soilgrids/latest/data_aggregated/1000m/wv1500/). La existencia del listado no prueba integridad, cobertura ni utilidad. Esta alternativa cambia resolución y soporte de incertidumbre; no puede incorporarse silenciosamente al experimento anterior. El [REST de ISRIC](https://rest.isric.org/) continúa declarado beta, sin garantía de disponibilidad y con política de cinco llamadas por minuto.

INEGI ofrece [edafología y perfiles de suelo](https://www.inegi.org.mx/temas/edafologia/) a escala 1:250 000. Es una alternativa de contexto nacional con límites de detalle; tampoco equivale a una muestra de nuestra parcela. WoSIS conserva [perfiles estandarizados y retención](https://isric.org/explore/wosis); habría que verificar proximidad, profundidad, método y fecha de cualquier muestra encontrada.

Inicialmente proponemos capacidades para 0–30 y 30–60 cm, con espesores reales y máscara común. Esos intervalos no representan automáticamente toda la zona radicular. Las diferencias físicamente incoherentes deben marcarse inválidas, y las diferencias entre quantiles no deben presentarse como un intervalo probabilístico calibrado de la capacidad resultante.

## 4. Lluvia, riego y balance de agua

Solicitar lluvia diaria, modalidad temporal/riego, fechas y láminas de riego. Variables candidatas: acumulados por etapa, duración de periodos secos, distribución de lluvia y anomalías respecto a una referencia histórica documentada.

[CHIRPS v3](https://www.chc.ucsb.edu/data/chirps3) cubre desde 1981 hasta cerca del presente a 0.05°. Su producto diario desagrega totales de cinco días mediante información auxiliar; la fecha no representa una ventana de observación uniforme de todas las estaciones. Es útil para probar contexto y acumulados, pero los días exactos sin lluvia deben contrastarse con estaciones. Conservar versión, variante diaria y condición preliminar/final. Cambiar de CHIRPS mensual a diario añade información temporal; no transforma el producto en medición de parcela.

Un balance hídrico requiere además demanda evaporativa, almacenamiento inicial y supuestos de escorrentía y drenaje. La resta lluvia−ET0 puede servir como indicador climático, pero no es el agua realmente almacenada ni la evapotranspiración del cultivo.

## 5. Temperatura, VPD, heladas y demanda evaporativa

El [SMN/CONAGUA](https://smn.conagua.gob.mx/es/?id=177%3Aqu&option=com_content&view=article) publica información de estaciones con temperatura máxima/mínima y precipitación de 24 horas. Primera tarea de adquisición: seleccionar estaciones por posición, elevación, continuidad y representatividad, y comprobar cobertura abril–octubre de 2025. Que una estación exista en el mapa no asegura datos completos de esa campaña.

[ERA5-Land](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview) ofrece estimaciones horarias desde 1950, a resolución nativa de 9 km y distribuida en 0.1°, con cuatro capas de suelo. Es alternativa para contexto climático y humedad modelada, con evaluación de sesgo local. Las capas 0–7, 7–28, 28–100 y 100–289 cm no coinciden con nuestros estratos propuestos.

[NASA POWER](https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/) documenta mallas de 0.5° × 0.625° para meteorología y 1° × 1° para radiación. Consultar coordenadas diferentes dentro de la misma celda no crea mediciones independientes.

Para VPD hacen falta temperatura y humedad relativa o punto de rocío coincidentes; para ET0 se añaden radiación y viento con altura de medición documentada. VPD representa demanda atmosférica, no déficit de agua del suelo. [FAO-56, datos meteorológicos](https://www.fao.org/4/X0490E/x0490e07.htm).

Para heladas proponemos temperatura local y duración bajo umbrales, vinculadas a etapa y daños observados. Un umbral bajo cero puede describir exposición meteorológica, pero no determina por sí solo daño productivo. Los ensayos de tolerancia de cereales requieren atención a fenología y repetición entre años y sitios. [Conducting Field Trials for Frost Tolerance Breeding in Cereals](https://pubmed.ncbi.nlm.nih.gov/32607974/).

## 6. Señal hídrica vegetal y estrés conjunto

USGS documenta NDMI como `(NIR − SWIR)/(NIR + SWIR)` para representar condición hídrica vegetal. El nombre NDWI por sí solo no permite identificar qué bandas se usaron en los CSV del reto. Primero debe recuperarse la fórmula del productor; alternativamente, producir una serie nueva y trazable. [USGS: NDMI](https://www.usgs.gov/landsat-missions/normalized-difference-moisture-index).

Una opción candidata es Sentinel-2 L2A con B8A y B11 a 20 m, conservando esa elección como definición propia, sin afirmar equivalencia exacta entre sensores. Añadir clasificación de escena y máscaras de nubes/sombras, porcentajes de área válida, fechas y lagunas. Remuestrear a 10 m no crea detalle SWIR nuevo. [Copernicus: bandas y calidad de Sentinel-2 L2A](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html).

Paul y colaboradores estudiaron 81 líneas de cebada, con un seguimiento replicado de 18, y encontraron distintas estrategias de respuesta a sequía. Es evidencia experimental a favor de considerar variedad y dinámica hídrica; procede de plantas en macetas y condiciones controladas, no de nuestros campos mexicanos. [Artículo original, 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11231632/).

La recomendación es comparar VPD, temperatura y señal hídrica por separado, después interacciones acotadas y coexposición temporal con soporte suficiente. Cualquier escala o umbral relativo debe aprenderse solo con entrenamiento. La suma directa de kPa, °C e índice adimensional carece de una escala común. Tampoco demuestra cierre estomático ni semanas exactas sin fotosíntesis.

## 7. Relieve, radiación y opciones posteriores

Para investigar la diferencia entre terrenos planos e inclinados hacen falta suelo y humedad junto al relieve. Un índice topográfico de humedad combina área contribuyente y pendiente, pero depende de resolución, tratamiento hidrológico y método de cálculo. Un estudio en cinco campos de Nueva York encontró que añadir suelo y mejorar el modelo de elevación ayudaba; no demuestra la misma precisión en México. [Buchanan et al., 2014](https://hess.copernicus.org/articles/18/3279/2014/).

INEGI proporciona una [ruta de descarga del CEM](https://www.inegi.org.mx/app/geo2/elevacionesmex/index.jsp) con [opciones de resolución](https://www.inegi.org.mx/app/geo2/elevacionesmex/DownloadPdf.do), incluido 15 m. Verificar producto, modelo de terreno/superficie, datum, resolución y cobertura antes de producir orientación, curvatura, posición topográfica o índice de humedad. Los indicadores de drenaje son hipótesis, no tasas medidas de infiltración o escorrentía.

La radiación debe expresarse como energía por superficie e integrarse por etapa. La fracción de nubes de una captura satelital mide soporte observacional y no permite contar días nublados meteorológicos. Su efecto incremental debe compararse contra un control que conserve exactamente la misma calidad y calendario.

Como segunda fase, explorar [temperatura superficial Landsat](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature): representa temperatura de superficie al paso del satélite, no mínima nocturna ni temperatura del aire. Los sensores térmicos de Landsat 8/9 adquieren a 100 m aunque sus productos se remuestreen a 30 m. [USGS: resoluciones por banda](https://www.usgs.gov/faqs/what-are-band-designations-landsat-satellites).

[SMAP Enhanced L3](https://nsidc.org/data/spl3smp_e/versions/6) publica humedad superficial en malla de 9 km: opción para contexto regional, no observación independiente por parcela ni capacidad de retención. Una malla fina respecto a otro producto tampoco garantiza igual resolución efectiva del sensor.

## 8. Lista priorizada de adquisición

| Orden | Datos | Variables candidatas | Cómo conseguirlos | Estado para nuestras parcelas |
| --- | --- | --- | --- | --- |
| 1 | Siembra, variedad y etapas | Edad y exposiciones por etapa | Productores, bitácoras, organizadores | No vinculados a IDs oficiales |
| 2 | Fórmula NDWI o bandas L2A | Índice hídrico y evolución con soporte | Productor del CSV; catálogo Copernicus | Fórmula pendiente; nueva extracción pendiente |
| 3 | Clima local 2025 | Frío/calor, lluvia, VPD, ET0 | SMN, estaciones cercanas; ERA5-Land como contraste | Portales verificados; cobertura por parcela pendiente |
| 4 | Suelo y humedad fechada | Capacidad por estrato y dinámica de humedad | Laboratorio/sensores; mapas como contexto | Capas originales no admitidas; rutas adicionales identificadas |
| 5 | Riego y manejo | Aportes de agua, fertilización y establecimiento | Registros de campo con fechas/unidades | Riego ausente del maestro; otros campos por auditar |
| 6 | Relieve | Orientación, posición topográfica, índice de humedad | CEM y producto de terreno comprobado | Ruta documentada; extracción nueva pendiente |
| 7 | Rendimientos de otras campañas | Etiquetas independientes y estabilidad temporal | Productores o ensayos con identidad y método | Ninguna campaña nueva validada en esta revisión |
| 8 | Daños y fertilidad | Plagas, enfermedades, acame, granizo, análisis de suelo | Visitas, bitácoras, laboratorio | Cobertura y calidad por verificar |
| 9 | Térmico y humedad regional | Anomalías de temperatura superficial y SMAP | USGS y NSIDC | Opciones posteriores; soporte parcelario limitado |

Fertilización debe registrar nutriente, dosis y fecha; densidad, población establecida o semilla con unidad; daños, fecha y severidad. Son campos candidatos cuya importancia no ha sido demostrada aquí. Rendimiento requiere área cosechada, masa, unidad, humedad de grano cuando corresponda y método de medición; no sustituir etiquetas parcelarias con promedios municipales.

## 9. Próxima comparación recomendada

1. Recuperar calendario y fórmula espectral antes de diseñar indicadores fisiológicos.
2. Auditar cobertura de fuentes nuevas sin mirar errores ni ajustar reglas según etiquetas.
3. Congelar población, fuentes, fechas de disponibilidad, transformaciones y alternativas. Conservar intacta la fase cerrada; una resolución de suelo diferente exige un protocolo nuevo.
4. Añadir un bloque cada vez al control activo recuperable, conservando familias, selección y particiones para aislar su aporte.
5. Evaluar interacciones solo después de los efectos principales y con búsqueda acotada: 138 etiquetas no justifican incorporar decenas de combinaciones sin control.
6. Reportar errores por estado y esquema y validar en otra campaña cuando existan etiquetas compatibles. Volver a evaluar 2025 no es una prueba temporal independiente.

Las fuentes publicadas o revisadas después de la campaña pueden usarse para análisis retrospectivo declarado. No demuestran qué habría estado disponible al emitir un pronóstico en 2025. La adquisición, incorporación y cualquier mejora quedan pendientes de comprobación experimental.
