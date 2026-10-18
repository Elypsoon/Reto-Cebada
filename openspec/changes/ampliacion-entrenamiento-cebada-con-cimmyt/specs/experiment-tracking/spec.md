## ADDED Requirements

### Requirement: Evidencia y embudo de ampliación recuperables
El sistema SHALL vincular fuente primaria, hipótesis, auditoría, cohortes y ejecuciones mediante versiones y hashes. MUST publicar por etapa conteos de filas, rendimientos únicos, parcelas, productores, campañas, grupos y exclusiones, incluyendo el soporte efectivo de cada ajuste. SHALL distinguir registros publicados, descargados, armonizados y admitidos; los tamaños de tres esquemas o varias campañas de una misma parcela no SHALL presentarse como parcelas nuevas independientes.

#### Scenario: Reducción después de filtrar
- **WHEN** una fuente reporta cientos de rendimientos pero solo una parte supera unidades, ciclo, fechas, características y separación espacial
- **THEN** el informe conserva el embudo completo y utiliza en cada resultado únicamente su población realmente admitida.

### Requirement: Cierre condicionado de auditoría y experimentos auxiliares
El sistema SHALL mantener un estado separado para auditoría y para cada comparación predictiva, con resultados completados, fallidos, pendientes de acceso, omitidos o no viables y sus motivos. MUST marcar una comparación como completada y verificada únicamente si reproduce sus predicciones, métricas, controles y exclusiones requeridas. SHALL preservar archivos, código y contratos recuperables según condiciones de uso; si se limita redistribución, conservará originales localmente y publicará únicamente manifiestos y derivados permitidos. MUST mantener intactas la versión activa y las fases congeladas.

#### Scenario: Auditoría terminada sin entrenamiento viable
- **WHEN** la auditoría demuestra que no existen suficientes auxiliares compatibles
- **THEN** se puede cerrar la auditoría con ese resultado, pero la comparación predictiva se registra como no viable y no como completada con mejora cero.

#### Scenario: Recuperación sin red
- **WHEN** se recupera una ejecución completada desde sus artefactos locales autorizados
- **THEN** reproduce sus predicciones oficiales y métricas sin consultar CIMMYT ni NASA y verifica también cohortes, pesos, exclusiones y hashes.

#### Scenario: Acceso pendiente durante la implementación
- **WHEN** faltan archivos que requieren una acción del titular de acceso
- **THEN** se conserva el trabajo independiente y la tarea dependiente permanece pendiente con la acción necesaria, sin marcar como probada la ampliación ni simular sus resultados.

### Requirement: Revisión del supuesto espacial trazable antes de ajustes
El sistema MUST registrar `cimmyt-point-assumption-v2`, su autorización, fecha, fuentes y hashes de los artefactos de planificación, conservando el antecedente que exigía vértices verificables. SHALL separar referencia de origen desconocida de WGS84 asumido para análisis y guardar las tres políticas de admisión con conjuntos, hashes, conteos y viabilidad por ajuste. MUST congelar la revisión implementada antes del primer entrenamiento real y bloquear alteraciones bajo el mismo identificador. Una actualización documental no SHALL completar tareas de implementación ni comparaciones predictivas.

#### Scenario: Registros anteriores indican metadatos pendientes
- **WHEN** se implementa la revisión autorizada y existen informes o bloqueos del protocolo anterior
- **THEN** se conservan sus antecedentes y se reconcilia el estado actual con la admisión asumida, sin presentar los metadatos faltantes como encontrados ni el experimento como ejecutado.

#### Scenario: Cohorte local insuficiente tras la revisión
- **WHEN** la auditoría mantiene como máximo 29 rendimientos locales frente al mínimo fijado de 30
- **THEN** permanece no viable la comparación A04 local, con métricas nulas y sin cambiar el mínimo para justificar una ejecución.
