## ADDED Requirements

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
