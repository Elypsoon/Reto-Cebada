# Spec Delta

## Purpose

Garantizar que los datos usados para estimar el rendimiento sean identificables, verificables y adecuados para su escala de uso, con una ruta operativa basada exclusivamente en los insumos del reto.

## ADDED Requirements

### Requirement: Inventario y procedencia recuperable
El sistema SHALL registrar para cada fuente ubicación, proveedor, consulta o archivo original, versión cuando exista, fecha de adquisición, hash, unidades, resolución, cobertura, licencia o condiciones de uso y decisión de admisión.

#### Scenario: Recuperación de una versión de datos
- **WHEN** se consulta una ejecución de entrenamiento o inferencia
- **THEN** sus fuentes se identifican por manifiesto y hash y sus transformaciones quedan asociadas a esa versión.

### Requirement: Separación oficial del conjunto
El sistema MUST conservar 197 identificadores únicos, 138 etiquetas de ENTRENAMIENTO y 59 casos de PREDICCION sin rendimiento conocido, y rechazar incoherencias de claves, áreas o asignación entre archivos oficiales.

#### Scenario: Etiqueta inesperada en predicción
- **WHEN** una entrada contiene rendimiento para un caso asignado a PREDICCION
- **THEN** la importación se detiene con un diagnóstico y ese rendimiento no entra al entrenamiento ni a la evaluación.

#### Scenario: Identificadores duplicados o incompatibles
- **WHEN** el cruce de parcelas y etiquetas contiene duplicados, áreas discrepantes o identificadores no reconocidos
- **THEN** el sistema informa los casos y no genera silenciosamente una tabla multiplicada o incompleta.

### Requirement: Admisión explícita de fuentes externas
El sistema SHALL admitir una fuente externa solo tras verificar procedencia, cobertura, unidades, resolución, integridad y pertinencia de cada variable. SHALL distinguir datos regionales de mediciones de parcela y registrar las exclusiones y sus motivos.

#### Scenario: Serie completa con resolución regional
- **WHEN** NASA ofrece una serie completa pero su celda cubre numerosas parcelas
- **THEN** la fuente se clasifica como contexto regional y no como evidencia de un evento observado dentro de una parcela.

#### Scenario: Calidad o acceso insuficiente
- **WHEN** una fuente carece de metadatos indispensables, no es recuperable o no es adecuada para la variable prevista
- **THEN** esa variable queda excluida y se conserva el motivo sin inventar valores sustitutivos.

### Requirement: Ruta sin datos externos
El sistema SHALL permitir construir variables, evaluar, entrenar e inferir con los insumos del reto aunque no se admita ninguna fuente externa. La aplicación MUST operar con una versión local validada sin consultas a proveedores durante la inferencia.

#### Scenario: Proveedor externo fuera de servicio
- **WHEN** un proveedor falla y existe una versión íntegra validada
- **THEN** se utiliza esa versión sin red; si no existe, se produce la variante oficial con su propio modelo compatible y se informa el conjunto de fuentes utilizado.

### Requirement: Claves municipales compuestas
El sistema SHALL relacionar estadísticas municipales mediante estado y municipio verificados, conservar ciclo, modalidad y cultivo, y separar el histórico 2018–2024 del rendimiento objetivo 2025.

#### Scenario: Municipios homónimos
- **WHEN** existen registros de Emiliano Zapata en Hidalgo y Tlaxcala
- **THEN** las parcelas de Hidalgo reciben únicamente estadísticas del municipio correspondiente en Hidalgo.

