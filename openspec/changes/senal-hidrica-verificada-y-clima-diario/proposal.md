# Proposal

## Why

La fase hídrica cerrada no pudo evaluar suelo ni estrés vegetal porque las entradas no superaron sus auditorías; además, la exploración detectó soporte semanal insuficiente en junio–julio. Necesitamos recuperar señales públicas comprobables, respetar su escala temporal y comparar su aporte con un control equivalente antes de afirmar una mejora.

## What Changes

- Crear una fase aislada para abril–octubre de 2025, conservando 197 parcelas, 138 etiquetas y 59 consultas oficiales.
- Recuperar o verificar una señal hídrica vegetal: documentar la fórmula original cuando exista evidencia del productor o extraer Sentinel-2 L2A con bandas y calidad explícitas; nunca reinterpretar automáticamente el NDWI entregado.
- Auditar precipitación CHIRPS v3 final diaria y clima diario regional NASA ya recuperado; contrastar estaciones SMN y permitir ERA5-Land solo si su acceso y cobertura se comprueban. Las alternativas se deciden por evidencia antes del entrenamiento, sin exigir cuentas nuevas ni sustituir fuentes silenciosamente.
- Evaluar agregados temporales, efectos principales e interacciones acotadas con calendario común, faltantes y soporte conservados. Resolver la viabilidad de intervalos de 14 días antes de fijar el catálogo.
- Incorporar de forma opcional registros verificables de productores, vinculados a parcela y campaña. Su ausencia no bloquea la ruta pública ni autoriza inventar siembra, variedad, riego o fases.
- Reproducir la referencia activa y construir un control experimental pareado; ejecutar comparaciones aisladas y un combinado predeclarado, conservando evidencia negativa y recuperación sin red.
- Mantener suelo, térmico Landsat, nuevos rendimientos de otras campañas y activación/despliegue fuera de esta fase. La cartografía de suelo requiere otra evaluación de viabilidad.

## Capabilities

### New Capabilities

Ninguna: se amplían capacidades existentes.

### Modified Capabilities

- `data-provenance`: adquisición pública recuperable, identidad de señales nuevas y admisión opcional de metadatos parcelarios.
- `parcel-features`: distinguir los rásteres mensuales originales de fuentes diarias nuevas y generar señal hídrica, calendario y coexposición con soporte comprobado.
- `yield-model`: comparaciones pareadas entre controles y bloques nuevos, con elegibilidad específica del combinado de esta fase.
- `experiment-tracking`: cierre reproducible de la adquisición, decisiones de viabilidad y conservación íntegra de controles y paquetes.

## Impact

La implementación residirá en `experiments/senal-clima-20261013/`, con código y dependencias fijados, datos locales, auditorías y resultados propios. Reutilizará patrones de `src/agrocebada` y de la fase hídrica mediante copias identificadas; las tablas de `data/processed`, los modelos activos y las fases congeladas se conservarán intactos. Los accesos externos se limitarán a adquisición; inferencia y recuperación serán locales. Las pruebas cubrirán identidad, unidades, soporte temporal, contaminación de etiquetas, equivalencia del control y recuperación de las 59 consultas. Los deltas se aplicarán a las cuatro especificaciones indicadas; no cambia la interfaz del dashboard.
