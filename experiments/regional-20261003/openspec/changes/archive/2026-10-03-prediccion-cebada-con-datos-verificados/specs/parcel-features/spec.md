# Spec Delta

## Purpose

Representar cada parcela mediante variables temporales y ambientales compactas y reproducibles, respetando el ciclo objetivo, la calidad observacional y las diferencias entre sensores.

## ADDED Requirements

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
El sistema SHALL registrar observaciones válidas, nubosidad, lagunas y método de reconstrucción por parcela e índice. MUST distinguir datos observados de interpolados, abstenerse de inventar fases cuando la señal sea insuficiente y no inferir aerosoles desde porcentaje de nubes.

#### Scenario: Laguna prolongada alrededor del pico
- **WHEN** una curva carece de observaciones suficientes para establecer el pico con el criterio configurado
- **THEN** la variable fenológica se marca como no confiable o faltante y se conserva la información de cobertura.

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

