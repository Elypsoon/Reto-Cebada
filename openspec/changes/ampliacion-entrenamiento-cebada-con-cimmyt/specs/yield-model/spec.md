## ADDED Requirements

### Requirement: Validación oficial intacta con entrenamiento auxiliar
El sistema SHALL comparar el aporte de etiquetas auxiliares sobre las mismas 138 etiquetas oficiales y los tres esquemas espaciales congelados, produciendo una predicción externa por parcela y esquema. MUST reservar las observaciones auxiliares para entrenamiento, excluirlas de métricas oficiales y de calibración, y mantener las 59 consultas fuera de toda selección basada en rendimiento. SHALL limitar coincidencia espacial bajo `cimmyt-point-assumption-v2` excluyendo cualquier grupo cuya caja principal ±0,01° quede a ≤2.000 m de un polígono oficial retenido, considerando todos sus puntos y campañas. Esta exclusión MUST repetirse en cada ajuste interno y externo antes de transformar o entrenar; los ajustes internos SHALL excluir también proximidad a validación externa. MUST conservar un límite inferior conservador de distancia en metros para la caja completa y excluir un caso incierto en torno al umbral. No SHALL presentar el supuesto como garantía de separación de parcelas reales sin límites conocidos.

#### Scenario: Parcela auxiliar cercana a validación
- **WHEN** la caja principal asumida de un auxiliar queda dentro del buffer de una parcela oficial retenida
- **THEN** se excluyen del ajuste todas las observaciones de su grupo de dependencia y el contrato conserva las claves, distancias conservadoras y motivos.

#### Scenario: Etiquetas retenidas alteradas
- **WHEN** cambian las etiquetas oficiales de validación manteniendo fijos entrenamiento, geometrías, entradas y protocolo
- **THEN** permanecen iguales los auxiliares admitidos, transformaciones aprendidas, configuraciones, pesos y predicciones del modelo de ese ajuste; solo cambian las métricas calculadas después.

#### Scenario: Ausencia de auxiliares utilizables
- **WHEN** ninguna cohorte supera los mínimos predeclarados después de la exclusión del ajuste
- **THEN** se utiliza el control oficial compatible, se registra la causa y no se atribuye a entrenamiento ampliado una predicción obtenida sin auxiliares.

### Requirement: Aporte de datos separado del cambio de representación
El sistema MUST publicar un control oficial completo, un control entrenado solo con etiquetas oficiales y características comunes, y el procedimiento ampliado con esas mismas características comunes. SHALL congelar cohortes, influencia auxiliar, grupos, muestreo, modelos, límites y reglas de selección antes del primer ajuste. MUST seleccionar configuraciones e influencia auxiliar únicamente con validación interna oficial y conservar una alternativa sin auxiliares. SHALL publicar curvas de aprendizaje predeclaradas como diagnóstico, sin utilizarlas retrospectivamente para elegir el procedimiento evaluado.

#### Scenario: Mejora del control reducido
- **WHEN** el modelo con características comunes mejora frente al control completo pero añadir etiquetas externas no mejora frente al control común
- **THEN** el reporte atribuye el contraste al cambio de representación y no afirma beneficio de aumentar registros.

#### Scenario: Donantes numerosos
- **WHEN** una cohorte contiene muchas campañas del mismo productor o muchas más filas que el entrenamiento oficial
- **THEN** la regla congelada limita su influencia y conserva conteos y pesos por fuente y grupo, sin permitir que las repeticiones equivalgan automáticamente a nuevas parcelas independientes.

#### Scenario: Curva favorable fuera de muestra
- **WHEN** un tamaño auxiliar de la curva diagnóstica obtiene menor error externo
- **THEN** ese tamaño se reporta sin sustituir retrospectivamente la configuración seleccionada internamente ni extender el catálogo.

### Requirement: Decisión diagnóstica de ampliación sin activación
El sistema SHALL calcular RMSE, MAE, R², sesgo, conteos y diferencias pareadas por esquema y estado, separando disponibilidad de datos, beneficio de añadir etiquetas y competitividad frente al control oficial completo. MUST aplicar criterios congelados para declarar una mejora estable y conservar resultados negativos o inviables. Ninguna comparación de esta fase SHALL activar modelos, modificar exportaciones vigentes o reemplazar las decisiones históricas E08/P06. Las mismas etiquetas oficiales reutilizadas MUST identificarse como evidencia de desarrollo y no como una nueva campaña independiente de validación.

#### Scenario: Mejora solo frente al control común
- **WHEN** añadir auxiliares mejora de forma estable el control común pero el procedimiento sigue siendo peor que el control oficial completo
- **THEN** se registra beneficio condicionado a esa representación y falta de competitividad operativa, sin recomendar automáticamente reemplazar la versión vigente.

#### Scenario: Comparación fundacional favorable
- **WHEN** una configuración opcional con auxiliares mejora su pareja sin auxiliares
- **THEN** se conserva como diagnóstico independiente y no se incorpora al procedimiento principal usando sus errores externos.

#### Scenario: Mejora bajo referencia geográfica asumida
- **WHEN** A02 satisface los criterios métricos de aporte estable bajo el protocolo de puntos
- **THEN** se informa estabilidad predictiva condicionada a ese supuesto junto con la sensibilidad de admisión, sin afirmar robustez geográfica, datum validado o separación espacial certificada.

### Requirement: Sensibilidad de admisión espacial previa al entrenamiento
El sistema SHALL publicar antes de ajustar modelos los conjuntos y conteos de admisión por cohorte y ajuste para políticas estrecha (±0,001°, 1.000 m), principal (±0,01°, 2.000 m) y amplia (±0,02°, 3.000 m), aplicando celda única, exclusión conjunta por grupo y los mismos mínimos. MUST utilizar exclusivamente la política principal para adquisición climática auxiliar, entrenamiento y selección. Las políticas de sensibilidad no SHALL incorporar ajustes predictivos, consultas adicionales o nuevos candidatos.

#### Scenario: El margen cambia la viabilidad
- **WHEN** conjuntos de claves o viabilidad difieren entre las tres políticas
- **THEN** se registra sensibilidad geográfica detectada y los cambios antes de entrenar; no se elige el margen que conserva más etiquetas ni se reducen los mínimos.

#### Scenario: Conjuntos iguales bajo los márgenes examinados
- **WHEN** las tres políticas conservan los mismos conjuntos en todos los ajustes examinados
- **THEN** se informa ausencia de sensibilidad de admisión detectada en esas políticas, manteniendo explícitas las incógnitas de datum y precisión y sin atribuirle robustez predictiva a otras ubicaciones.
