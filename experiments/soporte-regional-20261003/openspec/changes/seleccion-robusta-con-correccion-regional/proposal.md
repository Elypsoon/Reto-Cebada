## Why

La selección actual obtiene RMSE 0.764 t/ha frente a 0.744 de la media regional: reducir el error respecto a la versión anterior no ha demostrado utilidad adicional frente a una referencia simple. Hidalgo concentra aproximadamente 54% del error cuadrático total; hace falta una corrección regional regularizada y una selección cuya ganancia resista distintas separaciones geográficas.

## What Changes

- Comparar la media regional con modelos que aprendan una corrección parcelaria sobre esa media, ajustando todos sus componentes dentro de cada entrenamiento.
- Acotar la búsqueda principal a GPR, CatBoost, dos representaciones temporales y ensambles pequeños con referencia regional; registrar la política antes de ejecutar experimentos.
- Evaluar el procedimiento anidado en tres esquemas espaciales predefinidos, conservando el esquema actual como comparación histórica y los escenarios de transferencia y buffer como sensibilidades.
- Generar un diagnóstico trazable de errores, cobertura y faltantes por estado y municipio, con revisión específica de Hidalgo. Corregir datos únicamente cuando los originales demuestren un error.
- Revaluar NASA y DGSIAP como fuentes opcionales y mantener una ruta oficial independiente. La admisión actual de NASA no implica su admisión automática en el nuevo procedimiento.
- Separar resultados experimentales de artefactos vigentes y promover una versión completa solo cuando cumpla los criterios registrados; conservar también los experimentos fallidos.
- Recalibrar intervalos y adaptar explicaciones, contratos, informes y exportación al procedimiento que resulte admitido.

### Alcance de esta fase

Se trabaja con las 138 etiquetas y 59 parcelas ocultas actuales, para estimación retrospectiva de abril–octubre de 2025 en t/ha, con corte al 31 de octubre. Obtener nuevas campañas o datos de manejo queda como continuación documentada; no bloquea esta fase ni se sustituye con datos inventados. No incluye publicación, alojamiento, envío oficial ni cambios en la interfaz ajenos a la compatibilidad del nuevo modelo.

## Capabilities

### New Capabilities

Ninguna; se amplían capacidades existentes.

### Modified Capabilities

- `yield-model`: corrección regional sin contaminación, búsqueda acotada, evaluación multiesquema, promoción condicionada y explicación reproducible de sus componentes.
- `data-provenance`: diagnóstico regional y registro verificable de correcciones o exclusiones, conservando originales y comparabilidad entre ejecuciones.

## Impact

Afecta `src/agrocebada/modeling.py`, contratos y explicaciones en `inference.py`, rutas de ejecución en `cli.py`/`common.py`, pruebas de modelado e integración, scripts de informes y artefactos versionados. Reutiliza tablas oficiales y cachés externas actuales; no requiere nuevas dependencias ni alterar fórmulas satelitales. Las versiones incompatibles de código y modelos se conservarán conjuntamente, sin modificar hashes para aparentar compatibilidad.
