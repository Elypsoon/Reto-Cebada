## ADDED Requirements

### Requirement: Evidencia vinculada a cada hipótesis prioritaria
El sistema SHALL conservar para cada mecanismo prioritario identificador de hipótesis, fuente primaria o evidencia local, título, URL o ruta, fecha de consulta, alcance de lectura, justificación de aplicabilidad, limitación y vínculo a control, protocolo y ejecución. MUST distinguir observaciones del proyecto, resultados publicados e inferencias de diseño; y registrar las métricas nuevas como pendientes hasta completar y verificar la ejecución.

#### Scenario: Modelo respaldado por benchmark externo
- **WHEN** una hipótesis cita un benchmark tabular o un cultivo de otra región
- **THEN** el registro identifica ese alcance y no asigna su mejora publicada al conjunto de AgroCebada.

#### Scenario: Acceso parcial a una fuente
- **WHEN** solo se verificó un resumen, documentación oficial o fragmento indexado
- **THEN** la evidencia identifica esa limitación y no afirma haber reproducido el método ni validado ecuaciones no consultadas.

### Requirement: Cierre de cobertura prioritaria sin exhaustividad ficticia
El sistema SHALL publicar al cierre una matriz con cada comparación prioritaria, estado real, control, fuentes, resultados por esquema, verificaciones y decisión, además de un inventario separado de alternativas diferidas y su motivo. MUST distinguir cierre administrativo de cobertura evaluada: un fallo o inviabilidad puede cerrar su ejecución pero no contará como prueba predictiva completada. SHALL indicar explícitamente cuándo faltan resultados obligatorios o pesos opcionales; no afirmará haber probado todas las posibilidades ni validado otra campaña.

#### Scenario: Comparación obligatoria fallida
- **WHEN** una comparación obligatoria falla y conserva artefactos parciales
- **THEN** el informe permite cerrar la incidencia con su motivo, mantiene la cobertura predictiva incompleta y no inventa métricas ni una ejecución verificada.

#### Scenario: Comparación opcional omitida
- **WHEN** un modelo fundacional carece de pesos verificables o excede los límites de recursos registrados
- **THEN** se conserva la omisión individual con motivo y continúan los experimentos obligatorios, sin transferirle resultados de otro modelo.

#### Scenario: Alternativa de prioridad secundaria
- **WHEN** una opción como radar nuevo o simulación completa de cultivo está fuera de la fase
- **THEN** se muestra como diferida con motivo y se mantiene separada de alternativas evaluadas con resultado negativo.

### Requirement: Recuperación de representaciones y modelos nuevos
El sistema SHALL conservar en cada paquete experimental datos necesarios, contrato, dependencias, transformaciones ajustadas, parámetros efectivos y una receta de recuperación local. Para modelos fundacionales MUST incluir identidad y hash del checkpoint y contexto de entrenamiento compatible; para modelos funcionales y jerárquicos MUST incluir bases, máscaras, reglas de soporte y estadísticas aprendidas. SHALL verificar en un proceso nuevo métricas desde predicciones y las 59 consultas con el mismo orden, identificación y tolerancia registrada, sin descargar pesos ni reajustar transformaciones durante la recuperación.

#### Scenario: Contexto incompatible con checkpoint
- **WHEN** cambia el hash del modelo fundacional, contexto, dependencia requerida o esquema de variables
- **THEN** se rechaza la recuperación y la ejecución no obtiene verificación positiva ni elegibilidad.

#### Scenario: Recuperación funcional completa
- **WHEN** se recupera un paquete funcional o jerárquico compatible
- **THEN** sus 59 predicciones se reproducen en un proceso nuevo y se mantiene la versión activa íntegra.
