# data-provenance Specification

## Purpose

Garantizar que los datos usados para estimar el rendimiento sean identificables, verificables y adecuados para su escala de uso, con una ruta operativa basada exclusivamente en los insumos del reto.

## Requirements

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

### Requirement: Diagnóstico regional trazable
El sistema SHALL producir un diagnóstico de errores externos, etiquetas, superficie, faltantes, cobertura satelital y soporte de rásteres por estado y municipio, con detalle recuperable por identificador y esquema espacial. MUST incluir Hidalgo y distinguir una observación revisable de un error demostrado; registrar conteos y advertir cuando el tamaño municipal no permite conclusiones estables.

#### Scenario: Concentración de error en Hidalgo
- **WHEN** Hidalgo concentra una parte elevada del error
- **THEN** el diagnóstico muestra su contribución, casos y calidad de datos sin afirmar automáticamente que sus etiquetas son incorrectas.

#### Scenario: Municipio con pocas etiquetas
- **WHEN** un municipio dispone de menos de diez etiquetas evaluadas
- **THEN** se publica su tamaño y diagnóstico descriptivo con advertencia de muestra pequeña, sin utilizar su error como evidencia suficiente de una regla predictiva municipal.

### Requirement: Correcciones y exclusiones sustentadas en originales
El sistema MUST conservar los archivos originales y registrar para cada corrección o exclusión de variables u observaciones de fuentes identificador, campo, valor anterior/nuevo cuando corresponda, fuente comprobable, motivo, fecha y hashes de versiones. MUST rechazar correcciones sustentadas únicamente en errores del modelo, reducir artificialmente etiquetas o copiar rendimientos municipales sobre parcelas. SHALL mantener la separación oficial de 197 identificadores, 138 etiquetas y 59 casos ocultos; si una discrepancia demostrada impide cumplirla, MUST bloquear la comparación principal y registrar la necesidad de revisar ese alcance. Si una corrección verificada altera valores o variables del conjunto de evaluación SHALL recalcular referencias y candidatos sobre exactamente la misma versión y distinguir esa comparación de la anterior.

#### Scenario: Etiqueta difícil sin evidencia de error
- **WHEN** una parcela tiene un residuo elevado pero no hay evidencia de una discrepancia con los originales
- **THEN** conserva su etiqueta y participación en la evaluación principal.

#### Scenario: Error de transformación demostrado
- **WHEN** se demuestra que una transformación no reprodujo un valor o unidad del original
- **THEN** se corrige en una versión derivada trazable, se conserva el original y se vuelven a evaluar referencias y candidatos con las mismas filas de esa versión.

#### Scenario: Cambio del conjunto evaluado
- **WHEN** una corrección verificada modifica el valor de una etiqueta o variable
- **THEN** el reporte identifica las versiones y no atribuye una reducción de error por retirar casos al mérito predictivo del nuevo modelo.

#### Scenario: Discrepancia que invalida una etiqueta oficial
- **WHEN** un error demostrado impide mantener las 138 etiquetas oficiales válidas
- **THEN** se bloquea la comparación principal y se documenta el caso sin continuar con un conjunto reducido como si cumpliera el alcance vigente.

### Requirement: Auditoría semántica de señales y metadatos agronómicos
El sistema SHALL registrar por sensor la definición comprobada, bandas, unidades, disponibilidad y procedencia del índice usado como señal hídrica. MUST distinguir una columna denominada NDWI de una medición de agua foliar y registrar expresamente una fórmula desconocida. SHALL inventariar evidencia identificable por parcela y campaña de variedad, siembra y temperatura local; MUST mantener su ausencia como desconocida y no deducir esos campos de rendimiento, estado o municipio.

#### Scenario: NDWI sin fórmula verificable
- **WHEN** los originales describen NDWI sin especificar bandas y ecuación
- **THEN** conserva su identidad de señal espectral y no habilita la interpretación fisiológica ni el bloque experimental que requiere una señal hídrica vegetal comprobada.

#### Scenario: Variedad no suministrada
- **WHEN** solo existe una lista de variedades recomendadas para la región
- **THEN** el registro conserva variedad parcelaria desconocida y no asigna una variedad por recomendación regional.

#### Scenario: Evidencia nueva de siembra o helada
- **WHEN** se encuentra información local comprobable durante la auditoría
- **THEN** se registra alcance, campaña, escala y cobertura, sin incorporarla al catálogo predictivo congelado de esta fase; su evaluación requiere un protocolo posterior.

### Requirement: Admisión y recuperación de cartografía de retención
El sistema SHALL admitir cartografía de retención únicamente tras comprobar proveedor, versión, fecha de publicación/adquisición, licencia, unidades, significado volumétrico, presiones, profundidades, resolución nativa, incertidumbre y cobertura. MUST conservar los originales recuperables localmente, los hashes y las máscaras de soporte; diferenciar la estimación cartográfica de una muestra de suelo y el dato estático de una observación de humedad de 2025. MUST resolver viabilidad sin etiquetas antes de congelar el catálogo y conservar la población completa cuando existan faltantes.

#### Scenario: Servicio de consulta no disponible
- **WHEN** la API está fuera de servicio
- **THEN** se utiliza una vía oficial alternativa verificada y acotada a la zona necesaria o se registra el bloque como no viable, sin fabricar suelo, cambiar de proveedor silenciosamente ni detener las comparaciones independientes.

#### Scenario: Cobertura parcial de una parcela
- **WHEN** una capa no alcanza el soporte de superficie exigido por el protocolo
- **THEN** se conserva la parcela, su cobertura y el valor faltante, sin presentar la media parcial como suelo completo ni retirar su etiqueta de evaluación.

#### Scenario: Producto publicado después de la campaña
- **WHEN** la cartografía estática procede de una versión posterior a 2025
- **THEN** se declara su fecha y el uso retrospectivo con información posterior, sin afirmar disponibilidad previa a cosecha ni validación de un pronóstico histórico.
