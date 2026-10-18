## Why

El modelo dispone de lluvia, topografía y señales satelitales, pero no representa explícitamente la capacidad del suelo para almacenar agua ni contrasta interacciones de demanda atmosférica y humedad. La conversación agronómica del 9 de octubre de 2026 identifica hipótesis pertinentes que requieren comprobar definiciones, escala y utilidad predictiva antes de incorporarlas.

## What Changes

- Preparar una fase experimental aislada para estimación retrospectiva de rendimiento parcelario en t/ha, abril–octubre de 2025, conservando 197 parcelas, 138 etiquetas y 59 consultas ocultas.
- Auditar la fórmula y bandas del NDWI entregado, su disponibilidad y soporte temporal; conservarlo como señal espectral sin atribuir contenido de agua foliar cuando la definición no esté comprobada.
- Verificar acceso y metadatos de las capas de retención SoilGrids; construir, si cumplen los controles, estimaciones cartográficas de capacidad de agua disponible para 0–30 y 30–60 cm, diferenciadas de humedad actual y profundidad radicular observada.
- Comparar por separado suelo, interacciones acotadas VPD–señal hídrica–temperatura y radiación NASA, y un procedimiento combinado predeclarado. No adoptar la suma física inválida `VPD + temperatura - NDWI` ni interpretar las interacciones como medición de cierre estomático.
- Registrar viabilidad de evidencia local de heladas, variedad y fecha de siembra. Su ausencia no se sustituirá con inferencias por estado; en esta fase su auditoría no incorpora automáticamente nuevas ramas predictivas.
- Conservar controles pareados, selección interna, tres esquemas espaciales y criterios de mejora y protección regional; separar disponibilidad de fuentes, evaluación completada, elegibilidad y activación.

Fuera de alcance: implementar una simulación completa de balance hídrico/cultivo, ET0 con términos incompletos, adquirir nuevas imágenes/radar o ERA5, generar alertas parcelarias, inferir fases exactas, modificar etiquetas, cambiar la aplicación activa, activar/desplegar/enviar modelos o concluir efectos del cambio climático desde una campaña.

## Capabilities

### New Capabilities

Ninguna; se amplían capacidades existentes.

### Modified Capabilities

- `data-provenance`: admisión trazable de suelo y auditoría de definiciones espectrales y metadatos agronómicos, con decisiones de viabilidad previas al entrenamiento.
- `parcel-features`: capacidad disponible por estrato, interacciones con unidades normalizadas y soporte temporal, y separación entre nubosidad observacional y radiación.
- `yield-model`: catálogo acotado de comparaciones hídricas y procedimiento combinado con elegibilidad específica de esta fase, preservando criterios y decisiones históricas.
- `experiment-tracking`: vínculo recuperable entre hipótesis, auditorías, disponibilidad real, controles y resultados de la fase hídrica.

## Impact

La implementación futura residirá en `experiments/hidrica-estres-20261009/`, con adaptadores de fuentes, transformadores, orquestación, pruebas y reportes propios. Reutilizará copias verificadas de `features.py`, `external.py`, `modeling.py`, manejo de segmentos y validación/recuperación de fases anteriores; sus importaciones y destinos quedarán aislados. Los controles conservarán código, dependencias y contratos originales.

SoilGrids requerirá recuperación local verificada por una vía oficial disponible, sin depender de la API pausada ni descargar mapas globales completos. Se utilizarán inicialmente las bibliotecas numéricas y geoespaciales existentes; cualquier dependencia adicional tendrá versión y justificación registradas antes de congelar. La inferencia usará artefactos locales sin red. El modelo activo y los experimentos anteriores permanecerán intactos y recuperables.
