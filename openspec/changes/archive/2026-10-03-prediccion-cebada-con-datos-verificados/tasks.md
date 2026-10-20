# Tasks

## 1. Entorno, insumos y contrato oficial

- [x] 1.1 Preparar entorno Python aislado, dependencias fijadas y estructura modular en la raíz sin modificar `Reto-Cebada`; verificar importación de bibliotecas y apertura del shapefile y un GeoTIFF en Windows.
- [x] 1.2 Implementar manifiesto de insumos y promover las descargas de `evidence/raw/` a una caché versionada conservando los originales; verificar los 12 hashes de `download-manifest.json` y registrar unidades, resolución, condiciones de uso y citaciones.
- [x] 1.3 Implementar importación de tabla maestra y alias `ID_POLIGON`; verificar 197 filas, 138 etiquetas, 59 ocultas y correspondencia de área/conjunto, con pruebas que rechacen claves duplicadas y etiquetas de PREDICCION.
- [x] 1.4 Auditar CRS, geometrías, solapamientos, codificaciones, fechas, nube, estadísticas inconsistentes y ausencias estructurales; entregar reporte que incluya las tres etiquetas distintas de Tlaxcala y comprobar que no se imputa NDVI de Landsat.
- [x] 1.5 Documentar el contrato y la reproducción de la auditoría en `docs/data-validation.md`; verificar que otra ejecución obtiene los mismos conteos y no cambia archivos originales.

## 2. Variables con datos del reto

- [x] 2.1 Implementar selección temporal hasta 2025-10-31 y ramas Sentinel/Planet/VI6T; verificar con casos límite que noviembre/diciembre no entran y que las campañas históricas no multiplican etiquetas.
- [x] 2.2 Construir resúmenes mensuales, integrales con intervalos reales y cobertura por sensor; verificar una serie conocida con fechas irregulares y entregar diccionario de variables con unidades y ventana.
- [x] 2.3 Implementar variantes de filtrado por nube y Whittaker semanal con criterios de soporte/lagunas; verificar que una laguna >21 días no produce un pico aparentemente válido y que observado/reconstruido quedan diferenciados.
- [x] 2.4 Extraer clima mensual y topografía con reproyección, cobertura de píxeles y NoData explícitos; verificar contra rásteres pequeños de control y revisar parcelas que no contienen centros de píxel.
- [x] 2.5 Evaluar comparabilidad de series 2022–2024 para rasgos históricos compactos; entregar decisión por variable y verificar que no se denominan rendimientos ni campañas de cebada confirmadas.
- [x] 2.6 Generar la tabla oficial de una fila por parcela y documentar configuración, calidad y diccionario en `docs/features.md`; verificar 197 identificadores, corte temporal y ausencia de rendimiento/ID/conjunto como predictores.

## 3. Candidatos externos y decisión de calidad

- [x] 3.1 Implementar lectura de NASA y asignación geoespacial a celdas verificadas, preservando soporte regional y LST; verificar 214 fechas por respuesta, unidades, valores centinela, variables físicas y deduplicación por celda.
- [x] 3.2 Repetir la comparación mensual NASA/CHIRTS con extracción definitiva y evaluar radiación, demanda atmosférica aproximada y GDD regional; entregar reporte de pertinencia y excluir variables no justificadas, sin producir alertas parcelarias ni ET0 incompleta.
- [x] 3.3 Implementar normalización DGSIAP de nombres de columnas y filtros por código de cultivo/ciclo/modalidad; verificar nueve pares estado-municipio × siete años, producción/superficie y exclusión de Emiliano Zapata de Tlaxcala y del año 2025.
- [x] 3.4 Construir candidatos históricos municipales y registrar admisión/rechazo por calidad con condiciones de uso; entregar `docs/external-data.md` y comprobar que desactivar ambas fuentes aún produce una tabla oficial completa.

## 4. Evaluación espacial y selección anidada

- [x] 4.1 Construir y guardar cinco particiones geográficas según el diseño, o justificar cuatro antes de entrenar; verificar grupos disjuntos, tamaños mínimos, cobertura de las 138 etiquetas y mapa de vecindad sin un fold separado de dos parcelas.
- [x] 4.2 Registrar configuración del criterio interno y búsquedas acotadas antes de resultados; implementar referencias globales/regionales con fallback para estados no vistos y verificar que las medias no usan etiquetas de validación.
- [x] 4.3 Implementar ajuste interno de imputación, escalado, selección de variables y configuración temporal; verificar con un caso de contaminación deliberada que cambiar etiquetas outer-test no modifica el pipeline ajustado en outer-train.
- [x] 4.4 Comparar ElasticNet/Bayesian Ridge, SVR, CatBoost y GPR reducido en la variante oficial; entregar predicciones OOF de 138 parcelas, métricas globales/regionales/superficie y tiempo/memoria medidos.
- [x] 4.5 Evaluar adición de NASA y DGSIAP dentro del ajuste interno con el criterio 2%/estabilidad del diseño; entregar comparación en los mismos folds y decisiones trazables, manteniendo el modelo oficial independiente cuando no haya mejora.
- [x] 4.6 Evaluar promedio simple y, si procede, pesos convexos ajustados solo con OOF internas; verificar pesos no negativos/suma uno y que ninguna optimización usa outer-test.
- [x] 4.7 Ejecutar sensibilidad sin/con ubicación, buffer viable y leave-one-state-out; documentar diferencias de escenario y resultados negativos sin reemplazar la evaluación principal.
- [x] 4.8 Documentar metodología, configuraciones, semillas, comparaciones y limitaciones en `docs/model-validation.md`; verificar reproducción de métricas desde las predicciones externas guardadas y distinguirlas del test oculto.

## 5. Incertidumbre, artefactos e inferencia

- [x] 5.1 Evaluar intervalos con calibración interna por grupos y tamaños mínimos del diseño; entregar cobertura/amplitud externas y verificar que un intervalo que falla el criterio no se presenta como confiable.
- [x] 5.2 Aplicar el procedimiento de selección interno a las 138 etiquetas y guardar modelos/contratos versionados; verificar reproducción de inferencia y rechazo de tabla con columnas, fuentes o versión incompatibles.
- [x] 5.3 Generar las 59 predicciones oficiales, detectar valores no finitos/negativos y exportar sin límites artificiales de train/SIAP; verificar exactitud del conjunto de identificadores, unicidad y orden determinista.
- [x] 5.4 Preparar explicaciones y guía de inferencia en `docs/inference.md`; verificar contribuciones contra salidas del modelo cuando proceda y aclarar que no representan causas ni garantías crediticias.

## 6. Aplicación y experiencia de consulta

- [x] 6.1 Construir mapa, búsqueda y filtros por parcela/estado/municipio/conjunto; verificar navegación de las 197 parcelas y distinción visible entre rendimiento observado y estimado.
- [x] 6.2 Implementar ficha con ejecución del modelo, t/ha, ha, producción total, versión y corte; verificar que el botón realiza inferencia real, sin reentrenar, y que toneladas = t/ha × ha.
- [x] 6.3 Mostrar curvas por sensor, observaciones/reconstrucciones, calidad y procedencia; verificar visualmente una parcela de buena cobertura y otra con lagunas y comprobar que el pico no se llama floración exacta.
- [x] 6.4 Incorporar métricas regionales, intervalos admitidos, descarga oficial y resumen de ficha; verificar que el CSV contiene 59 predicciones aunque el mapa esté filtrado y que no se muestran intervalos rechazados.
- [x] 6.5 Probar la aplicación sin conexión y con artefactos incompatibles; entregar mensajes comprensibles y documentar el arranque/consulta local en `docs/app-guide.md`, sin sustituciones silenciosas de modelo.

## 7. Integración y paquete del reto

- [x] 7.1 Ejecutar la ruta completa de datos oficiales y la variante seleccionada desde configuración guardada; verificar trazabilidad de hashes, reproducción de 59 predicciones y coherencia entre inferencia de consola y aplicación.
- [x] 7.2 Preparar documento técnico con resultados realmente obtenidos, bibliografía, herramientas/prompts de IA y aportaciones del equipo, respetando las extensiones de bases/guía; verificar todos los apartados y mantener dos páginas de anexos salvo aclaración oficial.
- [x] 7.3 Preparar paquete local de código, dependencias, documentación y guion de demo de hasta cinco minutos; verificar en una ejecución limpia que el guion muestra consulta e inferencia real y registrar lo pendiente de URL/entrega oficial, sin publicar.
