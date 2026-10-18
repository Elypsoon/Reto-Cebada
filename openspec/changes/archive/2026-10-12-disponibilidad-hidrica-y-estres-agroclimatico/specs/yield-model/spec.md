## ADDED Requirements

### Requirement: Comparaciones hídricas y elegibilidad del combinado
El sistema SHALL comparar controles recuperables y variantes acotadas de suelo, estrés y radiación con las mismas 138 etiquetas, corte y tres esquemas espaciales predefinidos. MUST congelar controles, fórmulas, reglas de viabilidad, familias, parámetros, subconjuntos del combinado y criterios antes del primer ajuste predictivo de la fase. SHALL evaluar elegibilidad únicamente del combinado W05, sin modificar decisiones E08/P06 ni seleccionarlo retrospectivamente entre ganadores externos.

La elegibilidad W05 MUST exigir tres esquemas completos, reducción de RMSE de al menos 2% frente a la media regional en el principal y en al menos dos esquemas, media de razones frente a regional no superior a 0.98 y ninguna razón superior a 1.05; aumento de MAE estatal no superior a 10% frente a regional para estados con al menos diez etiquetas en cada esquema; reducción principal de al menos 2% frente al control activo seleccionado y ninguna razón frente a ese control superior a 1.05; controles reproducidos, pruebas y recuperación de las 59 consultas. MUST distinguir esta elegibilidad puntual de intervalos, activación y validación independiente de otra campaña.

#### Scenario: Fuente no viable antes del entrenamiento
- **WHEN** suelo o definición hídrica no cumple su auditoría previa
- **THEN** el catálogo conserva esa exclusión mediante una regla registrada, continúa con bloques viables y no introduce una fuente o índice sustituto después de revisar errores.

#### Scenario: Bloque disponible sin ganancia interna
- **WHEN** un bloque no mejora la validación interna con la estabilidad y protección estatal exigidas
- **THEN** el combinado utiliza un subconjunto elegible o la referencia de respaldo predeclarada y conserva el rechazo de ese bloque.

#### Scenario: Combinado que reproduce únicamente el control
- **WHEN** no se admite ningún bloque nuevo durante el ajuste completo
- **THEN** se conserva un resultado válido de respaldo, pero no se declara mejora atribuible a información hídrica nueva ni promoción de esta fase.

#### Scenario: Ganancia dependiente de un esquema
- **WHEN** W05 mejora en el principal pero deteriora más de 5% frente a la referencia requerida en otro esquema
- **THEN** se rechaza su elegibilidad y se mantienen íntegros errores, fuentes y predicciones de los tres esquemas.
