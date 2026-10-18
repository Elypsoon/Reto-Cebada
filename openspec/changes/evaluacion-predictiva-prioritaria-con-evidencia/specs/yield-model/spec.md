## MODIFIED Requirements

### Requirement: Selección acotada y política recuperable
El sistema SHALL registrar antes de entrenar el conjunto de candidatos, representaciones, parámetros, ensambles, fuentes, semillas, particiones y criterios de admisión de cada comparación experimental y del procedimiento combinado. MUST limitar cada comparación principal nueva a dos familias predictivas, como máximo dos representaciones temporales y como máximo 160 candidatos oficiales únicos, incluidas referencias global/regional y correcciones regularizadas; los ensambles SHALL utilizar únicamente combinaciones pequeñas declaradas. Los controles históricos SHALL reproducir su procedimiento original congelado sin ampliar su búsqueda. La elección de parámetros, componentes y fuentes MUST utilizar exclusivamente evaluación interna y conservar las alternativas rechazadas con sus motivos. El procedimiento combinado SHALL quedar definido antes de consultar resultados externos de los experimentos y no se reconfigurará seleccionando retrospectivamente sus ganadores. En la fase histórica de soporte regional, el candidato opcional adicional SHALL conservar su comparación separada de hasta dos configuraciones y no entrará a E08. En la fase prioritaria, TabICLv2 y TabPFN-3 SHALL disponer cada uno de una comparación opcional independiente con hasta dos configuraciones fijas; ninguno entrará al combinado P06 ni a la versión activa como consecuencia de sus resultados exploratorios.

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
- **THEN** se conserva como evidencia exploratoria y no se incorpora al procedimiento combinado ni a la versión activa durante su fase.

#### Scenario: Búsqueda prioritaria fuera del presupuesto
- **WHEN** un bloque nuevo excede dos familias predictivas, dos representaciones o 160 candidatos oficiales únicos
- **THEN** el entrenamiento del bloque se rechaza antes de ajustar y se conserva el motivo; el resultado externo no autoriza ampliar ese protocolo.

### Requirement: Promoción condicionada a estabilidad espacial
El sistema SHALL evaluar el mismo procedimiento congelado en tres esquemas espaciales predefinidos y calcular en cada uno una predicción externa por cada una de las 138 etiquetas. MUST declarar elegible para promoción una versión únicamente si reduce el RMSE al menos 2% frente a la media regional del esquema principal y de al menos dos de los tres esquemas, si la media de las tres razones RMSE-modelo/RMSE-regional no supera 0.98 y ninguna razón supera 1.05. MUST limitar en cada esquema el aumento de MAE por estado a 10% frente a la referencia regional cuando ese estado tiene al menos diez etiquetas evaluadas. También SHALL exigir reproducción de exportación, contratos y pruebas antes de declarar elegibilidad. En la fase histórica de soporte regional SHALL aplicar la elegibilidad exclusivamente al combinado E08 definido antes de observar E01–E07, conservando sus decisiones por ruta. En la fase prioritaria SHALL aplicarla exclusivamente al combinado oficial P06 congelado antes de consultar P01–P05; MUST exigir además reducción principal de RMSE de al menos 2% frente al control activo reproducido y que ningún esquema aumente RMSE más de 5% frente a dicho control. MUST bloquear la elegibilidad si falta un esquema obligatorio o la reproducción íntegra del control activo y conservar una decisión negativa ante un fallo de protección regional. Las ablaciones, pruebas térmicas, modelos fundacionales y evaluación dentro de cada estado SHALL conservar carácter diagnóstico. MUST distinguir elegibilidad de activación efectiva y declarar la reutilización de etiquetas como evidencia de desarrollo. Esta fase SHALL preparar paquetes elegibles sin activación, despliegue ni envío automático.

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
- **WHEN** una ablación aislada o el esquema dentro de cada estado obtiene menor error que el combinado elegible de su fase
- **THEN** ese resultado no reemplaza los tres esquemas requeridos ni se convierte retrospectivamente en el procedimiento elegible.

#### Scenario: Mejora frente a referencia sin avance frente a la activa
- **WHEN** P06 cumple los umbrales de media regional pero no reduce el RMSE principal al menos 2% frente al control activo reproducido
- **THEN** su elegibilidad es negativa y el informe distingue ambas comparaciones.

#### Scenario: Combinado prioritario elegible
- **WHEN** P06 cumple todos los criterios y sus métricas e inferencia son reproducibles
- **THEN** se publica un paquete recuperable con elegibilidad positiva y activación falsa, sin alterar la decisión histórica de E08.

## ADDED Requirements

### Requirement: Cobertura de mecanismos predictivos prioritarios
El sistema SHALL evaluar separadamente selección de variables, alineación térmica, regularización jerárquica, modelos aditivos y representación funcional sobre la campaña abril–octubre de 2025. MUST conservar control, unidad parcelaria y rendimiento en t/ha, además de la variante con solo insumos oficiales. SHALL identificar las comparaciones térmicas como dependientes de la fuente regional diaria NASA y no imputar su existencia a la ruta oficial. MUST distinguir experimentos terminados, fallos, pruebas inviables y comparaciones opcionales omitidas; ningún resultado bibliográfico ni histórico sustituirá una predicción externa nueva.

#### Scenario: Fuente diaria ausente
- **WHEN** la alineación térmica no dispone de una serie NASA compatible y verificada
- **THEN** se registra la prueba térmica como inviable con su motivo, sin crear clima diario desde promedios mensuales y sin detener las comparaciones oficiales independientes.

#### Scenario: Hipótesis sin beneficio
- **WHEN** una alternativa prioritaria completa su evaluación y empeora frente al control
- **THEN** el informe conserva sus predicciones y diferencias como resultado negativo, sin retirarla del inventario de cobertura.

### Requirement: Selección y efectos regionales sin contaminación
El sistema SHALL comparar el ranking marginal vigente con una selección agronómica predefinida y una variante sin ranking supervisado, conservando las diferencias de disponibilidad e imputación por entrenamiento. SHALL comparar modelos que comparten información entre estados mediante regularización jerárquica con controles sin ese mecanismo. MUST ajustar medias, efectos regionales, parámetros de regularización y correcciones exclusivamente con entrenamiento y selección interna, y mostrar el soporte y la composición de cada predicción. Para una corrección jerárquica, un estado no visto MUST recibir la media global del entrenamiento sin efecto estatal ni corrección parcelaria aprendida para ese estado.

#### Scenario: Variable con relación no lineal
- **WHEN** la variante sin ranking conserva una variable con baja correlación marginal
- **THEN** su utilidad se contrasta mediante predicciones externas pareadas y no se afirma mejora por su mera inclusión.

#### Scenario: Efectos regionales con pocas etiquetas
- **WHEN** el entrenamiento contiene una o pocas etiquetas de un estado
- **THEN** el modelo conserva ese soporte y aplica la regularización elegida dentro del entrenamiento, sin corregir sus parámetros con etiquetas externas.

#### Scenario: Estado nuevo en corrección jerárquica
- **WHEN** una consulta pertenece a un estado sin etiquetas de entrenamiento
- **THEN** referencia más efecto regional más corrección reproduce exactamente la media global aprendida y el reporte indica soporte cero.

#### Scenario: Alteración de etiquetas externas
- **WHEN** se cambian las etiquetas externas manteniendo fijo el entrenamiento
- **THEN** permanecen iguales selección de variables, efectos regionales, transformaciones funcionales, parámetros, configuración y predicciones del procedimiento ajustado.
