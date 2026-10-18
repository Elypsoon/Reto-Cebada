## Why

La fase de soporte regional redujo el RMSE principal de E08 a 0.687622 t/ha, pero rechazó su promoción por deterioro de Puebla en el esquema rotado; las mismas 138 etiquetas siguen siendo evidencia de desarrollo. La exploración bibliográfica identificó mecanismos prioritarios todavía no contrastados y permite ampliar la evaluación con hipótesis acotadas antes de determinar un resultado final.

## What Changes

- Crear una fase experimental aislada con controles reproducibles y cinco comparaciones prioritarias: selección de variables, alineación térmica de curvas, regularización jerárquica regional, GAM/EBM y representación funcional compacta.
- Comparar calendario y tiempo térmico con las series diarias NASA ya verificadas, conservando su escala regional y una ruta oficial independiente. No reconstruir clima diario desde CHIRTS mensual ni atribuir fechas de siembra o antesis no observadas.
- Comparar el filtro de correlación vigente con variables agronómicas predefinidas y una variante sin ranking supervisado; ajustar cualquier transformación aprendida dentro de cada entrenamiento.
- Registrar un procedimiento combinado P06 antes de observar resultados externos: corrección jerárquica con GPR/GAM y dos representaciones oficiales. Las pruebas térmicas y los modelos fundacionales conservan comparaciones separadas y no redefinen P06 retrospectivamente.
- Evaluar TabICLv2 y TabPFN-3 como comparaciones opcionales independientes con hasta dos configuraciones fijas por modelo, sin adjudicarles resultados del TabPFN 2.5 anterior.
- Mantener tres esquemas espaciales, protección de MAE estatal y verificación de las 59 consultas; añadir trazabilidad entre evidencia, hipótesis y resultado, incluyendo fallos y pruebas inviables. Evaluar elegibilidad sin activar automáticamente un modelo.
- Excluir de esta fase BART, TabM, NGBoost, nuevas imágenes/radar, ERA5, SoilGrids, AlphaEarth y simulación completa de cultivo. Registrar esas alternativas como diferidas, no como evaluadas o descartadas científicamente.

La evidencia guía hipótesis, no promete ganancias: [Franch et al., 2026](https://doi.org/10.1016/j.jag.2026.105140), [Zou y Okhrin, 2026](https://onlinelibrary.wiley.com/doi/full/10.1002/cjs.70043), [TabICLv2](https://proceedings.mlr.press/v306/qu26a.html) y [TabPFN-3](https://arxiv.org/abs/2605.13986). El diseño conserva fuentes, limitaciones y su relación con cada comparación.

## Capabilities

### New Capabilities

Ninguna: la fase amplía capacidades existentes.

### Modified Capabilities

- `yield-model`: catálogo prioritario, selección sin filtro marginal obligatorio, modelos jerárquicos/aditivos, comparaciones fundacionales independientes y elegibilidad específica de P06 preservando el alcance histórico de E08.
- `parcel-features`: representación de curvas en calendario/tiempo térmico y proyección funcional ajustada por entrenamiento, con máscaras de soporte, identidad del sensor y unidades.
- `experiment-tracking`: vínculo entre literatura, hipótesis, control, protocolo y resultado; cierre explícito de la cobertura prioritaria y conservación recuperable de cada familia nueva.

## Impact

La implementación futura residirá en una carpeta nueva bajo `experiments/`, reutilizando de forma versionada `modeling.py`, `variants.py`, `segments.py`, `external.py`, `phase.py`, `tracking.py` y los adaptadores opcionales de la fase `soporte-regional-20261003`. Se ampliarán pruebas de contaminación, contratos, particiones, recuperación e inferencia y el informe experimental; la versión activa y las fases históricas permanecerán recuperables.

GAM puede implementarse con splines y regularización del entorno existente; EBM requiere una dependencia `interpret` fijada. Los modelos fundacionales necesitan entornos separados, versiones y checkpoints verificables. No se incorporan proveedores nuevos, cambios de etiquetas, despliegues ni alteraciones del dashboard activo. Las dependencias y hashes concretos se resolverán en la preparación anterior a cualquier entrenamiento de la fase.
