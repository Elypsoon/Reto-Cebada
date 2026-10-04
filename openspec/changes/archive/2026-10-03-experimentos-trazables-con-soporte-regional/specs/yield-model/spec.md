## MODIFIED Requirements

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

## ADDED Requirements

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
