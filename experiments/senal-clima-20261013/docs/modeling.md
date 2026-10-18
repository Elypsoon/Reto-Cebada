# Comparación y recuperación del modelo

F00-ACT recupera la política histórica original, sin reentrenar, y verifica dos rutas de 59 consultas y tres OOF. F00 usa un procedimiento acotado compartido con los perfiles D/H/M/I: GPR (1/5), ElasticNet (0.05/0.2), `monthly_40_10`/`whittaker_40_10` y base oficial con/sin columnas NASA. Referencias global/regional se ajustan exclusivamente dentro del entrenamiento. F05 tiene como máximo 82 candidatos únicos; los ajustes reales de validación se cuentan por separado.

Imputación, selección supervisada, escalado e interacciones se reajustan dentro de cada entrenamiento interno/externo. NASA histórica requiere mejora frente al control comparable sin esas columnas. Un perfil nuevo debe superar internamente su control y la referencia con al menos 2% de reducción RMSE, mejora en dos folds y protección estatal de MAE. I exige además beneficio frente a M. Las variables nuevas deben participar realmente en el selector para admitir su perfil.

F00/F01/F02/F03/F04 son comparaciones de desarrollo; F05 es el único elegible. La elegibilidad exige los tres esquemas completos, límites globales/estatales frente a regional y activa, información nueva utilizada y recuperación. Un respaldo sin información nueva tiene elegibilidad negativa. Las 138 etiquetas de 2025 se reutilizan y no representan otra campaña ni un test independiente.

Estados permitidos: planned → running → fitted → completed; fallos/interrupciones conservan evidencia y no son resultados completados. Nunca se sobrescribe una ejecución completada. Los archivos congelados y modelos se comprueban por hash; una incompatibilidad bloquea recuperación. Los paquetes conservan modelo, receta, tablas, OOF, contratos y exportación.

Al reintentar una ejecución `failed`/`incomplete`, se verifica íntegro el protocolo, se trasladan sus archivos parciales a `runs/<variante>/partials/attempt-N` y se reinicia el entrenamiento completo. No se reutilizan folds parciales como resultados definitivos. El tiempo de todas las tentativas se descuenta de las seis horas acumuladas. Una ejecución `completed` no acepta reintentos; una recuperación fallida conserva el motivo.

`signalclima.comparison.paired` alinea por ID y comprueba etiqueta, estado y partición antes de producir diferencias de predicción, error absoluto y error cuadrático por parcela, además de métricas por estado/fold. El modelo activo usa su columna `selected`; las variantes usan `prediction`. Las diferencias externas se informan y no vuelven a seleccionar candidatos.

Después de congelar, `scripts/execute.py F00` ejecuta entrenamiento y verificación en procesos distintos con red bloqueada, dos hilos y límites medidos de seis horas/6 GiB para el árbol. `scripts/offline_worker.py module signalclima.run verify F00` recupera el paquete sin red. Activación, despliegue y envío quedan falsos.

Las habilidades de scikit-learn/GeoPandas contribuyeron al control de contaminación, CRS y recuperación. Referencia comprobada: Kassis, T., Agarwal, V., He, Y., Patel, D., y Brueckner, A. M. (2026), [Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://doi.org/10.48550/arXiv.2609.00065).
