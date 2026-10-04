# Evaluación de fuentes externas

Consulta: 2026-10-02. Los tiempos exactos, URL, tamaños y SHA-256 de las descargas exitosas están en `download-manifest.json`. Los archivos se descargaron como evidencia para planificar; no constituyen un pipeline implementado.

## Inventario y decisión

| Fuente | Evidencia conseguida | Calidad y limitaciones | Decisión |
| --- | --- | --- | --- |
| NASA POWER | Cuatro respuestas JSON, nueve parámetros diarios, 214 días por respuesta, abril–octubre 2025, comunidad AG, tiempo LST | Sin valores centinela ni Tmin mayor que Tmax; unidades explícitas. Meteorología MERRA-2 a 0.5° × 0.625°, radiación SYN1deg a escala más gruesa. No es medición de parcela. | Candidato regional condicionado a evaluación; no reemplaza CHIRPS/CHIRTS ni demuestra eventos locales de helada/calor. |
| DGSIAP | Siete CSV nacionales 2018–2024 y diccionario XLSX; subconjunto comprobado de 63 combinaciones municipio-año para los nueve municipios del reto | Cebada grano, Primavera-Verano, Temporal, unidad Tonelada. Rendimiento municipal = producción / superficie cosechada. No identifica exclusivamente cebada maltera ni manejo de cada parcela. | Candidato histórico agregado, nunca etiqueta del reto ni límite obligatorio de predicción. |
| SoilGrids | Documentación oficial; consulta REST de propiedades en un punto de la región agotó el tiempo de espera de 25 s | La FAQ oficial desaconseja aplicaciones a escala local/finca; el servicio REST es beta. No se consiguieron valores ni incertidumbres verificables. | Excluido del alcance inicial. No inventar AWC, tepetate, SOC o clases de suelo. |
| ERA5-Land | Catálogo oficial accesible | No se descargaron series: el acceso estándar CDS requiere registro/autenticación y no se configuraron credenciales. Una página de catálogo no acredita cobertura/calidad de una serie. | Excluido de dependencias; no es necesario para que funcione el proyecto. |
| SMN/CONAGUA EMA | Portal oficial accesible con inventario y visualización | No se consiguieron series instrumentales completas abril–octubre 2025 con QA, estaciones operativas y unidades comprobadas. | Excluido; no usar coordenadas de estaciones citadas sin verificarlas. |
| INEGI edafología | Portal temático accesible, sin descarga verificable de una capa aplicable | No se verificaron atributos ni cobertura. Cartografía regional no equivale a una medición de profundidad efectiva por parcela. | Excluido; sí se conserva el CEM y pendiente entregados con el reto. |

## NASA: comprobación preliminar

`nasa-quality-screening.json` conserva los controles y el método. Se descargaron nodos meteorológicos (-98.75,19.5), (-98.125,19.5), (-98.75,20.0), (-98.125,20.0), que rodean la extensión de parcelas. Una asignación exploratoria usando centros de cajas envolventes ocupa tres nodos: 50, 1 y 146 parcelas; el cuarto se conserva como comprobación de cobertura. Esto no sustituye la asignación geoespacial definitiva ni aumenta el número de observaciones independientes. Las cuatro respuestas contienen solo dos series solares distintas.

Se compararon las medias mensuales de Tmax/Tmin diarias de NASA con los rásteres mensuales CHIRTS entregados, muestreados en esos puntos representativos aproximados (197 parcelas × 7 meses = 1,379 pares por variable):

| Variable | Sesgo NASA − CHIRTS | Diferencia absoluta media | Rango de diferencias |
| --- | --- | --- | --- |
| Tmax | -0.565 °C | 1.248 °C | -2.531 a 2.218 °C |
| Tmin | -1.300 °C | 1.314 °C | -3.368 a 0.791 °C |

CHIRTS no se trata como verdad instrumental; las diferencias pueden reflejar resolución, altitud y métodos. No se aplicó corrección de sesgo. La evaluación final deberá rehacer la extracción de forma geoespacial documentada. NASA puede aportar radiación, humedad y contexto diario, pero no respalda alertas por helada dentro de una parcela. VPD calculado con temperaturas y punto de rocío diarios será una aproximación atmosférica agregada, no VPD observado a mediodía.

## DGSIAP: comprobación preliminar

Los archivos usan CP1252. El campo de cultivo cambia de `Nomcultivo Sin Um` a `Nomcultivo` en 2021; se verificó `Idcultivo=5920000` (Cebada grano). El filtro inicial por nombre encontró un municipio homónimo Emiliano Zapata en Tlaxcala; se excluyeron sus seis registros porque las parcelas correspondientes están en Hidalgo. La integración debe usar estado + municipio, preferentemente claves verificadas, nunca municipio solo.

`siap-history-screening.csv` contiene exactamente nueve municipios × siete años, sin rendimientos derivados faltantes. El rendimiento se recalculó con toneladas producidas / hectáreas cosechadas; diferencias con el campo oficial inferiores a 0.005 t/ha son compatibles con redondeo. No se descargó ni se utilizará el cierre 2025 para generar predictores de rendimiento del ciclo objetivo.

Ejemplos comprobados: Chignahuapan tuvo rendimientos municipales 2018–2024 entre 2.65 y 3.45 t/ha, mientras el promedio observado del reto en 2025 es 4.48. Esto contradice las cotas históricas 4.10–4.65 propuestas sin datos en la investigación del colega: el histórico es contexto, no un límite para recortar predicciones. `siap-quality-screening.json` conserva los demás municipios.

## Puerta de admisión propuesta

1. Fuente pública original identificable, condiciones de uso/citación revisadas y archivo recuperable con hash, consulta, versión y fecha.
2. Cobertura del ciclo y del área, unidades, codificación, claves, resolución y valores centinela explícitos; ≥95% de cobertura de la variable en cada periodo utilizado y ninguna interpolación automática de lagunas mayores de siete días.
3. Separar idoneidad regional de idoneidad parcelaria: la resolución gruesa se registra y no se presenta como precisión local. Una fuente puede pasar integridad y fallar pertinencia para una variable concreta.
4. Registrar discrepancias físicas y con insumos oficiales; excluir la variable cuando no pueda justificarse su uso. No corregir sesgos para mejorar el ajuste al rendimiento observado.
5. Comparar la fuente con el modelo de datos del reto en las mismas particiones espaciales. La decisión forma parte del ajuste interno; la evaluación externa permanece independiente.
6. Aceptar una familia adicional solo con mejora del criterio predefinido y estabilidad regional. Si no mejora o su calidad es insuficiente, mantener exclusivamente los insumos del reto para el modelo final. Conservar los datos rechazados como evidencia, sin hacerlos dependencias de ejecución.

## Fuentes primarias

- NASA API diaria: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- NASA resolución y descargas: https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/
- NASA meteorología: https://power.larc.nasa.gov/docs/methodology/meteorology/
- DGSIAP datos abiertos: https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php
- ISRIC FAQ: https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_04.html
- ISRIC REST: https://rest.isric.org/
- ERA5-Land: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
- SMN EMA: https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s
- INEGI: https://www.inegi.org.mx/temas/edafologia/
