# Spec Delta

## ADDED Requirements

### Requirement: Congelación posterior a la auditoría de adquisición
El sistema SHALL cerrar la auditoría de acceso, semántica, cobertura y calendario antes de congelar fuentes, bloques y catálogo predictivo. MUST conservar el historial de intentos y alternativas, con decisiones independientes del rendimiento; completar planificación o adquisición no equivale a ejecutar o validar un modelo.

#### Scenario: Fuente disponible después del primer ajuste
- **WHEN** una descarga o corrección habilita una fuente excluida por el protocolo utilizado
- **THEN** se exige otra versión de protocolo y ejecución, sin reabrir decisiones ni sobrescribir resultados anteriores.

#### Scenario: Límite de adquisición alcanzado
- **WHEN** una fuente agota su límite predeclarado de tiempo, bytes o intentos
- **THEN** se registra no viable con evidencia y continúan los bloques independientes, sin declarar descarga o cobertura que no se verificó.

### Requirement: Paquetes temporales aislados y cierre reproducible
El sistema SHALL conservar controles, descargas admitidas, tablas, modelos, contratos y resultados en una fase independiente y recuperable. MUST verificar la integridad de la versión activa y fases cerradas, recalcular métricas desde predicciones y recuperar las 59 consultas en un proceso nuevo sin red.

#### Scenario: Resultado completado sin elegibilidad
- **WHEN** una ejecución supera integridad, reproducción y recuperación pero falla los criterios predictivos
- **THEN** se registra completada y verificada con elegibilidad negativa; activación, despliegue y envío permanecen en falso.

#### Scenario: Hash protegido alterado
- **WHEN** cambia un archivo protegido de la activa o de una fase histórica
- **THEN** se informa la discrepancia y se bloquea el cierre verificable, sin actualizar el hash esperado para aceptar la alteración.

#### Scenario: Proceso interrumpido
- **WHEN** una ejecución no termina sus evaluaciones o recuperación
- **THEN** conserva evidencia parcial, permanece incompleta y no se presenta con la etiqueta de resultado verificado.
