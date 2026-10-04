## Context

La motivación está en `proposal.md`. El proyecto ya dispone de nueve tablas oficiales, 138 etiquetas, cachés NASA/DGSIAP verificadas y referencias ajustadas por entrenamiento. `modeling.py` concentra particiones, selección, calibración y exportación; `inference.py` comparte el cálculo y las explicaciones con la aplicación.

La ejecución vigente tiene RMSE seleccionado 0.7640529, referencia regional 0.7439757 y ajuste final GPR con NASA. La búsqueda principal mantiene 81 configuraciones y un promedio de cinco familias más referencia. GPR aislado obtuvo 0.696937 y CatBoost 0.712859 en OOF; esos resultados motivan hipótesis de desarrollo y no autorizan a atribuirles una selección independiente. La versión actual tiene 25 pruebas, seis de ellas agregadas en la revisión anterior.

Hay dos restricciones de integración observadas: los contratos comparan un hash de todo `src/agrocebada`, y el entrenamiento escribe directamente en `artifacts/` y modifica la columna de grupos de `parcels.parquet`. Además, explicaciones y estabilidad de variables asumen componentes con pasos `select`, `scale` y `model`; un estimador compuesto exige adaptar esa interfaz.

## Goals / Non-Goals

**Goals:**

- Separar aprendizaje de diferencias regionales y variación parcelaria, manteniendo una referencia reproducible.
- Probar un protocolo acotado, completamente congelado antes de sus resultados, con pruebas de contaminación y comparaciones pareadas.
- Hacer recuperables modelos, datos y código de cada ejecución, y evaluar una promoción sin sustituir la aplicación vigente durante los experimentos.
- Terminar la fase con una decisión verificable, incluso si ninguna variante mejora suficientemente.

**Non-Goals:**

- No entrenar un modelo independiente por municipio o estado con estas muestras pequeñas.
- No incorporar covariables de manejo ausentes ni dar etiquetas a campañas anteriores.
- No transformar nuevas divisiones espaciales de las mismas parcelas en un supuesto test independiente.
- No optimizar pesos continuos de ensamble, redes neuronales, nuevas fuentes remotas ni más fórmulas de fenología en esta fase.

## Decisions

### 1. Estimador compuesto con corrección aprendida dentro de cada ajuste

Agregar un estimador compatible con la interfaz de entrenamiento existente. Para cada `fit`, calcular la media global y las medias por estado con sus filas de entrenamiento; formar residuos `r_i = y_i - media_train(estado_i)`; ajustar selección de variables, escala y modelo sobre esos residuos. Predecir `media_train(estado) + alpha * correccion(X)`, con `alpha` elegido internamente entre 0.5 y 1.0. La referencia sola representa intensidad cero y permanece siempre elegible.

Los indicadores de estado disponibles en `load_tables` sirven a la referencia y no entran al ranking de variables de la corrección. Conservar un modelo compartido para las tres regiones. Para un estado ausente en train, devolver la media global sin corrección: la transferencia a una región nueva se documenta aparte. Cada componente conserva sus estadísticas de train y columnas para serialización y explicación.

Alternativas consideradas: añadir estado como otro predictor permite que el ranking siga dominado por diferencias entre regiones; modelos separados por estado reducen todavía más el tamaño de entrenamiento. La corrección compartida permite probar variación parcelaria sin ambos problemas, aunque no garantiza mejora.

### 2. Grilla inicial de 26 candidatos oficiales y cuatro ensambles fijos

Usar únicamente `monthly_20_10` y `whittaker_20_10`. Ambas mantienen nube máxima 20%; comparan representaciones observada y reconstruida con el mismo filtro de calidad. Es una simplificación propuesta por calidad y tamaño de búsqueda, no una afirmación de que sean las mejores tablas según OOF externa.

- GPR: longitudes 1 y 5, conservando el resto de sus parámetros actuales.
- CatBoost: profundidades 2 y 3, conservando 220 iteraciones y regularización actual.
- Dos representaciones por dos familias por dos parámetros: ocho modelos directos.
- Las mismas ocho configuraciones con corrección regional e intensidades 0.5/1.0: dieciséis modelos compuestos.
- Media global y regional: dos referencias.

No cambiar inicialmente el máximo de veinte variables, diez para GPR. Los ganadores internos de cada familia podrán ser directos o compuestos. Comparar cuatro promedios uniformes: GPR+CatBoost, regional+GPR, regional+CatBoost y regional+GPR+CatBoost. Registrar participantes y rechazos; no ajustar pesos a OOF externa ni ampliar automáticamente la grilla si los resultados son desfavorables.

Conservar el criterio interno de reducción relativa de RMSE de al menos 2%, mejora en al menos dos folds internos y aumento de MAE regional no mayor de 10% para estados con diez ejemplos. Un candidato o ensamble debe cumplirlo frente a la mejor referencia interna; un reemplazo posterior debe cumplirlo también frente a la opción vigente. Si no hay candidato elegible, conservar la referencia interna. En empates de RMSE con tolerancia 1e-12, preferir referencia, individuo y menor número de componentes/fuentes, en ese orden.

Alternativa descartada: elegir directamente GPR por su OOF actual. Una comparación diagnóstica externa no sustituye un protocolo de selección.

### 3. Fuentes externas como ablaciones pareadas

Sobre los dos ganadores internos oficiales de familia, evaluar tres variantes externas por ganador: NASA, DGSIAP y NASA+DGSIAP. Esto agrega seis configuraciones, sin multiplicar las 26 configuraciones oficiales por todas las combinaciones de fuentes. La pareja de fuentes se evalúa explícitamente para evitar depender del orden NASA/DGSIAP.

Cada admisión debe superar el mismo candidato sin esas fuentes y la referencia interna con los umbrales anteriores. Elegir fuentes solo dentro de train; los ensambles posteriores pueden combinar componentes con distintos contratos, incluida la referencia sin externos. Conservar comparaciones internas por fold/estado y no forzar una fuente por su admisión histórica. Ajustar por separado la ruta oficial y la enriquecida en los mismos esquemas externos.

### 4. Tres esquemas espaciales congelados

Registrar asignaciones por identificador antes de consultar rendimientos de los experimentos:

| Esquema | Construcción | Papel |
| --- | --- | --- |
| `principal-5` | Asignaciones vigentes de `artifacts/folds.csv` | Comparación histórica exacta |
| `balanceado-4` | Cortes medianos de mayor extensión sobre puntos UTM 14N, cuatro grupos | Sensibilidad al número de grupos |
| `rotado-45-5` | Centrar puntos UTM, rotarlos 45 grados y aplicar los mismos cortes, cinco grupos | Sensibilidad a orientación |

Mantener al menos quince etiquetas de validación y ochenta de train externo por fold; resolver empates geométricos por identificador canónico. Las etiquetas intervienen únicamente para distinguir el conjunto oficialmente etiquetado, nunca sus magnitudes para diseñar bloques. Los folds internos retiran uno de los grupos disponibles de outer-train por vez, como en la corrección anterior. No escoger el mejor esquema después de observar errores.

Guardar tres OOF separadas de 138 filas por procedimiento, métricas por fold, estado y tercil de área, y composición regional. La frecuencia de selección es descriptiva de estos ajustes dependientes; no acredita nuevas observaciones. Un esquema no viable bloquea la promoción y no se sustituye silenciosamente. Las sensibilidades leave-one-state-out y buffer de 1 km se conservan para el candidato congelado y registran inviabilidad sin afectar el denominador del criterio principal.

### 5. Diagnóstico específico de Hidalgo antes de atribuir errores al modelo

Cruzar las OOF actuales por `ID_POLIGONO` con estado/municipio, etiqueta, superficie, soporte satelital y `parcel-raster-coverage.parquet`. Publicar residuos firmados/absolutos, contribución al error cuadrático, conteos de etiquetas, faltantes por variable y soportes por sensor. Revisar los casos con mayor error y muestras municipales pequeñas; repetir el mismo diagnóstico con las OOF nuevas.

Las observaciones revisadas no se borran por residuo elevado. Una discrepancia demostrada con los originales produce una transformación derivada y registro por campo, versión y hash, sin modificar el original. Si cambia la versión de etiquetas, repetir referencia y candidato sobre las mismas 138 filas, identificando separadamente el efecto de la corrección de datos. Si un error demostrado impide mantener 138 etiquetas oficiales válidas, bloquear el experimento y registrar la necesidad de revisar ese alcance; no admitir automáticamente menos parcelas. Nuevas campañas, fechas, variedad, riego y fertilización quedan en una lista futura con disponibilidad y verificación pendientes; no son tareas de descarga en esta fase.

### 6. Decisión de promoción separada de la selección de modelos

Aplicar exactamente los requisitos de `specs/yield-model/spec.md`: ganancia de al menos 2% sobre la referencia regional en el esquema principal y al menos dos de tres esquemas; promedio de las tres razones de RMSE no mayor de 0.98; ninguna razón mayor de 1.05; MAE por estado no más de 10% superior a la referencia en ningún esquema elegible. Reportar razones y condiciones individuales, sin condensar todo en una etiqueta de éxito.

Con las etiquetas actuales intactas, la meta principal equivale aproximadamente a RMSE menor o igual a 0.7291 t/ha; es un umbral de aceptación, no una predicción de resultado. Si la referencia tiene RMSE no positivo o no finito, bloquear la decisión y conservar el motivo en vez de dividir por cero. No comparar como independiente una referencia de otra versión de datos. Superar el gate permite elegir el procedimiento congelado para uso local; sus métricas siguen siendo de desarrollo, condicionado por las iteraciones anteriores.

Si falla, conservar el modelo vigente completo, las tablas de comparación y una conclusión negativa. No iterar nuevas grillas hasta alcanzar el umbral dentro de este cambio; una nueva hipótesis requiere revisar el protocolo y registrar otra ejecución.

### 7. Artefactos, intervalos y explicaciones compatibles

Agregar un identificador de ejecución y destinos explícitos para artefactos experimentales. El conjunto de grupos de cada esquema vive en archivos de la ejecución; no sobrescribir `parcels.parquet` para alternar esquemas. `Candidate` y los contratos registran tipo directo/compuesto, intensidad de corrección, estado oficial requerido, columnas de cada componente, fuentes, esquema, política y hashes.

Adaptar `fit_selection`, `predict_selection`, recopilación de variables y `Predictor.explain` a una interfaz de componentes que pueda describir referencia y corrección. Para GPR, mostrar sensibilidades no aditivas; para CatBoost conservar SHAP cuando corresponda. La identidad exacta exigida es referencia más corrección ponderada igual a predicción; en ensambles se suman los componentes con sus pesos. Mantener comprobación de producción = rendimiento por superficie.

Recalibrar con el grupo interno separado y sin sus etiquetas en selección. Conservar nominal 90%, mínimo de calibración de 25 y admisión de intervalos solo con cobertura OOF del esquema principal al menos 85% y artefacto final compatible. Publicar también cobertura/amplitud por esquema y estado, sin ajustar el radio con etiquetas externas. Una cobertura insuficiente desactiva intervalos; no inventa otro nominal ni impide por sí sola una predicción puntual válida.

## Risks / Trade-offs

- [Sesgo acumulado por explorar las mismas 138 etiquetas] → Declarar todas las ejecuciones como desarrollo, congelar decisiones antes de sus resultados y reservar la confirmación para nuevas etiquetas o el test oficial.
- [Hidalgo tiene pocas etiquetas y algunos municipios aún menos] → Corrección compartida, intensidades discretas y diagnóstico con conteos; no construir reglas municipales por sus residuos.
- [La grilla reducida descarta una alternativa útil] → Conservar comparación histórica y variantes rechazadas; asumir esa pérdida potencial para evaluar menor variabilidad.
- [Tres esquemas comparten etiquetas y ajustes] → Reportes separados y razones descriptivas, sin tratar 414 predicciones como observaciones independientes o calcular significancia como si lo fueran.
- [Datos climáticos regionales pueden actuar como identificadores de ubicación] → Ablaciones, evaluación espacial y explicación de su escala; NASA y DGSIAP no se presentan como causas parcelarias.
- [Código nuevo invalida contratos anteriores] → Aislar experimentos y conservar paquetes íntegros de ejecución; no reescribir el hash antiguo para eludir validación.
- [No se supera el criterio de aceptación] → Terminar con evidencia negativa y versión vigente recuperable; no prometer una reducción de RMSE.

## Migration Plan

1. Antes de editar código de implementación, crear una versión recuperable de código, dependencias, datos procesados requeridos, modelos, contratos, OOF, exportaciones e informes actuales; comprobar inferencia desde esa versión íntegra.
2. Desarrollar y ejecutar en un directorio experimental aislado dentro del proyecto, con su propia copia de código y destinos de resultados. Los insumos grandes pueden copiarse o referenciarse en modo lectura con hash, pero todos los archivos necesarios para ejecutar la versión vigente deben permanecer recuperables. No instalar el código experimental sobre el servicio vigente para leer contratos antiguos.
3. Guardar política y particiones congeladas, diagnóstico y resultados bajo un identificador nuevo; verificar ambas rutas y la decisión de promoción en procesos nuevos.
4. Si pasa el gate, preparar una versión completa con ajuste final sobre 138 etiquetas, calibración compatible y exactamente 59 salidas, regenerar informes desde esa versión y ejecutar las pruebas de integración/aplicación sin red.
5. Promover código, datos requeridos, modelos, contratos e informes como una unidad después de todas las verificaciones. Conservar la versión anterior y una receta de restauración; volver a ella íntegramente si la nueva versión falla en compatibilidad o inferencia.
6. Si no pasa, mantener el código y los artefactos vigentes, publicar únicamente el informe experimental con la decisión negativa y conservar su paquete para reproducción. No desplegar ni enviar al organizador en esta fase.
