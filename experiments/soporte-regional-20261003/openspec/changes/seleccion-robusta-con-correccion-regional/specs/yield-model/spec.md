## ADDED Requirements

### Requirement: Corrección parcelaria sobre una referencia regional
El sistema SHALL comparar la media regional con estimadores de rendimiento formados por una referencia regional y una corrección parcelaria regularizada. MUST ajustar medias regionales/globales, residuos objetivo, imputación, selección supervisada, escala, corrección y su intensidad exclusivamente con las etiquetas del subconjunto de ajuste de cada partición. SHALL conservar la predicción en t/ha y registrar separadamente referencia y corrección.

#### Scenario: Contaminación deliberada de etiquetas externas
- **WHEN** se modifican las etiquetas externas manteniendo intacto el entrenamiento
- **THEN** las medias aprendidas, variables elegidas, configuración, pesos y predicciones del modelo ajustado permanecen iguales.

#### Scenario: Estado ausente en entrenamiento
- **WHEN** el estimador regional recibe una parcela de un estado sin etiquetas en su entrenamiento
- **THEN** devuelve la media global aprendida sin una corrección regional inventada y registra el uso de esa referencia.

#### Scenario: Corrección anulada
- **WHEN** la intensidad de corrección es cero
- **THEN** la salida reproduce exactamente la referencia regional o su sustitución global aplicable.

### Requirement: Selección acotada y política recuperable
El sistema SHALL registrar antes de entrenar el conjunto de candidatos, representaciones, parámetros, ensambles, fuentes, semillas, particiones y criterios de admisión de la fase. MUST limitar la búsqueda principal a dos familias predictivas, dos representaciones temporales, referencias global/regional y correcciones regularizadas; los ensambles SHALL utilizar únicamente combinaciones pequeñas declaradas. La elección de parámetros, componentes y fuentes MUST utilizar exclusivamente evaluación interna y conservar las alternativas rechazadas con sus motivos.

#### Scenario: Ganador aparente en evaluación externa
- **WHEN** una familia aislada obtiene menor error externo que el procedimiento de selección
- **THEN** se publica como diagnóstico y no se sustituye retrospectivamente la selección ni se recalculan pesos con esas etiquetas.

#### Scenario: Fuente adicional sin beneficio
- **WHEN** NASA, DGSIAP o su combinación no cumple la política interna
- **THEN** la opción queda excluida del ajuste correspondiente y sigue disponible una variante completa con solo insumos oficiales.

### Requirement: Promoción condicionada a estabilidad espacial
El sistema SHALL evaluar el mismo procedimiento congelado en tres esquemas espaciales predefinidos y calcular en cada uno una predicción externa por cada una de las 138 etiquetas. MUST promover una versión únicamente si reduce el RMSE al menos 2% frente a la media regional del esquema principal y de al menos dos de los tres esquemas, si la media de las tres razones RMSE-modelo/RMSE-regional no supera 0.98 y ninguna razón supera 1.05. MUST limitar en cada esquema el aumento de MAE por estado a 10% frente a la referencia regional cuando ese estado tiene al menos diez etiquetas evaluadas. También SHALL exigir reproducción de exportación, contratos y pruebas antes de promover.

#### Scenario: Mejora dependiente de una partición
- **WHEN** el nuevo procedimiento supera la referencia únicamente en el esquema principal
- **THEN** la promoción se rechaza, se conservan los resultados de los tres esquemas y la versión vigente permanece recuperable.

#### Scenario: Ganancia global con perjuicio regional
- **WHEN** el RMSE cumple el umbral global pero el MAE de un estado elegible aumenta más de 10% en un esquema
- **THEN** se rechaza la promoción y se identifica el estado y esquema responsables.

#### Scenario: Partición no viable
- **WHEN** un esquema no alcanza los tamaños mínimos definidos antes del experimento
- **THEN** se registra como no viable y no se elimina del denominador ni se reemplaza después de consultar errores para permitir una promoción.

#### Scenario: Experimento sin mejora suficiente
- **WHEN** ningún procedimiento registrado satisface todos los criterios
- **THEN** se conserva el experimento como resultado negativo sin afirmar éxito predictivo ni reemplazar automáticamente modelos, contratos o exportaciones vigentes.

## MODIFIED Requirements

### Requirement: Reporte de desempeño fuera de muestra
El sistema SHALL reportar RMSE y MAE en t/ha, R² global sobre el vector de predicciones externas, métricas por estado y superficie, composición de particiones y variabilidad del error. MUST distinguir estas métricas de resultados del conjunto oculto. SHALL publicar además métricas y decisiones de promoción por esquema espacial, diferencias frente a la referencia regional y la ejecución anterior, así como frecuencias de selección y admisión de fuentes. MUST declarar que la reutilización de las mismas etiquetas durante el desarrollo no constituye un test independiente ni validación de otra campaña; no tratará las predicciones repetidas de una parcela como nuevas etiquetas independientes.

#### Scenario: Evaluación regional difícil
- **WHEN** una partición presenta R² negativo o un estado tiene error elevado
- **THEN** el reporte muestra ese resultado sin sustituirlo por métricas de entrenamiento o promedios que oculten el fallo.

#### Scenario: Tres evaluaciones de las mismas parcelas
- **WHEN** se publican los tres vectores de predicciones externas
- **THEN** cada esquema se identifica por separado y no se afirma disponer de 414 etiquetas independientes ni de un test externo nuevo.

### Requirement: Interpretación de contribuciones
El sistema SHALL describir las explicaciones como contribuciones al resultado del modelo y comprobar su estabilidad fuera de muestra. MUST evitar presentarlas como causas demostradas, decisiones crediticias o garantías productivas. Para un modelo con corrección regional SHALL mostrar la referencia, intensidad y corrección total de manera que su composición reproduzca la predicción; MUST distinguir esa composición exacta de efectos individuales no aditivos.

#### Scenario: Coordenadas con gran contribución
- **WHEN** la ubicación domina una explicación
- **THEN** se informa su papel y se contrasta la variante sin ubicación mediante evaluación espacial; no se afirma causalidad agronómica.

#### Scenario: Corrección no lineal
- **WHEN** se explica un modelo cuya corrección tiene efectos individuales no aditivos
- **THEN** referencia más corrección ponderada reproduce la predicción, mientras los efectos individuales se identifican como sensibilidades y no se fuerza que su suma sea exacta.
