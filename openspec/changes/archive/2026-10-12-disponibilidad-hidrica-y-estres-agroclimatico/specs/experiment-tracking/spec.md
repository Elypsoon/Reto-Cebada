## ADDED Requirements

### Requirement: Evidencia y cierre de la fase hídrica
El sistema SHALL relacionar cada hipótesis hídrica con auditoría de datos, control, protocolo congelado y resultado real. MUST separar fuentes existentes, verificadas, no viables y pendientes; variables disponibles, elegibles y utilizadas en cada ajuste; y antecedente, diagnóstico aislado y combinado elegible. SHALL conservar comparaciones pareadas por esquema, decisiones internas por bloque, diferencias por parcela y paquetes recuperables, con la advertencia de reutilización de las mismas etiquetas.

#### Scenario: Suelo no adquirido
- **WHEN** la auditoría de acceso no recupera capas válidas
- **THEN** el informe publica el motivo y los bloques no ejecutados sin adjudicarles métricas ni afirmar que se descartó científicamente el papel del suelo.

#### Scenario: Variable mostrada pero no utilizada
- **WHEN** pendiente o NDWI existe en las tablas pero no participa en el modelo final
- **THEN** el informe identifica su disponibilidad y su exclusión final, evitando afirmar que el predictor usa esa variable.

#### Scenario: Cierre verificable
- **WHEN** una ejecución recupera contratos, modelos y 59 consultas en un proceso nuevo sin red y reproduce métricas externas
- **THEN** se registra completada y verificada, con elegibilidad separada y activación, despliegue y envío en falso.
