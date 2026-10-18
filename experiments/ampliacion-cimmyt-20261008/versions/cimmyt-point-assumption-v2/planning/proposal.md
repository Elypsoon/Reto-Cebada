## Why

Los modelos siguen aprendiendo de las mismas 138 etiquetas oficiales de 2025; las comparaciones prioritarias no justificaron activar P06. CIMMYT ofrece una fuente mexicana con rendimientos históricos de cebada que permite investigar si nuevas observaciones reales aportan información, siempre que se compruebe su compatibilidad y se mida el efecto sobre la evaluación oficial intacta.

## What Changes

- Auditar [Historical Agronomic Dataset — Mexico 2012–2022](https://hdl.handle.net/11529/10548986): archivos de parcela/bitácora, siembra/cosecha/rendimiento y glosario. Registrar versión, acceso, condiciones de uso, hashes, cardinalidad de uniones y motivos de exclusión. El [artículo descriptor](https://www.nature.com/articles/s41597-025-06143-w) reporta 968 registros de cebada; la auditoría local de V6 encontró 1.396 filas de cebada y 48 candidatos tras filtros agronómicos, de los cuales 29 son locales. Todavía no son etiquetas admitidas para entrenamiento.
- Construir, si supera la auditoría, una población auxiliar identificada por fuente, parcela y campaña, separada de los 197 identificadores oficiales. Admitir únicamente rendimientos de grano con unidades verificables; separar registros repetidos, productos y ciclos, sin copiar estadísticas municipales ni etiquetas entre años.
- Comparar dos cohortes predefinidas de primavera–verano y temporal: Puebla/Hidalgo/Tlaxcala y México. La compatibilidad de modalidad con las parcelas oficiales se declarará desconocida mientras los originales no la documenten; no se deducirá desde SIAP.
- Preparar características comunes de área y clima regional NASA POWER en la ventana abril–octubre de cada año. Ampliar únicamente el histórico del proveedor NASA ya utilizado. No reconstruir índices satelitales de parcela desde ubicaciones anonimizadas ni sustituirlos por valores inventados.
- Admitir para este diagnóstico los puntos aproximados del Excel bajo el protocolo `cimmyt-point-assumption-v2`, con referencia WGS84 asumida y documentada, margen espacial principal de ±0,01° y separación de 2.000 m frente a validación. La búsqueda de documentación no verificó datum, precisión del punto ni relación con los vértices del artículo. Publicar sensibilidad de admisión a otros dos márgenes antes de entrenar; no convertir esos supuestos en precisión certificada o límites reales de parcela.
- Ejecutar comparaciones pareadas de entrenamiento oficial frente a entrenamiento ampliado, con control de características comunes y referencia oficial completa. Congelar antes de entrenar cohortes, pesos, modelos, límites y selección interna; conservar los tres esquemas y las 138 etiquetas como único conjunto evaluado.
- Publicar conteos efectivos de nuevas etiquetas, parcelas y campañas, curvas de aprendizaje, ganancias o pérdidas por estado, fallos y limitaciones. Un acceso pendiente o una cohorte insuficiente cerrará la auditoría con ese diagnóstico, sin afirmar que la ampliación fue probada.
- Mantener el estudio como diagnóstico: sin activación, despliegue o envío automático. Bajío, ICARDA, suelos y otros proveedores quedan diferidos; no se consideran probados.

## Capabilities

### New Capabilities

Ninguna: se amplían capacidades existentes.

### Modified Capabilities

- `data-provenance`: adquisición y auditoría de etiquetas externas, uniones seguras y población auxiliar separada de la oficial.
- `parcel-features`: contrato de características compartidas entre campañas y fuentes, respetando fechas, unidades y ubicación aproximada.
- `yield-model`: comparación anidada del aporte de nuevas etiquetas, control de influencia auxiliar y exclusión espacial frente a validación.
- `experiment-tracking`: embudo de admisión, conteos independientes, protocolo congelado y cierre verificable de la auditoría y los experimentos.

## Impact

La implementación futura residirá en una fase nueva bajo `experiments/`. Reutilizará de manera versionada los contratos de población, particiones, selección, registro y recuperación de `experiments/prioridades-predictivas-20261006`, que actualmente rechazan entradas distintas de las 197 parcelas oficiales. La ampliación necesita un cargador auxiliar independiente; no puede anexar filas al maestro oficial ni modificar la fase congelada.

La fase iniciada el 8 de octubre de 2026 ya conserva los tres originales V6 y el lector XLSX fijado; su auditoría geográfica y entrenamiento ampliado siguen pendientes. La revisión del 9 de octubre afecta el protocolo espacial y los contratos de trazabilidad, sin reabrir filtros agronómicos, mínimos, catálogo o tareas completadas. Los paquetes recuperables respetarán las condiciones de adquisición y redistribución registradas. El cambio anterior, completado pero aún no archivado, conserva sus decisiones E08/P06 y sus deltas; este cambio añade requisitos distintos y no los sustituye. Las bases locales permiten información pública adicional (`docs/Reto Agrocebada Bases.md`, sección DATASET).

Más registros no garantizan menor error. Esta fase distingue evidencia publicada, datos realmente admitidos y mejora medida; las 59 parcelas ocultas permanecen sin etiquetas de evaluación.
