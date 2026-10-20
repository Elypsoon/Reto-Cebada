## 1. Aislamiento y versiones recuperables

- [x] 1.1 Verificar H00 y H01, guardar manifiestos de código, dependencias, datos, modelos y contratos e identificar el control oficial/enriquecido; comprobar hashes y reproducir las 59 salidas activas en un proceso nuevo con tolerancia absoluta 1e-10.
- [x] 1.2 Crear una copia aislada `experiments/soporte-regional-<phase-id>` a partir de la versión regional, con originales en lectura y todos los destinos derivados internos; verificar que preparar o entrenar allí no cambie los hashes activos ni escriba fuera de los destinos permitidos.
- [x] 1.3 Parametrizar representaciones, variantes y destinos en la copia experimental manteniendo el comportamiento E00; verificar que código y dependencias de cada versión queden recuperables por hash, sin modificar contratos históricos.

## 2. Registro incremental de experimentos

- [x] 2.1 Implementar catálogo y registros por ejecución con los campos, estados y relaciones del diseño; verificar IDs únicos, rechazo de colisión y métricas pendientes como null.
- [x] 2.2 Implementar eventos, escritor único, cierre atómico y recuperación de interrupciones; verificar un fallo entre guardado de métricas y cierre, un reintento con nuevo ID y una reanudación con hashes incompatibles que sea rechazada.
- [x] 2.3 Generar `changes.json` con diferencias de procedimiento y modelo ajustado frente al control; verificar registro de tablas, fuentes, columnas, parámetros efectivos, componentes, soporte e inexistencia de modelo cuando falle el ajuste.
- [x] 2.4 Generar índice CSV e informe Markdown desde ejecuciones y manifiestos verificados; comprobar que una ejecución negativa aparece al cerrarse, una parcial conserva su estado y una revisión de interpretación conserva la anterior.
- [x] 2.5 Importar H00/H01 y los diagnósticos existentes como antecedentes, conservando hashes, procedencia y fechas de importación; verificar sus métricas originales, rechazo regional y ausencia de resultados atribuidos a E01–E08.

## 3. Política, comparaciones y particiones

- [x] 3.1 Registrar y congelar catálogo E00–E08, subvariantes, controles, orden, obligatoriedad, composición E08, fuentes y límites antes de los resultados nuevos; verificar que un cambio posterior requiera nueva versión/ejecución y que E08 excluya los factores diagnósticos definidos.
- [x] 3.2 Importar exactamente los tres esquemas H01 y construir `intraestado-3` mediante geometría y orden canónico; verificar hash histórico, determinismo al cambiar magnitudes de y, tamaños mínimos y conteos estatales por entrenamiento/validación.
- [x] 3.3 Implementar comparaciones pareadas y cierre verificado desde OOF con RMSE, MAE, R², sesgo, estados, folds y terciles; verificar rechazo de etiquetas/IDs/folds incompatibles, referencias inválidas y publicación separada por ruta/esquema.

## 4. Reproducción del control E00

- [x] 4.1 Ejecutar E00 oficial/enriquecido en los tres esquemas y guardar versiones completas y salidas finales; verificar coincidencia con OOF H01 y reproducción de 59 predicciones por ruta en proceso nuevo a tolerancia absoluta 1e-10 antes de continuar.
- [x] 4.2 Evaluar E00 en `intraestado-3` y cerrar su registro, comparación y resumen; verificar 138 OOF y soporte por estado, identificación del diagnóstico y permanencia del antecedente H00 sin esquemas inventados.

## 5. Soporte regional E01

- [x] 5.1 Implementar atenuación dura E01a y gradual E01b dentro de cada ajuste, incluida selección y calibración; verificar casos con n=0, 1, 9 y 10, referencias sin cambios y comportamiento directo/compuesto para estado ausente.
- [x] 5.2 Serializar y explicar soporte, referencia, salida original, atenuación e intensidad efectiva; verificar round-trip y composición numérica de la predicción, además de invariancia al modificar etiquetas externas manteniendo fija la consulta.
- [x] 5.3 Ejecutar E01a/E01b oficiales contra E00 en registros separados y cerrar cada uno inmediatamente; verificar sus OOF, sesgo de Tlaxcala, criterios diagnósticos, modelos finales y 59 salidas reproducibles, sin escoger la regla E08 con OOF externa.

## 6. Selección dentro del estado E02

- [x] 6.1 Implementar imputación, medias de predictores por estado, centrado y selección sobre residuos dentro del ajuste de compuestos; verificar que candidatos directos del control permanezcan iguales y que constantes/redundancia se determinen solo en entrenamiento.
- [x] 6.2 Extender contratos y consultas con medias globales/estatales recuperables; verificar invariancia a etiquetas externas y composición del lote de consultas, ausencia de corrección estatal inventada y serialización reproducible.
- [x] 6.3 Ejecutar E02 oficial contra E00 y cerrar resultados y cambios; verificar 138 OOF por esquema, frecuencias descriptivas de selección, comparación pareada y modelo final con 59 salidas verificadas.

## 7. Sustitución temporal E03

- [x] 7.1 Permitir la pareja `monthly_20_10`/`whittaker_40_10` sin ampliar otras grillas; verificar 26 candidatos, mismas filas/corte, filtro de calidad y hash de ambas tablas, conservando selector y fuentes oficiales del control.
- [x] 7.2 Ejecutar E03 oficial contra E00 y registrar cambios, calidad y resultados; verificar OOF y predicciones finales reproducibles y que un resultado favorable no cambie las representaciones congeladas de E08.

## 8. Reconstrucción y nuevos índices E04

- [x] 8.1 Implementar segmentos separados por lagunas >21 días, suavizado local, AUC respaldada y AUC/día con calidad trazable; verificar una serie sintética cuya integral excluya exactamente el intervalo sin soporte y no extrapole fuera de extremos.
- [x] 8.2 Implementar máximos locales respaldados y conservación de faltantes de temporada; verificar picos sin dos observaciones originales por lado, segmentos pequeños y máximo oculto por una laguna, sin inventar pico global o antesis.
- [x] 8.3 Generar `segmented_20_10`, ejecutar E04a oficial contra E00 y cerrar su registro; verificar población/corte, segmentos y faltantes por sensor/estado, OOF y 59 salidas con el modelo final.
- [x] 8.4 Añadir AUC respaldada de EVI/MSAVI donde estén suministrados y ejecutar E04b contra E04a; verificar unidades, ausencia estructural de índices, única diferencia de mecanismo y publicación inmediata de cambios/métricas, manteniendo E08 limitado a E04a.

## 9. Sensores y calidad E05

- [x] 9.1 Implementar las cinco máscaras declaradas con clima/topografía/área constantes; verificar retiro de columnas del sensor eliminado y conservación de dispersión espacial al retirar conteos de adquisición.
- [x] 9.2 Integrar las máscaras como elección exclusivamente interna, con dos referencias únicas; verificar máximo 122 candidatos únicos y que alterar outer-test no cambie máscara, columnas, decisiones o pesos.
- [x] 9.3 Ejecutar E05 oficial contra E00 y cerrar su historial; verificar resultados pareados, selección de sensores por ajuste y 59 salidas del modelo final, distinguiendo las métricas diagnósticas por máscara de la evaluación del procedimiento.

## 10. Regularización GPR E06

- [x] 10.1 Implementar ruido fijo y optimización acotada con parámetros del diseño; verificar 62 candidatos únicos como máximo, límites del kernel, permanencia de CatBoost/tablas y ajuste del optimizador solo con entrenamiento.
- [x] 10.2 Conservar kernel efectivo, normalización objetivo y parámetros nominales en modelos y contratos; verificar diferencia entre ruido e intensidad de corrección, round-trip e invariancia ante etiquetas externas.
- [x] 10.3 Ejecutar E06 oficial contra E00, midiendo tiempo/memoria y cerrando cambios/resultados; verificar OOF, métricas regionales y 59 salidas reproducibles, sin trasladar sus parámetros ganadores a E08.

## 11. Candidato opcional E07

- [x] 11.1 Verificar dependencias, checkpoint de regresión TabPFN-2.5, condiciones de uso y recursos en un entorno separado; entregar manifiesto de versiones/pesos/parámetros antes de su primer ajuste o motivo verificable de omisión, sin alterar el entorno activo.
- [x] 11.2 Implementar el adaptador para las dos configuraciones directas y contexto de entrenamiento; verificar transformaciones aprendidas exclusivamente en train, datos por parcela y reproducción de consultas sin depender de un joblib convencional; si E07 se omite, documentar que esta tarea no aplica.
- [x] 11.3 Ejecutar ambas configuraciones E07 sin selección externa o cerrar su omisión; verificar registros separados con OOF/59 salidas/configuración o motivo, y exclusión expresa de E08 y de cualquier activación de esta fase.

## 12. Procedimiento combinado E08

- [x] 12.1 Integrar únicamente E01a+E02+E04a según la política previa con 26 candidatos, cuatro promedios y seis ablaciones externas sobre ganadores oficiales internos; verificar hash/composición, comparaciones de fuentes independientes y prueba de contaminación de selección completa.
- [x] 12.2 Ejecutar E08 oficial/enriquecido en los tres esquemas y `intraestado-3`, guardando comparaciones por ruta frente a E00; verificar 138 OOF por esquema, soportes, sesgos, referencias y ausencia de decisiones tomadas con OOF de E01–E07.
- [x] 12.3 Ejecutar leave-one-state-out, buffer entre polígonos e intervalos recalibrados E08; verificar exclusión real, escenarios inviables preservados, ausencia de etiquetas de calibración en selección, nominal 90%, mínimo 25 y cobertura global/estatal publicada.
- [x] 12.4 Calcular elegibilidad E08 por ruta y finalizar sus modelos, contratos, cambios y 59 exportaciones; verificar todos los umbrales existentes, rechazo por perjuicio regional/esquema inválido, inferencia en proceso nuevo y `activated=false` independientemente de la elegibilidad.

## 13. Cierre de fase y entrega

- [x] 13.1 Ejecutar la suite completa experimental y comprobar inferencia/explicaciones sin red con artefactos finales; verificar composición, producción por superficie, contratos incompatibles rechazados y resultados guardados en el registro.
- [x] 13.2 Recalcular el informe acumulado desde todos los runs y sus manifiestos, incluidos fallos y omisiones; verificar cifras, enlaces, diferencias frente a controles, límites de reutilización de etiquetas y resumen actualizado tras cada ejecución.
- [x] 13.3 Preparar paquete candidato completo solo para rutas E08 elegibles o entregar la decisión negativa con artefactos; verificar reproducción desde paquete y que ninguna salida afirme activación, despliegue o evaluación oficial no realizada.
- [x] 13.4 Verificar nuevamente hashes y las 59 predicciones de la activa y entregar prioridades de nueva campaña/manejo con disponibilidad pendiente; cerrar la fase con el historial íntegro, sin ampliar grillas para forzar mejora.
