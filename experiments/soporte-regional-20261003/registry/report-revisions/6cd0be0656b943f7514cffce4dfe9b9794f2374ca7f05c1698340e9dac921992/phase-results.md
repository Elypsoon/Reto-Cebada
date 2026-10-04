# Resultados de la fase de soporte regional

Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.

La versión activa conserva sus hashes y las 59 predicciones por ruta. La elegibilidad de E08 se calcula por separado; ninguna ruta se activa en esta fase.

| ejecución | ruta | RMSE principal | MAE | diferencia con control |
| --- | --- | --- | --- | --- |
| [E00-v2](../runs/E00-v2/run.json) | official | 0.756346 | 0.603169 | +0.000000 |
| [E00-v2](../runs/E00-v2/run.json) | selected | 0.749458 | 0.596553 | +0.000000 |
| [E01a-v2](../runs/E01a-v2/run.json) | official | 0.683994 | 0.539156 | -0.072352 |
| [E01b-v2](../runs/E01b-v2/run.json) | official | 0.889789 | 0.721320 | +0.133443 |
| [E02-v2](../runs/E02-v2/run.json) | official | 0.756346 | 0.603169 | +0.000000 |
| [E03-v2](../runs/E03-v2/run.json) | official | 0.754529 | 0.600804 | -0.001817 |
| [E04a-v2](../runs/E04a-v2/run.json) | official | 0.756386 | 0.602347 | +0.000040 |
| [E04b-v2](../runs/E04b-v2/run.json) | official | 0.756386 | 0.602347 | +0.000000 |
| [E05-v2](../runs/E05-v2/run.json) | official | 0.733562 | 0.583391 | -0.022784 |
| [E06-v2](../runs/E06-v2/run.json) | official | 0.757375 | 0.605847 | +0.001029 |
| [E07-v3-monthly_20_10](../runs/E07-v3-monthly_20_10/run.json) | official | 0.753740 | 0.569636 | -0.002606 |
| [E07-v3-whittaker_20_10](../runs/E07-v3-whittaker_20_10/run.json) | official | 0.747715 | 0.569805 | -0.008631 |
| [E08-v2](../runs/E08-v2/run.json) | official | 0.688201 | 0.541857 | -0.068145 |
| [E08-v2](../runs/E08-v2/run.json) | selected | 0.687622 | 0.541033 | -0.061836 |

## Comparación entre esquemas

![RMSE en los tres esquemas](figures/experiment-rmse.png)

| ejecución | ruta | principal | balanceado | rotado |
| --- | --- | --- | --- | --- |
| E00-v2 | official | 0.756346 | 0.764389 | 0.749169 |
| E00-v2 | selected | 0.749458 | 0.769436 | 0.749169 |
| E01a-v2 | official | 0.683994 | 0.757338 | 0.748971 |
| E01b-v2 | official | 0.889789 | 0.891325 | 0.760997 |
| E02-v2 | official | 0.756346 | 0.765028 | 0.749169 |
| E03-v2 | official | 0.754529 | 0.764656 | 0.726224 |
| E04a-v2 | official | 0.756386 | 0.763580 | 0.748870 |
| E04b-v2 | official | 0.756386 | 0.763580 | 0.751552 |
| E05-v2 | official | 0.733562 | 0.769155 | 0.738939 |
| E06-v2 | official | 0.757375 | 0.735315 | 0.751434 |
| E07-v3-monthly_20_10 | official | 0.753740 | 0.780706 | 0.663860 |
| E07-v3-whittaker_20_10 | official | 0.747715 | 0.772652 | 0.665158 |
| E08-v2 | official | 0.688201 | 0.760462 | 0.748305 |
| E08-v2 | selected | 0.687622 | 0.761172 | 0.748305 |

Pruebas: **68 pasan**; artefactos de entrenamiento intactos. [Registro de pruebas](../registry/test-results.json).


## Decisión E08

**Ninguna ruta E08 es elegible.** La mejora global pasa los umbrales, pero falla la protección de Puebla en el rotado: MAE 0.424265 frente a 0.377922 regional, superior al máximo 0.415714. [Paquete de recuperación experimental, sin candidatura ni activación](../packages/E08-v2/manifest.json).

**official: elegible=False; activated=false.**
Razones por condición: `{'three_valid_schemes': True, 'principal_gain_2pct': True, 'at_least_two_gains': True, 'mean_ratio_098': True, 'none_above_105': True, 'regional_protection': False, 'verification': True}`.
Razones de error por región: `[{'scheme': 'rotado-45-5', 'state': 'Puebla', 'mae': 0.42426526747441046, 'regional_mae': 0.37792164303387904}]`.

**selected: elegible=False; activated=false.**
Razones por condición: `{'three_valid_schemes': True, 'principal_gain_2pct': True, 'at_least_two_gains': True, 'mean_ratio_098': True, 'none_above_105': True, 'regional_protection': False, 'verification': True}`.
Razones de error por región: `[{'scheme': 'rotado-45-5', 'state': 'Puebla', 'mae': 0.42426526747441046, 'regional_mae': 0.37792164303387904}]`.

Condiciones de la ruta official:

| condición | cumple |
| --- | --- |
| three_valid_schemes | True |
| principal_gain_2pct | True |
| at_least_two_gains | True |
| mean_ratio_098 | True |
| none_above_105 | True |
| regional_protection | False |
| verification | True |

Condiciones de la ruta selected:

| condición | cumple |
| --- | --- |
| three_valid_schemes | True |
| principal_gain_2pct | True |
| at_least_two_gains | True |
| mean_ratio_098 | True |
| none_above_105 | True |
| regional_protection | False |
| verification | True |

## Intervalos E08

Nominal 90%; mínimo de calibración 25. Cobertura empírica sobre esta campaña, sin garantía temporal ni estatal.

| ruta | cobertura principal | predicciones evaluadas | disponible |
| --- | --- | --- | --- |
| official | 0.847826 | 138 | None |
| selected | 0.847826 | 138 | None |

[Cobertura por estado, soporte y folds](../runs/E08-v2/artifacts/validation-principal-5.json). [Pruebas de exclusión estatal y separación entre polígonos](../runs/E08-v2/artifacts/stress.json).

Los intervalos permanecen desactivados en ambas rutas: cobertura principal 84.78%, inferior al mínimo 85%. En Hidalgo la cobertura es 58.33%; en Puebla 91.55% y en Tlaxcala 100%. No se ajustaron los umbrales después de observar estos resultados.

## Lectura de los experimentos

Cada prueba conserva el efecto sobre los tres esquemas y su diferencia por parcela. E04b se contrasta con E04a. El esquema intraestado es diagnóstico y reutiliza las mismas etiquetas. Los resultados de E01–E07 no deciden los factores de E08.

La revisión 1 quedó cerrada tras detectar bloques diagnósticos desiguales (68/35/35; train mínimo70) por sus tamaños geométricos. La revisión 2 usa cortes iguales por estado (47/46/45 globales), mantiene los tres esquemas H01 y conserva el intento E00 y sus resultados parciales. [Incidencia y hashes](../registry/partition-revision.json).

Los detalles por estado, soporte, selección interna, parámetros efectivos, fuentes y composición final se encuentran en el `result.md`, `changes.json` y artefactos de cada ejecución. El registro conserva también fallos y omisiones.

## Prioridades de datos

1. Obtener etiquetas verificadas de otra campaña para una evaluación temporal independiente; su disponibilidad sigue pendiente.
2. Obtener registros de manejo por parcela: siembra y cosecha, variedad, fertilización, riego y eventos documentados, con origen y fecha; su disponibilidad sigue pendiente.
3. Una vez disponibles, versionar esos datos y registrar una fase nueva antes de entrenar. No ampliar esta grilla para forzar una mejora.

## Archivos y reproducción

- [Historial completo](experiment-history.md).
- [Índice CSV](../registry/summary.csv).
- [Catálogo congelado](../registry/catalog.json).
- [Condiciones y checkpoint TabPFN](../optional/tabpfn-2.5/manifest.json); comparación opcional independiente, sin activación.
- `scripts/recover_package.py <run-id>` ensambla código, dependencias, tablas, modelos y contratos verificados en un destino nuevo y reproduce las 59 consultas por ruta.
- [Scientific Agent Skills](https://arxiv.org/abs/2609.00065): procedimientos de scikit-learn y GeoPandas utilizados para implementar y verificar esta fase.

## Efectos observados

- E01a reduce el error principal y el sesgo de Tlaxcala; E01b empeora los tres esquemas. La regla dura no es una solución regional universal: también falla la protección de Puebla en el rotado.
- E02 mantiene prácticamente el control. E03 mejora principalmente el rotado. E04a recupera integrales con soporte temporal y mantiene ausentes los picos globales sin respaldo, con cambios pequeños en RMSE. E04b no añade una mejora global reproducida entre esquemas.
- E05 mejora principal y rotado pero empeora balanceado. E06 mejora balanceado, con pequeños retrocesos en principal y rotado. Sus ganadores internos no se trasladan a E08.
- Las dos configuraciones TabPFN se presentan por separado, sin selección externa; sus resultados no alteran E08.
- E08 mejora el RMSE principal frente al control E00 y la media regional, pero perjudica Puebla según el criterio congelado. El diagnóstico intraestado E08 da 0.652265 frente a 0.647705 E00; reutiliza etiquetas y no valida otra campaña.
- Las 59 salidas finales de E08 oficial/enriquecido coinciden con E01a, aunque cambian el procedimiento y sus contratos. Una mejora OOF o un cambio de procedimiento no implica necesariamente cambiar las consultas finales.

[Diagnósticos de umbrales por experimento](../registry/diagnostic-criteria.json); descriptivos para E01–E06, elegibilidad únicamente para E08.

## Incidencia de exportación TabPFN

El entrenamiento del primer intento E07 terminó, pero su CSV float32 redondeó hasta 2.2082519546273716e-7; la reconstrucción produjo exactamente los mismos valores float32. El reintento E07-v3 conserva pesos, tablas, particiones y parámetros, y exporta los valores como float64 con 17 dígitos. Cada configuración se entrenó de nuevo y sus 59 consultas se verificaron en un proceso nuevo con tolerancia absoluta 1e-10. El intento fallido permanece cerrado y no se presenta como resultado verificado.

[Catálogo del reintento congelado antes de entrenar](../registry/optional-retry-catalog.json). [Código, datos y pesos del adaptador recuperable](../optional/adapter-v3/manifest.json).
