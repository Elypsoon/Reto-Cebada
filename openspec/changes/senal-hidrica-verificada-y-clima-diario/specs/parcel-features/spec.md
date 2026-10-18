# Spec Delta

## MODIFIED Requirements

### Requirement: Extracción ambiental respetando escala y unidades
El sistema SHALL documentar reproyección, tratamiento de NoData, soporte espacial y unidades de clima, elevación y pendiente. MUST conservar el carácter mensual de los CHIRPS/CHIRTS originales y el carácter regional de NASA. Las nuevas fuentes diarias u horarias SHALL tener identidad, calendario y escala propios, sin convertir datos mensuales en eventos diarios ni estimaciones regionales en mediciones parcelarias.

#### Scenario: Solicitud de días de helada desde Tmin mensual
- **WHEN** se construyen variables con el promedio mensual de Tmin entregado
- **THEN** no se produce un conteo de heladas diarias ni una alerta de helada parcelaria.

#### Scenario: Fuente diaria desagregada
- **WHEN** se utiliza precipitación diaria producida mediante desagregación de totales de varios días
- **THEN** el registro conserva ese método y las rachas se identifican como estimadas, sin atribuirles fechas exactas de lluvia observada en parcela.

#### Scenario: Dos parcelas comparten celda climática
- **WHEN** dos consultas corresponden a la misma celda nativa
- **THEN** se conserva la identidad común de la serie y no se declara disponer de dos mediciones climáticas independientes.

## ADDED Requirements

### Requirement: Señal espectral con soporte de superficie y calendario
El sistema SHALL resumir una señal vegetal comprobada conservando fechas únicas, superficie válida, máscaras de calidad, cobertura temporal y faltantes por parcela. MUST respetar el detalle nativo de todas sus bandas y distinguir observaciones de reconstrucciones; remuestrear no aumentará la resolución informativa.

#### Scenario: Banda SWIR más gruesa que NIR
- **WHEN** las bandas tienen resoluciones diferentes
- **THEN** se declara la rejilla de cálculo y el detalle limitado por la banda más gruesa, conservando las conversiones de reflectancia.

#### Scenario: Capturas duplicadas
- **WHEN** varias entradas representan la misma fecha o adquisición
- **THEN** no cuentan como fechas independientes para superar el mínimo de soporte temporal.

#### Scenario: Píxeles insuficientes
- **WHEN** el área válida queda por debajo del mínimo congelado
- **THEN** el índice queda faltante y su soporte se conserva, sin representar una media parcial como observación completa.

### Requirement: Calendario común decidido por cobertura
El sistema SHALL fijar antes del entrenamiento la duración de los intervalos, alineación de fechas, soporte mínimo y agregación temporal utilizando únicamente disponibilidad y calidad. MUST vincular clima y señal vegetal al mismo intervalo y conservar las 197 parcelas; una laguna no se interpretará como ausencia de estrés.

#### Scenario: Cobertura semanal insuficiente
- **WHEN** la auditoría semanal no alcanza el soporte predefinido
- **THEN** se registra el diagnóstico y se evalúa solo la alternativa temporal predeclarada, sin consultar errores para escoger duración ni alterar la fase anterior.

#### Scenario: Intervalo compartido pero sin observación vegetal
- **WHEN** existe clima diario completo y no hay señal satelital suficiente en el intervalo
- **THEN** la coexposición permanece faltante y la cobertura se informa separadamente.

#### Scenario: Fecha agronómica desconocida
- **WHEN** no existe fecha de siembra o etapa comprobada
- **THEN** los resúmenes conservan ventanas de calendario y no se denominan exposición durante floración o llenado confirmado.

### Requirement: Coexposición temporal comparada con efectos principales
El sistema SHALL comparar VPD, temperatura y señal hídrica como efectos principales antes de añadir interacciones o fracciones de coexposición. MUST aprender sus escalas y umbrales relativos exclusivamente con entrenamiento, respetar identidad de celda y soporte temporal, y describirlas como indicadores estadísticos.

#### Scenario: Etiquetas o entradas externas modificadas
- **WHEN** cambia la validación manteniendo intactos entrenamiento y configuración
- **THEN** las escalas, umbrales y parámetros aprendidos permanecen iguales y no se ajustan para mejorar el error externo.

#### Scenario: Interacción con beneficio de desarrollo
- **WHEN** la interacción mejora la comparación pareada
- **THEN** se informa su ganancia predictiva y cobertura sin afirmar cierre estomático, detención de fotosíntesis ni semanas exactas de paro productivo.
