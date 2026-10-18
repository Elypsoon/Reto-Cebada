## ADDED Requirements

### Requirement: Auditoría recuperable de rendimientos externos de cebada
El sistema SHALL verificar acceso, versión, archivos originales, condiciones de uso, hashes y diccionario del conjunto CIMMYT México 2012–2022 antes de admitir observaciones. MUST conservar un embudo de conteos desde registros originales hasta rendimientos de grano en t/ha, con año, ciclo, modalidad, estado, parcela, unidad original, transformación y motivo de exclusión recuperables. MUST distinguir una cifra publicada de un conteo efectivamente auditado y no presentar los 968 registros reportados como nuevas etiquetas admitidas.

#### Scenario: Descarga condicionada
- **WHEN** el proveedor exige una cuenta, acuerdo o acceso que todavía no está disponible
- **THEN** se registra acceso pendiente y no se afirma disponer de los archivos ni haber probado la ampliación predictiva.

#### Scenario: Producto o unidad incompatibles
- **WHEN** un registro corresponde a forraje, a otro cultivo o a una unidad sin conversión documentada a rendimiento de grano en t/ha
- **THEN** queda excluido de entrenamiento y permanece en el embudo con su motivo, sin aplicar factores agronómicos supuestos.

#### Scenario: Pérdida total documentada
- **WHEN** un rendimiento cero corresponde a una pérdida real y cumple los demás criterios de admisión
- **THEN** se conserva como cero y no se reemplaza por un faltante ni por una media; tampoco se aplican límites del proveedor a las etiquetas oficiales.

### Requirement: Población auxiliar separada y uniones sin multiplicación
El sistema MUST mantener intacto el maestro oficial de 197 identificadores, con sus 138 etiquetas y 59 consultas sin etiqueta. SHALL representar cada observación auxiliar mediante claves con espacio de nombres de fuente, productor, parcela, bitácora, campaña y producto; registrar cardinalidad de uniones y resolver duplicados antes de entrenar. MUST impedir que una unión muchos-a-muchos, un registro de resiembra o varias líneas del mismo rendimiento creen etiquetas independientes artificiales. SHALL contar separadamente rendimientos, parcelas, productores, campañas y grupos de dependencia.

#### Scenario: Coincidencia de identificadores entre fuentes
- **WHEN** una clave auxiliar tiene el mismo texto que un identificador oficial
- **THEN** sus espacios de nombres impiden la colisión y la observación no modifica el maestro, su etiqueta ni su partición.

#### Scenario: Varias líneas de cosecha
- **WHEN** varias filas describen la misma parcela, campaña y producto
- **THEN** se conserva una observación únicamente si la documentación permite deduplicar o agregar producción y área sin doble conteo; en caso contrario el caso se excluye como ambiguo.

#### Scenario: Campañas repetidas
- **WHEN** una parcela tiene rendimientos reales de varios años
- **THEN** cada campaña conserva su etiqueta observada y todas comparten su grupo de dependencia, sin copiar el rendimiento de 2025 hacia otros años.

### Requirement: Admisión contextual explícita de cohortes auxiliares
El sistema SHALL construir cohortes predeclaradas de cebada de grano, primavera–verano, temporal y campañas 2012–2022, distinguiendo Puebla/Hidalgo/Tlaxcala de México. MUST verificar fechas y cobertura compatibles con abril–octubre del año correspondiente, y excluir de estas cohortes ciclos, modalidades y fechas faltantes o incompatibles. SHALL registrar método de medición y base de humedad cuando consten, y las incertidumbres restantes frente al objetivo oficial. MUST marcar como desconocida la modalidad oficial si sus originales no la documentan; las estadísticas municipales no la demuestran.

#### Scenario: Rendimiento de invierno bajo riego
- **WHEN** el registro es de otoño–invierno o riego
- **THEN** queda fuera de ambas cohortes de esta fase y su disponibilidad no se presenta como compatibilidad con el objetivo oficial.

#### Scenario: Compatibilidad parcial
- **WHEN** grano y unidades son verificables pero la base de humedad oficial o la modalidad parcelaria no están documentadas
- **THEN** el informe declara esa incertidumbre y el experimento se identifica como transferencia diagnóstica, sin inventar una corrección de humedad ni afirmar equivalencia agronómica completa.

### Requirement: Evidencia geográfica distinguida de supuestos autorizados
El sistema SHALL conservar coordenadas originales y distinguir datum, semántica del punto y precisión documentados de los desconocidos. MUST vincular la búsqueda de metadatos a fuentes primarias, fecha y revisión consultada. SHALL permitir puntos aproximados sin datum verificado únicamente bajo el protocolo diagnóstico autorizado `cimmyt-point-assumption-v2`, registrando WGS84 como supuesto de análisis, referencia de origen desconocida y márgenes experimentales. MUST impedir que el número de decimales, coherencia con México o herramienta de captura se presenten como prueba de precisión, datum o centroide.

#### Scenario: Búsqueda sin metadatos suficientes
- **WHEN** las fuentes revisadas no resuelven el datum o la derivación de los puntos del Excel
- **THEN** se registra el alcance de la búsqueda y la incertidumbre; la admisión diagnóstica usa el supuesto autorizado sin afirmar que los metadatos no existen en ningún otro lugar.

#### Scenario: Evidencia posterior incompatible
- **WHEN** aparece documentación de una referencia incompatible o incertidumbre mayor que la política principal
- **THEN** se bloquea el ajuste dependiente y se exige revisión del protocolo antes de entrenar, sin corregir coordenadas o márgenes silenciosamente bajo una versión congelada.
