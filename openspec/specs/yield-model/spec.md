# yield-model Specification

## Purpose

Estimar rendimiento parcelario en toneladas por hectárea mediante modelos comparados honestamente fuera de muestra, con resultados reproducibles para las 59 parcelas del conjunto oficial.

## Requirements

### Requirement: Evaluación independiente por parcela
El sistema SHALL obtener una predicción externa por cada parcela etiquetada mediante particiones espaciales reproducibles. MUST mantener todas las observaciones de una parcela en el mismo grupo y realizar el ajuste de variables, modelos y ensambles dentro del entrenamiento externo.

#### Scenario: Serie temporal con numerosas capturas
- **WHEN** una parcela tiene decenas de capturas satelitales
- **THEN** sus capturas no se reparten entre entrenamiento y validación como ejemplos independientes.

### Requirement: Comparación de referencias y fuentes
El sistema SHALL comparar modelos contra referencias globales y regionales ajustadas con datos de entrenamiento y contra una variante completa que use solo insumos del reto. MUST elegir fuentes adicionales y complejidad con un criterio registrado antes de revisar resultados.

#### Scenario: Fuente adicional sin beneficio estable
- **WHEN** una fuente no cumple calidad o no mejora el criterio predefinido dentro de la evaluación anidada
- **THEN** el modelo seleccionado prescinde de ella y el reporte conserva la comparación y el motivo.

### Requirement: Reporte de desempeño fuera de muestra
El sistema SHALL reportar RMSE y MAE en t/ha, R² global sobre el vector de predicciones externas, métricas por estado y superficie, composición de particiones y variabilidad del error. MUST distinguir estas métricas de resultados del conjunto oculto. SHALL publicar además métricas y decisiones de promoción por esquema espacial, diferencias frente a la referencia regional y la ejecución anterior, así como frecuencias de selección y admisión de fuentes. MUST declarar que la reutilización de las mismas etiquetas durante el desarrollo no constituye un test independiente ni validación de otra campaña; no tratará las predicciones repetidas de una parcela como nuevas etiquetas independientes.

#### Scenario: Evaluación regional difícil
- **WHEN** una partición presenta R² negativo o un estado tiene error elevado
- **THEN** el reporte muestra ese resultado sin sustituirlo por métricas de entrenamiento o promedios que oculten el fallo.

#### Scenario: Tres evaluaciones de las mismas parcelas
- **WHEN** se publican los tres vectores de predicciones externas
- **THEN** cada esquema se identifica por separado y no se afirma disponer de 414 etiquetas independientes ni de un test externo nuevo.

### Requirement: Incertidumbre evaluada
El sistema SHALL publicar intervalos solo cuando estén calibrados sin utilizar el subconjunto evaluado y se reporte cobertura y amplitud empíricas. MUST indicar cuando un intervalo no está disponible o no cumple la cobertura configurada.

#### Scenario: Intervalo nominal sin cobertura suficiente
- **WHEN** un intervalo nominal de 90% no alcanza el criterio de cobertura definido
- **THEN** no se presenta como un intervalo confiable de 90% y la salida informa esa limitación.

### Requirement: Exportación oficial y reproducibilidad
El sistema SHALL exportar exactamente 59 filas de PREDICCION, con identificador oficial único y rendimiento finito en t/ha, vinculadas a versión de datos, variables, modelo, dependencias y semilla. MUST rechazar artefactos de modelo y variables incompatibles.

#### Scenario: Exportación incompleta
- **WHEN** falta una parcela o existe una predicción duplicada o no finita
- **THEN** la exportación final se bloquea e informa los casos pendientes.

### Requirement: Interpretación de contribuciones
El sistema SHALL describir las explicaciones como contribuciones al resultado del modelo y comprobar su estabilidad fuera de muestra. MUST evitar presentarlas como causas demostradas, decisiones crediticias o garantías productivas. Para un modelo con corrección regional SHALL mostrar la referencia, intensidad y corrección total de manera que su composición reproduzca la predicción; MUST distinguir esa composición exacta de efectos individuales no aditivos.

#### Scenario: Coordenadas con gran contribución
- **WHEN** la ubicación domina una explicación
- **THEN** se informa su papel y se contrasta la variante sin ubicación mediante evaluación espacial; no se afirma causalidad agronómica.

#### Scenario: Corrección no lineal
- **WHEN** se explica un modelo cuya corrección tiene efectos individuales no aditivos
- **THEN** referencia más corrección ponderada reproduce la predicción, mientras los efectos individuales se identifican como sensibilidades y no se fuerza que su suma sea exacta.

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
El sistema SHALL registrar antes de entrenar el conjunto de candidatos, representaciones, parámetros, ensambles, fuentes, semillas, particiones y criterios de admisión de cada comparación experimental y del procedimiento combinado. MUST limitar cada comparación principal a dos familias predictivas, como máximo dos representaciones temporales y como máximo 160 candidatos oficiales únicos, incluidas referencias global/regional y correcciones regularizadas; los ensambles SHALL utilizar únicamente combinaciones pequeñas declaradas. Un candidato opcional adicional SHALL evaluarse en una comparación separada con como máximo dos configuraciones congeladas y no entrará al procedimiento combinado de esta fase. La elección de parámetros, componentes y fuentes MUST utilizar exclusivamente evaluación interna y conservar las alternativas rechazadas con sus motivos. El procedimiento combinado SHALL quedar definido antes de consultar resultados externos de los experimentos y no se reconfigurará seleccionando retrospectivamente sus ganadores.

#### Scenario: Ganador aparente en evaluación externa
- **WHEN** una familia aislada obtiene menor error externo que el procedimiento de selección
- **THEN** se publica como diagnóstico y no se sustituye retrospectivamente la selección ni se recalculan pesos con esas etiquetas.

#### Scenario: Fuente adicional sin beneficio
- **WHEN** NASA, DGSIAP o su combinación no cumple la política interna
- **THEN** la opción queda excluida del ajuste correspondiente y sigue disponible una variante completa con solo insumos oficiales.

#### Scenario: Experimento con otra representación
- **WHEN** se compara una representación temporal histórica o por segmentos
- **THEN** se registra una comparación con su pareja de representaciones y control, sin ampliar automáticamente las demás grillas ni alterar el procedimiento combinado después de sus resultados.

#### Scenario: Candidato opcional favorable
- **WHEN** el candidato adicional obtiene un resultado externo favorable
- **THEN** se conserva como evidencia exploratoria y no se incorpora al procedimiento combinado ni a la versión activa durante esta fase.

### Requirement: Promoción condicionada a estabilidad espacial
El sistema SHALL evaluar el mismo procedimiento congelado en tres esquemas espaciales predefinidos y calcular en cada uno una predicción externa por cada una de las 138 etiquetas. MUST promover una versión únicamente si reduce el RMSE al menos 2% frente a la media regional del esquema principal y de al menos dos de los tres esquemas, si la media de las tres razones RMSE-modelo/RMSE-regional no supera 0.98 y ninguna razón supera 1.05. MUST limitar en cada esquema el aumento de MAE por estado a 10% frente a la referencia regional cuando ese estado tiene al menos diez etiquetas evaluadas. También SHALL exigir reproducción de exportación, contratos y pruebas antes de promover. En esta fase SHALL aplicar la elegibilidad de promoción exclusivamente al procedimiento combinado E08, definido antes de observar E01–E07, y conservar separadamente sus decisiones por ruta; los experimentos aislados y la evaluación espacial dentro de cada estado son diagnósticos. MUST distinguir elegibilidad de activación efectiva y declarar la reutilización de etiquetas como evidencia de desarrollo.

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

#### Scenario: Diagnóstico adicional favorable
- **WHEN** una ablación aislada o el esquema dentro de cada estado obtiene menor error que E08
- **THEN** ese resultado no reemplaza los tres esquemas requeridos ni se convierte retrospectivamente en el procedimiento elegible.

### Requirement: Soporte regional visible y ajustado sin contaminación
El sistema SHALL conservar por ajuste el número de etiquetas de entrenamiento de cada estado, la referencia aplicable y la regla de atenuación de correcciones o predicciones. MUST determinar el soporte y sus parámetros exclusivamente con entrenamiento y evaluación interna, identificar estados con soporte insuficiente o ausente y conservar el comportamiento especificado para correcciones regionales en estados no vistos. Las predicciones de un modelo directo compartido para un estado ausente SHALL identificarse como transferencia, sin presentarse como corrección regional aprendida.

#### Scenario: Una etiqueta estatal disponible
- **WHEN** una validación retira treinta de las treinta y una parcelas de un estado
- **THEN** el registro identifica una etiqueta disponible y aplica la regla predeclarada de soporte, sin utilizar las etiquetas externas para corregir el sesgo.

#### Scenario: Estado ausente
- **WHEN** no existen etiquetas del estado consultado en entrenamiento
- **THEN** una corrección regional conserva la media global sin corrección y un modelo directo identifica su predicción como transferencia; ambos registran soporte cero.

### Requirement: Selección de señal dentro del estado
El sistema SHALL comparar una variante que selecciona y ajusta la corrección sobre variación dentro del estado con su control regional sin esa transformación. MUST aprender medias de predictores, residuos, disponibilidad, imputación, selección y escalado exclusivamente dentro de cada ajuste, conservar los parámetros necesarios para reproducir consultas y registrar la regla para estados ausentes.

#### Scenario: Etiquetas externas alteradas
- **WHEN** se cambian etiquetas externas conservando fijo el entrenamiento y la entrada consultada
- **THEN** permanecen iguales medias, variables, soporte, configuración, pesos y predicción del modelo ajustado.

#### Scenario: Variables dominadas por diferencias estatales
- **WHEN** se compara selección global con selección dentro del estado
- **THEN** el informe conserva ambas variantes y sus resultados externos sin atribuir causalidad a sus correlaciones o escoger columnas con las etiquetas externas.

### Requirement: Evaluación diagnóstica dentro de regiones conocidas
El sistema SHALL evaluar control y procedimiento combinado con un esquema espacial adicional construido por geometría dentro de cada estado, congelado antes de consultar sus errores. MUST publicar tamaños estatales de entrenamiento y validación, mantener separación por parcela, identificar su carácter diagnóstico y registrar inviabilidad sin reemplazar los tres esquemas de promoción.

#### Scenario: Interpretación de escenarios distintos
- **WHEN** el procedimiento mejora con regiones representadas y empeora cuando un estado queda ausente
- **THEN** el reporte distingue predicción en regiones conocidas de transferencia y mantiene ambos resultados.

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
