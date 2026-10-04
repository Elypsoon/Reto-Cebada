# Spec Delta

## Purpose

Permitir a productores, equipo y evaluadores consultar y ejecutar la estimación del ciclo 2025 por parcela, comprender sus datos y descargar resultados con unidades y limitaciones claras.

## ADDED Requirements

### Requirement: Consulta geográfica del conjunto
La aplicación SHALL mostrar las 197 parcelas en un mapa y permitir búsqueda por identificador y filtros por estado, municipio y conjunto, conservando la distinción entre rendimiento observado y estimado.

#### Scenario: Consulta de parcela oculta
- **WHEN** se selecciona una parcela de PREDICCION
- **THEN** se muestra su estimación y nunca un supuesto rendimiento real no proporcionado.

### Requirement: Ejecución interactiva de inferencia
La aplicación SHALL permitir ejecutar el modelo validado para una parcela disponible sin reentrenarlo, mostrando rendimiento en t/ha, superficie en ha, producción estimada en toneladas, versión y fecha de corte.

#### Scenario: Estimación desde la ficha
- **WHEN** el usuario solicita calcular el rendimiento de una parcela con variables compatibles
- **THEN** se ejecuta el artefacto del modelo y la producción se calcula como rendimiento estimado multiplicado por superficie.

### Requirement: Curvas y calidad comprensibles
La aplicación SHALL mostrar series diferenciadas por sensor, datos observados y reconstruidos, cobertura de nubes/lagunas y fuentes utilizadas. MUST denominar la estimación como retrospectiva del ciclo 2025.

#### Scenario: Curva reconstruida con observaciones escasas
- **WHEN** una variable procede de una curva de calidad insuficiente
- **THEN** la ficha muestra su limitación y no presenta una fecha exacta de floración ni un pronóstico de cosechas futuras.

### Requirement: Evidencia del modelo y descarga
La aplicación SHALL mostrar métricas de validación espacial globales y por región, fuentes admitidas/excluidas, y permitir descargar el conjunto oficial de 59 predicciones y un resumen de ficha con versión y unidades.

#### Scenario: Descarga del conjunto oficial
- **WHEN** el usuario solicita el archivo para evaluación
- **THEN** obtiene las 59 filas validadas de PREDICCION con identificador y rendimiento, aunque tenga aplicado un filtro visual sobre el mapa.

### Requirement: Operación con artefactos locales
La aplicación SHALL operar con datos y modelo locales compatibles aunque los servicios externos estén fuera de línea. MUST explicar errores de compatibilidad o falta de datos sin inventar resultados ni cambiar silenciosamente de modelo.

#### Scenario: Modelo y tabla de variables de versiones distintas
- **WHEN** la tabla no coincide con el contrato de variables del artefacto cargado
- **THEN** el cálculo se bloquea con un mensaje claro y no devuelve una estimación parcial.

