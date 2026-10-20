## 1. Preparación y aislamiento

- [x] 1.1 Crear `experiments/hidrica-estres-20261009/` con rutas e importaciones aisladas y copias necesarias de módulos/entradas; verificar con un recibo de orígenes y hashes que ningún destino experimental apunta a la activa o a fases históricas.
- [x] 1.2 Importar por ID población, etiquetas y tres esquemas espaciales originales; verificar 197 IDs, 138 etiquetas, 59 consultas, corte, asignaciones y hashes contra `scheme-validation.json`, sin regenerar grupos.
- [x] 1.3 Inventariar artefactos protegidos y versiones/dependencias de cada control; entregar manifiesto inicial y comprobar que las diez columnas del modelo seleccionado coinciden con el artefacto recuperado, diferenciándolas de columnas disponibles.

## 2. Auditoría semántica y adquisición acotada

- [x] 2.1 Revisar diccionario, CSV y documentación accesible del proveedor de NDWI; entregar `spectral-audit.json` con fórmula/bandas/orientación comprobadas o desconocidas, cobertura por sensor y decisión de habilitar/excluir S sin usar rendimiento.
- [x] 2.2 Inventariar evidencia accesible de variedad, siembra y temperatura local por ID/campaña; entregar `agronomic-metadata-audit.json` que conserve desconocidos y compruebe que no se incorporan campos inferidos ni ramas predictivas nuevas.
- [x] 2.3 Verificar catálogo oficial SoilGrids y recuperar recortes de retención a 33/1500 kPa, medias y quantiles, dentro de zona y presupuesto del diseño; entregar registro de consultas, bytes/tiempo, licencia, fechas, metadatos y hashes, o un recibo de inviabilidad recuperable sin sustituir proveedor.
- [x] 2.4 Verificar conversión volumétrica, presiones, profundidades, resolución, CRS, NoData y volumen de referencia de las capas; entregar `soil-admission.json` y demostrar con datos sintéticos que incoherencias o metadatos indispensables ausentes excluyen G.

## 3. Variables de suelo y señales compartidas

- [x] 3.1 Implementar extracción por área con máscara común y AWC por espesor para 0–30/30–60 cm; verificar unidades mediante casos sintéticos de 0.20/0.10 m³/m³ y espesores conocidos, y conservar valores incoherentes como faltantes diagnosticados.
- [x] 3.2 Implementar cobertura parcelaria y admisión G de 95% de área por valor y 90% de parcelas con ambos estratos; verificar parcelas sin centro de píxel, capas con máscaras distintas y conservación de las 197 filas ante cobertura parcial.
- [x] 3.3 Producir envolventes de sensibilidad de retención y, si hay capas a 10 kPa válidas dentro del presupuesto, comparación descriptiva de presiones; verificar que no se presentan como intervalos calibrados ni entran al catálogo predictivo.
- [x] 3.4 Construir las tablas W01-O/E y el bloque R desde entradas oficiales/NASA verificadas; comprobar mismas columnas base, ventanas, celdas, unidades, ausencia de radiación en W01-E y ausencia total de NASA en W01-O.

## 4. Estrés estadístico y controles de soporte

- [x] 4.1 Implementar semanas de siete días, asignación por fecha central y soporte NDWI de dos fechas, cuatro semanas y 50% por ventana; verificar corte, duplicados, semanas entre meses y lagunas que permanecen faltantes sin interpolación.
- [x] 4.2 Implementar aprendizaje en train de umbrales relativos VPD/NDWI y fracciones marginales de W03-M; verificar deduplicación celda/semana, peso igual por parcela, denominador común e invariancia ante modificación de etiquetas externas.
- [x] 4.3 Implementar los seis productos normalizados y tres proporciones conjuntas de W03-I; verificar escalas ajustadas solo en train, efectos principales conservados y exclusión de columnas semanales no aprendibles sin inventar umbrales.
- [x] 4.4 Verificar puertas de viabilidad con casos sintéticos de NDWI desconocido, semanas insuficientes y bloques sin columnas informativas; comprobar exclusión S cuando corresponda y continuidad de controles/R sin atribuciones fisiológicas.

## 5. Selección y congelación del protocolo

- [x] 5.1 Implementar las dos familias y cinco configuraciones del diseño, referencias y transformaciones aprendidas en train; verificar comportamiento con estado ausente, columnas constantes/faltantes y ausencia de ranking global o uso de la selección final activa.
- [x] 5.2 Registrar W00, seis variantes comunes y W05 con ocho subconjuntos G/S/R; verificar máximo 42 candidatos W05 y 84 comunes, deduplicación por viabilidad previa y conservación de IDs/razones de exclusión sin introducir ensambles.
- [x] 5.3 Implementar selección interna y puertas de mejora frente a referencia y control, desempates, respaldo y tratamiento de candidatos inviables; verificar sintéticamente que una mejora aislada o perjuicio estatal no admite un bloque y que W05 no depende de ganadores externos.
- [x] 5.4 Implementar supervisor y recuperación de proceso sin red; ejecutar preflight sintético que verifique límites agregados de memoria/hilos/tiempo, exportación float64 y tolerancia 1e-10 sin modificar entornos de controles.
- [x] 5.5 Congelar `frozen-protocol.json`, auditorías, catálogo efectivo, esquemas, versiones y hashes antes del primer ajuste predictivo de la fase; verificar que un cambio posterior bloquea reutilizar el identificador y que no hay resultados externos nuevos anteriores a la congelación.

## 6. Controles y comparaciones verificables

- [x] 6.1 Recuperar W00 oficial/seleccionada con versiones originales y los tres esquemas; verificar antecedentes, contratos y 59 consultas, y bloquear comparaciones si el control no reproduce su identidad o resultados.
- [x] 6.2 Ejecutar W01-O/E secuencialmente con selección anidada; verificar 138 OOF por esquema, métricas recalculables, referencias ajustadas en train y paquetes que recuperan 59 consultas sin red.
- [x] 6.3 Ejecutar W02 si G es viable o cerrar su no ejecución con motivo; verificar comparación pareada frente a W01-E, decisiones internas y recuperación íntegra, sin adjudicar resultado a suelo si no fue utilizado.
- [x] 6.4 Ejecutar W03-M/I si S es viable o registrar su no ejecución; verificar controles pareados, soporte temporal, columnas utilizadas y recuperación, distinguiendo efecto principal de ganancia por interacción.
- [x] 6.5 Ejecutar W04 con radiación regional compartida; verificar comparación pareada frente a W01-E y recuperación, manteniendo calidad satelital y sin convertir nubes de captura en días nublados.
- [x] 6.6 Ejecutar W05 sin reconfigurarlo con errores de diagnósticos; verificar OOF completos, selección de bloques por ajuste y recuperación de su paquete final, registrando respaldo puro sin promoción cuando no se admita información nueva.

## 7. Elegibilidad y cierre

- [x] 7.1 Calcular elegibilidad W05 con todos los umbrales frente a regional, activa y control interno; verificar pruebas sintéticas de deterioro >5%, MAE estatal >10%, esquema incompleto y ausencia de bloques nuevos, con activación/despliegue/envío en falso.
- [x] 7.2 Publicar registro incremental y reporte final de métricas por esquema/estado/fold/tercil, diferencias por parcela, decisiones y cobertura de investigación; verificar cada cifra desde OOF y separar disponibilidad, uso real, no viabilidad, resultado y elegibilidad.
- [x] 7.3 Completar recuperación global y auditoría final de integridad; entregar recibo que verifique contratos, entradas protegidas intactas, 197/138/59 IDs, consultas individuales/lote y paquetes locales de todas las ejecuciones completadas, sin trasladar intervalos activos a W05.
