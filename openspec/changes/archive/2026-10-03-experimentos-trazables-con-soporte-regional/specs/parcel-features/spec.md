## MODIFIED Requirements

### Requirement: Calidad y reconstrucción temporal trazable
El sistema SHALL registrar observaciones válidas, nubosidad, lagunas y método de reconstrucción por parcela e índice. MUST distinguir datos observados de interpolados, abstenerse de inventar fases cuando la señal sea insuficiente y no inferir aerosoles desde porcentaje de nubes. SHALL comparar el método vigente con reconstrucción por segmentos observados, conservar el soporte temporal de cada segmento y excluir de integrales y pendientes los intervalos sin soporte. MUST distinguir picos locales respaldados de un pico de temporada identificado y mantener faltantes las variables cuya definición requiera cobertura no disponible.

#### Scenario: Laguna prolongada alrededor del pico
- **WHEN** una curva carece de observaciones suficientes para establecer el pico con el criterio configurado
- **THEN** la variable fenológica se marca como no confiable o faltante y se conserva la información de cobertura.

#### Scenario: Laguna fuera de un segmento utilizable
- **WHEN** una parcela tiene segmentos utilizables separados por una laguna prolongada
- **THEN** se conservan los segmentos respaldados y sus integrales sin unir sus extremos ni presentar la suma como una integral observada de toda la temporada.

#### Scenario: Dos segmentos con máximos locales
- **WHEN** la cobertura no permite identificar el máximo de la temporada
- **THEN** se reporta la calidad y los máximos locales permitidos por el protocolo, sin inventar una fecha de pico global, antesis o llenado confirmado.

## ADDED Requirements

### Requirement: Representaciones y ablaciones comparables
El sistema SHALL identificar por versión las representaciones temporales, filtros de nubosidad, índices, sensores y variables de calidad utilizados en cada experimento. MUST conservar población, corte y covariables de control al comparar una sustitución de representación o ablación, y diferenciar señal espectral, soporte observacional y faltantes.

#### Scenario: Sustitución de representación histórica
- **WHEN** se reemplaza la reconstrucción con filtro de nubes de veinte por una de cuarenta por ciento
- **THEN** se registran la sustitución, calidad y faltantes correspondientes, conservando el resto del procedimiento para la comparación pareada.

#### Scenario: Ablación de calidad
- **WHEN** se retiran conteos de observaciones y otras variables de adquisición
- **THEN** permanecen las variables de señal declaradas, la variante se identifica separadamente y no se altera silenciosamente la selección de fuentes o los folds.

#### Scenario: Índice inexistente
- **WHEN** una ablación solicita un índice no suministrado para un sensor
- **THEN** se rechaza esa combinación o se registra su ausencia estructural sin sintetizar el índice ni fusionarlo con otro sensor.
