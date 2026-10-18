## ADDED Requirements

### Requirement: Capacidad cartográfica de agua disponible por estrato
El sistema SHALL producir estimaciones de capacidad de agua disponible en milímetros para 0–30 y 30–60 cm a partir de retención volumétrica a presiones documentadas y espesores reales. MUST comprobar conversión de unidades, orden físico, máscara común y cobertura de todas las capas integrantes; no equiparar estas estimaciones con humedad actual, infiltración, escorrentía o agua disponible en una profundidad radicular observada. SHALL documentar por separado la sensibilidad a la presión elegida y la incertidumbre de las capas.

#### Scenario: Integración de estratos superiores
- **WHEN** existen datos válidos para 0–5, 5–15 y 15–30 cm
- **THEN** el resumen 0–30 cm pondera sus espesores y superficies válidas comunes, conserva milímetros y no calcula una media simple de los tres intervalos.

#### Scenario: Retención físicamente incoherente
- **WHEN** la retención a 1500 kPa supera la retención a la presión utilizada para capacidad de campo
- **THEN** el valor se marca inválido con motivo, sin recortarlo a cero como si fuera una medición coherente.

#### Scenario: Diferencia de quantiles de capas
- **WHEN** se calculan límites a partir de quantiles de retención
- **THEN** se reportan como envolventes de sensibilidad y no como un intervalo probabilístico calibrado de capacidad disponible.

### Requirement: Estrés conjunto con unidades y soporte temporal explícitos
El sistema SHALL conservar los efectos principales al comparar interacciones entre VPD, temperatura y señal hídrica comprobada. MUST aprender normalización y umbrales relativos únicamente con el entrenamiento de cada ajuste, vincular señales al mismo intervalo y registrar fechas, lagunas y soporte. SHALL distinguir indicadores estadísticos de coexposición de un diagnóstico fisiológico; MUST excluir la suma directa de kPa, grados Celsius e índices adimensionales y abstenerse de afirmar cierre estomático, detención de fotosíntesis o semanas exactas de pérdida de rendimiento.

#### Scenario: Cambio de etiquetas externas
- **WHEN** cambian las etiquetas de validación conservando el entrenamiento
- **THEN** permanecen iguales escalas, umbrales, interacciones y predicciones del ajuste.

#### Scenario: Semana sin señal satelital suficiente
- **WHEN** un intervalo semanal carece de las observaciones exigidas
- **THEN** no se cuenta como ausencia de estrés ni se interpola sobre la laguna; el resumen conserva su cobertura y permanece faltante si no alcanza soporte.

#### Scenario: Interacción favorable
- **WHEN** una interacción reduce el error frente al control con efectos principales
- **THEN** se informa una ganancia predictiva de desarrollo sin convertirla en evidencia de un mecanismo fisiológico medido.

### Requirement: Radiación separada de nubosidad observacional y extremos locales
El sistema SHALL identificar la radiación regional acumulada como energía por superficie y la nubosidad de captura como calidad de observación. MUST conservar los controles de calidad compartidos al evaluar radiación y no convertir una fracción de nubes satelitales en días nublados meteorológicos. MUST distinguir exposición térmica regional de una helada medida en parcela y no producir conteos diarios desde temperaturas mensuales.

#### Scenario: Serie regional sin mínimos bajo cero
- **WHEN** las mínimas diarias NASA no tienen días bajo cero
- **THEN** se registra esa propiedad de la serie sin afirmar ausencia de heladas en cada parcela ni generar una variable informativa inexistente.

#### Scenario: Comparación de radiación
- **WHEN** se añade radiación al control enriquecido
- **THEN** se mantienen fuente VPD, calendario, calidad satelital y población comunes para identificar el efecto incremental de radiación.
