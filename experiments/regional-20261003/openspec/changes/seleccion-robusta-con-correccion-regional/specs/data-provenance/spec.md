## ADDED Requirements

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
