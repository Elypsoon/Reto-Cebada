# Spec Delta

## ADDED Requirements

### Requirement: Control equivalente para las comparaciones temporales
El sistema SHALL conservar el control activo y comparar bloques temporales contra un control de fase que comparta familias, representaciones, selección, parámetros, fuentes de base, etiquetas y particiones. MUST separar la diferencia entre métodos del aporte incremental de cada bloque y congelar las alternativas antes del primer ajuste.

#### Scenario: Control de fase peor que la activa
- **WHEN** el control experimental tiene un error superior al control activo recuperado
- **THEN** se muestra esa diferencia y no se atribuye automáticamente a la fuente nueva la distancia entre el candidato y la activa.

#### Scenario: Comparación de interacciones
- **WHEN** se evalúa estrés conjunto
- **THEN** su pareja conserva los mismos efectos principales, clima, señal y soporte, de modo que la diferencia identifica únicamente la adición de interacciones.

#### Scenario: Sin bloque público viable
- **WHEN** ninguna entrada nueva supera su auditoría previa
- **THEN** se conservan controles y exclusiones, el combinado queda como respaldo sin nueva información y no se declara mejora de esta fase.

### Requirement: Elegibilidad temporal exclusiva del combinado
El sistema SHALL evaluar elegibilidad únicamente del combinado F05 predeclarado, con las mismas 138 etiquetas y los tres esquemas espaciales de referencia. MUST exigir estabilidad frente a la media regional y a la activa, protección estatal y recuperación íntegra; resultados aislados no sustituirán retrospectivamente al combinado.

#### Scenario: Criterios completos
- **WHEN** se decide elegibilidad de F05
- **THEN** se exigen RMSE al menos 2% menor que regional en el principal y al menos dos esquemas, media de razones frente a regional ≤0.98 y ninguna >1.05; MAE estatal no más de 10% superior a regional donde haya al menos diez etiquetas; RMSE principal al menos 2% menor que la activa y ninguna razón frente a ella >1.05; tres esquemas completos, pruebas, controles y 59 consultas recuperables.

#### Scenario: Información nueva no utilizada
- **WHEN** el ajuste final utiliza solo el respaldo o no admite ningún bloque nuevo
- **THEN** la ejecución conserva su resultado pero su elegibilidad de mejora temporal es negativa, aunque el respaldo tenga métricas favorables.

#### Scenario: Diagnóstico aislado favorable
- **WHEN** una variante aislada obtiene menor error externo que F05
- **THEN** se conserva como diagnóstico y no se cambia F05, su catálogo ni sus pesos utilizando esos resultados.

#### Scenario: Falta una evaluación o estado perjudicado
- **WHEN** falta un esquema obligatorio o se excede el límite estatal en alguno
- **THEN** la elegibilidad es negativa y no se elimina el esquema o estado para permitir la promoción.
