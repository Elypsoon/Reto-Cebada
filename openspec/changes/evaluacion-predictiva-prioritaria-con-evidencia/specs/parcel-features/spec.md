## ADDED Requirements

### Requirement: Curvas comparables en calendario y tiempo térmico
El sistema SHALL producir representaciones de las mismas observaciones parcelarias en días y grados-día acumulados, documentando ecuación, origen temporal, temperatura base, límite térmico, unidades y asignación a la celda NASA verificada. MUST usar únicamente observaciones entre el 1 de abril y el 31 de octubre de 2025, mantener identidad del sensor, filtro de calidad y segmentos originales, y conservar separadamente las covariables del control. SHALL identificar el tiempo térmico como contexto regional desde un origen convencional, sin atribuirle siembra, antesis o fase agronómica confirmada. MUST rechazar clima diario incompatible o incompleto y no convertir datos mensuales en temperaturas diarias observadas.

#### Scenario: Cambio del eje de la curva
- **WHEN** se compara calendario con tiempo térmico
- **THEN** se conservan las observaciones aceptadas, la población y las etiquetas, se documentan diferencias de soporte y faltantes y las integrales informan índice × día o índice × grado-día según su eje.

#### Scenario: Laguna espectral prolongada
- **WHEN** dos segmentos están separados por más de 21 días calendario sin observaciones
- **THEN** permanecen separados también en tiempo térmico y no se integra ni interpola a través de esa laguna.

#### Scenario: Incremento térmico nulo
- **WHEN** varias fechas tienen el mismo tiempo térmico acumulado
- **THEN** se registra la agregación o ausencia de soporte según la regla congelada, sin introducir pasos térmicos artificiales ni dividir por cero.

#### Scenario: Ruta exclusivamente oficial
- **WHEN** se prepara o consulta la variante oficial
- **THEN** no se requiere la tabla diaria NASA ni se presentan predictores térmicos derivados de ella como insumos oficiales.

### Requirement: Representación funcional aprendida por entrenamiento
El sistema SHALL comparar resúmenes vigentes con una representación funcional de baja dimensión de curvas, identificada por versión, sensor, índice, eje y máscara de soporte. MUST aprender base estadística compartida, centrado, normalización, número de componentes, imputación y proyección exclusivamente con el entrenamiento aplicable; conservar los objetos necesarios para transformar consultas nuevas sin reajuste; y mantener una fila por parcela. SHALL conservar faltantes e indicadores de soporte para curvas insuficientes y rechazar una proyección que no pueda construirse con el entrenamiento, sin completar trayectorias completas ficticias ni eliminar etiquetas de evaluación.

#### Scenario: Consulta externa transforma la representación
- **WHEN** se transforma una parcela externa o de PREDICCION
- **THEN** se usa la base aprendida en entrenamiento, sin actualizarla con esa curva ni con su etiqueta y sin depender de otras consultas del lote.

#### Scenario: Soporte temporal insuficiente
- **WHEN** una parcela no permite estimar componentes funcionales según el protocolo
- **THEN** conserva su fila, faltantes y diagnóstico de calidad y utiliza únicamente la imputación aprendida o la referencia prevista por el procedimiento.

#### Scenario: Forma no aprendible en un fold
- **WHEN** un entrenamiento carece del soporte necesario para una rama funcional
- **THEN** la rama se declara no disponible para ese ajuste, la selección interna conserva alternativas viables y no se aprende una base con curvas de validación.

#### Scenario: Índice ausente estructuralmente
- **WHEN** una rama solicita un índice no entregado para un sensor
- **THEN** la combinación se rechaza o se registra como ausente y no se sintetiza desde otros índices ni se interpreta como curva observada.
