# parcel-features Specification

## Purpose

Representar cada parcela mediante variables temporales y ambientales compactas y reproducibles, respetando el ciclo objetivo, la calidad observacional y las diferencias entre sensores.

## Requirements

### Requirement: Unidad parcelaria y fecha de corte
El sistema SHALL producir una fila por parcela con variables para la estimación retrospectiva abril–octubre 2025. MUST excluir observaciones posteriores al 31 de octubre de 2025 y no convertir años históricos sin etiqueta en muestras de rendimiento.

#### Scenario: Observaciones posteriores a la cosecha objetivo
- **WHEN** un CSV contiene capturas de noviembre o diciembre de 2025
- **THEN** esas capturas quedan fuera de las variables del modelo para este ciclo.

### Requirement: Conservación de la identidad del sensor
El sistema SHALL mantener ramas identificables para Sentinel-2, Planet y VI6T de Landsat. MUST tratar los índices inexistentes de cada sensor como ausencia estructural, sin imputarlos ni simular reflectancias no entregadas.

#### Scenario: NDVI vacío de Landsat
- **WHEN** se procesan registros Landsat con NDVI vacío y VI6T disponible
- **THEN** únicamente VI6T participa en esa rama y no se fusiona con la curva NDVI de Sentinel o Planet.

### Requirement: Calidad y reconstrucción temporal trazable
El sistema SHALL registrar observaciones válidas, nubosidad, lagunas y método de reconstrucción por parcela e índice. MUST distinguir datos observados de interpolados, abstenerse de inventar fases cuando la señal sea insuficiente y no inferir aerosoles desde porcentaje de nubes. SHALL comparar el método vigente con reconstrucción por segmentos observados, conservar el soporte temporal de cada segmento y excluir de integrales y pendientes los intervalos sin soporte. MUST distinguir picos locales respaldados de un pico de temporada identificado y mantener faltantes las variables cuya definición requiera cobertura no disponible.

#### Scenario: Laguna prolongada alrededor del pico
- **WHEN** una curva carece de observaciones suficientes para establecer el pico con el criterio configurado
- **THEN** la variable fenológica se marca como no confiable o faltante y se conserva la información de cobertura.

#### Scenario: Laguna fuera de un segmento utilizable
- **WHEN** una parcela tiene segmentos utilizables separados por una laguna prolongada
- **THEN** se conservan los segmentos respaldados y sus integrales sin unir sus extremos ni presentar la suma como una integral observada de toda la temporada.

#### Scenario: Dos segmentos con máximos locales
- **WHEN** la cobertura no permite identificar el máximo de la temporada
- **THEN** se reporta la calidad y los máximos locales permitidos por el protocolo, sin inventar una fecha de pico global, antesis o llenado confirmado.

### Requirement: Fenología como indicador aproximado
El sistema SHALL identificar las fechas y áreas temporales derivadas como pico vegetativo e integral posterior al pico. MUST reservar las etiquetas de antesis y llenado confirmado para casos con evidencia agronómica independiente.

#### Scenario: Pico de EVI sin fecha observada de floración
- **WHEN** solo se dispone de una curva satelital
- **THEN** el resultado se presenta como pico estimado y no como fecha exacta de floración.

### Requirement: Extracción ambiental respetando escala y unidades
El sistema SHALL documentar reproyección, tratamiento de NoData, soporte espacial y unidades de clima, elevación y pendiente. MUST conservar el carácter mensual de CHIRPS/CHIRTS y el carácter regional de NASA.

#### Scenario: Solicitud de días de helada desde Tmin mensual
- **WHEN** se construyen variables con el promedio mensual de Tmin entregado
- **THEN** no se produce un conteo de heladas diarias ni una alerta de helada parcelaria.

### Requirement: Historia y transformaciones sin contaminación
El sistema SHALL preservar la procedencia y ventana de variables históricas y ejecutar imputación, escalado, selección supervisada y parámetros elegidos con rendimiento únicamente sobre el subconjunto de ajuste de cada partición.

#### Scenario: Variable seleccionada por correlación con rendimiento
- **WHEN** se evalúa una partición externa
- **THEN** la selección usa solo sus datos de entrenamiento, sin etiquetas del subconjunto externo ni de PREDICCION.

### Requirement: Representaciones y ablaciones comparables
El sistema SHALL identificar por versión las representaciones temporales, filtros de nubosidad, índices, sensores y variables de calidad utilizados en cada experimento. MUST conservar población, corte y covariables de control al comparar una sustitución de representación o ablación, y diferenciar señal espectral, soporte observacional y faltantes.

#### Scenario: Sustitución de representación histórica
- **WHEN** se reemplaza la reconstrucción con filtro de nubes de veinte por una de cuarenta por ciento
- **THEN** se registran la sustitución, calidad y faltantes correspondientes, conservando el resto del procedimiento para la comparación pareada.

#### Scenario: Ablación de calidad
- **WHEN** se retiran conteos de observaciones y otras variables de adquisición
- **THEN** permanecen las variables de señal declaradas, la variante se identifica separadamente y no se altera silenciosamente la selección de fuentes o los folds.

#### Scenario: Índice inexistente
- **WHEN** una ablación solicita un índice no suministrado para un sensor
- **THEN** se rechaza esa combinación o se registra su ausencia estructural sin sintetizar el índice ni fusionarlo con otro sensor.

### Requirement: Capacidad cartográfica de agua disponible por estrato
El sistema SHALL producir estimaciones de capacidad de agua disponible en milímetros para 0–30 y 30–60 cm a partir de retención volumétrica a presiones documentadas y espesores reales. MUST comprobar conversión de unidades, orden físico, máscara común y cobertura de todas las capas integrantes; no equiparar estas estimaciones con humedad actual, infiltración, escorrentía o agua disponible en una profundidad radicular observada. SHALL documentar por separado la sensibilidad a la presión elegida y la incertidumbre de las capas.

#### Scenario: Integración de estratos superiores
- **WHEN** existen datos válidos para 0–5, 5–15 y 15–30 cm
- **THEN** el resumen 0–30 cm pondera sus espesores y superficies válidas comunes, conserva milímetros y no calcula una media simple de los tres intervalos.

#### Scenario: Retención físicamente incoherente
- **WHEN** la retención a 1500 kPa supera la retención a la presión utilizada para capacidad de campo
- **THEN** el valor se marca inválido con motivo, sin recortarlo a cero como si fuera una medición coherente.

#### Scenario: Diferencia de quantiles de capas
- **WHEN** se calculan límites a partir de quantiles de retención
- **THEN** se reportan como envolventes de sensibilidad y no como un intervalo probabilístico calibrado de capacidad disponible.

### Requirement: Estrés conjunto con unidades y soporte temporal explícitos
El sistema SHALL conservar los efectos principales al comparar interacciones entre VPD, temperatura y señal hídrica comprobada. MUST aprender normalización y umbrales relativos únicamente con el entrenamiento de cada ajuste, vincular señales al mismo intervalo y registrar fechas, lagunas y soporte. SHALL distinguir indicadores estadísticos de coexposición de un diagnóstico fisiológico; MUST excluir la suma directa de kPa, grados Celsius e índices adimensionales y abstenerse de afirmar cierre estomático, detención de fotosíntesis o semanas exactas de pérdida de rendimiento.

#### Scenario: Cambio de etiquetas externas
- **WHEN** cambian las etiquetas de validación conservando el entrenamiento
- **THEN** permanecen iguales escalas, umbrales, interacciones y predicciones del ajuste.

#### Scenario: Semana sin señal satelital suficiente
- **WHEN** un intervalo semanal carece de las observaciones exigidas
- **THEN** no se cuenta como ausencia de estrés ni se interpola sobre la laguna; el resumen conserva su cobertura y permanece faltante si no alcanza soporte.

#### Scenario: Interacción favorable
- **WHEN** una interacción reduce el error frente al control con efectos principales
- **THEN** se informa una ganancia predictiva de desarrollo sin convertirla en evidencia de un mecanismo fisiológico medido.

### Requirement: Radiación separada de nubosidad observacional y extremos locales
El sistema SHALL identificar la radiación regional acumulada como energía por superficie y la nubosidad de captura como calidad de observación. MUST conservar los controles de calidad compartidos al evaluar radiación y no convertir una fracción de nubes satelitales en días nublados meteorológicos. MUST distinguir exposición térmica regional de una helada medida en parcela y no producir conteos diarios desde temperaturas mensuales.

#### Scenario: Serie regional sin mínimos bajo cero
- **WHEN** las mínimas diarias NASA no tienen días bajo cero
- **THEN** se registra esa propiedad de la serie sin afirmar ausencia de heladas en cada parcela ni generar una variable informativa inexistente.

#### Scenario: Comparación de radiación
- **WHEN** se añade radiación al control enriquecido
- **THEN** se mantienen fuente VPD, calendario, calidad satelital y población comunes para identificar el efecto incremental de radiación.
