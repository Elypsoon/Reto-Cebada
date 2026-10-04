# Spec Delta

## Purpose

Estimar rendimiento parcelario en toneladas por hectárea mediante modelos comparados honestamente fuera de muestra, con resultados reproducibles para las 59 parcelas del conjunto oficial.

## ADDED Requirements

### Requirement: Evaluación independiente por parcela
El sistema SHALL obtener una predicción externa por cada parcela etiquetada mediante particiones espaciales reproducibles. MUST mantener todas las observaciones de una parcela en el mismo grupo y realizar el ajuste de variables, modelos y ensambles dentro del entrenamiento externo.

#### Scenario: Serie temporal con numerosas capturas
- **WHEN** una parcela tiene decenas de capturas satelitales
- **THEN** sus capturas no se reparten entre entrenamiento y validación como ejemplos independientes.

### Requirement: Comparación de referencias y fuentes
El sistema SHALL comparar modelos contra referencias globales y regionales ajustadas con datos de entrenamiento y contra una variante completa que use solo insumos del reto. MUST elegir fuentes adicionales y complejidad con un criterio registrado antes de revisar resultados.

#### Scenario: Fuente adicional sin beneficio estable
- **WHEN** una fuente no cumple calidad o no mejora el criterio predefinido dentro de la evaluación anidada
- **THEN** el modelo seleccionado prescinde de ella y el reporte conserva la comparación y el motivo.

### Requirement: Reporte de desempeño fuera de muestra
El sistema SHALL reportar RMSE y MAE en t/ha, R² global sobre el vector de predicciones externas, métricas por estado y superficie, composición de particiones y variabilidad del error. MUST distinguir estas métricas de resultados del conjunto oculto.

#### Scenario: Evaluación regional difícil
- **WHEN** una partición presenta R² negativo o un estado tiene error elevado
- **THEN** el reporte muestra ese resultado sin sustituirlo por métricas de entrenamiento o promedios que oculten el fallo.

### Requirement: Incertidumbre evaluada
El sistema SHALL publicar intervalos solo cuando estén calibrados sin utilizar el subconjunto evaluado y se reporte cobertura y amplitud empíricas. MUST indicar cuando un intervalo no está disponible o no cumple la cobertura configurada.

#### Scenario: Intervalo nominal sin cobertura suficiente
- **WHEN** un intervalo nominal de 90% no alcanza el criterio de cobertura definido
- **THEN** no se presenta como un intervalo confiable de 90% y la salida informa esa limitación.

### Requirement: Exportación oficial y reproducibilidad
El sistema SHALL exportar exactamente 59 filas de PREDICCION, con identificador oficial único y rendimiento finito en t/ha, vinculadas a versión de datos, variables, modelo, dependencias y semilla. MUST rechazar artefactos de modelo y variables incompatibles.

#### Scenario: Exportación incompleta
- **WHEN** falta una parcela o existe una predicción duplicada o no finita
- **THEN** la exportación final se bloquea e informa los casos pendientes.

### Requirement: Interpretación de contribuciones
El sistema SHALL describir las explicaciones como contribuciones al resultado del modelo y comprobar su estabilidad fuera de muestra. MUST evitar presentarlas como causas demostradas, decisiones crediticias o garantías productivas.

#### Scenario: Coordenadas con gran contribución
- **WHEN** la ubicación domina una explicación
- **THEN** se informa su papel y se contrasta la variante sin ubicación mediante evaluación espacial; no se afirma causalidad agronómica.

