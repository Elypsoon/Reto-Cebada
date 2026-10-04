## Why

La fase regional redujo el RMSE principal de 0.764053 a 0.749458 t/ha, pero no superó la media regional de 0.743976 y perjudicó a Tlaxcala; la versión vigente permanece activa. Se necesita investigar soporte regional, representación temporal y selección de variables mediante comparaciones controladas, conservando los cambios y resultados de cada experimento sin convertir la reutilización de 138 etiquetas en una validación independiente.

## What Changes

- Crear un registro persistente de experimentos y ejecuciones con hipótesis, control, estado, configuración congelada, versiones, cambios del modelo, métricas, artefactos, limitaciones y decisión; registrar también resultados negativos, fallos y ejecuciones incompletas.
- Importar como antecedentes separados la versión vigente y la fase regional rechazada, sin adjudicar resultados históricos a experimentos nuevos.
- Ejecutar en un entorno aislado siete comparaciones: soporte regional, selección dentro del estado, sustitución de representación temporal, reconstrucción por segmentos, ablaciones de sensores/calidad, regularización GPR y TabPFN como candidato opcional.
- Definir antes de entrenar un procedimiento combinado E08 con soporte regional, selección dentro del estado y reconstrucción por segmentos; su configuración no dependerá de elegir ganadores con las OOF externas de E01–E07.
- Mantener evaluación anidada, rutas oficial/enriquecida, población y corte actuales, así como los umbrales de promoción. Añadir una evaluación espacial dentro de cada estado exclusivamente diagnóstica.
- Actualizar el registro y el informe al finalizar cada ejecución, verificando predicciones y diferencias frente a su control antes de marcarla completada.
- Registrar nueva campaña, manejo y medición de cosecha como evidencia pendiente; no incorporarlos sin disponibilidad y verificación.

## Capabilities

### New Capabilities

- `experiment-tracking`: historial recuperable de experimentos, cambios, resultados por ejecución, fallos, comparaciones y decisiones.

### Modified Capabilities

- `yield-model`: soporte regional por ajuste, selección de señal parcelaria y búsqueda acotada por comparación, candidato opcional separado, composición predeclarada y promoción independiente del historial exploratorio.
- `parcel-features`: reconstrucción por segmentos y soporte local, representaciones intercambiables y ablaciones trazables de sensores/calidad sin inventar fases.

## Impact

La implementación partirá de la copia experimental `experiments/regional-20261003`, cuya corrección regional ya existe, y creará una nueva copia aislada. Afectará allí `common.py`, `cli.py`, `modeling.py`, `robust.py`, `features.py`, `inference.py`, pruebas y generación de informes; la raíz activa conservará código, datos, modelos y exportaciones íntegros durante la fase.

El registro usará archivos locales JSON/JSONL, CSV y Markdown, sin servicio remoto. TabPFN y sus pesos requerirán un entorno opcional independiente, con versiones y condiciones verificadas; su indisponibilidad no bloqueará los experimentos principales. No se modifica el dashboard ni se despliega o envía una versión al organizador. La adquisición de nuevas fuentes y campañas queda fuera de esta implementación.
