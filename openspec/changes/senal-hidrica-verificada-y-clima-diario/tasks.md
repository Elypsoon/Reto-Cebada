# Tasks

## 1. Aislamiento e identidad

- [x] 1.1 Crear `experiments/senal-clima-20261013/` con estructura y copias mínimas identificadas; verificar rutas resueltas y entregar `registry/copy-origins.json` sin escribir en la activa ni fases cerradas.
- [x] 1.2 Registrar hashes protegidos, dependencias efectivas y separación oficial; verificar 197 IDs únicos, 138 etiquetas y 59 consultas mediante recibos de población e integridad.
- [ ] 1.3 Documentar en el README de la fase los comandos locales, versiones y límites; verificar que todos sus destinos de escritura permanecen dentro de la nueva fase.

## 2. Recuperación pública y auditorías

- [x] 2.1 Implementar recuperación con manifiestos, caché y límites de 4 GiB/45 minutos/tres intentos; verificar mediante pruebas de respuesta HTML, descarga truncada, agotamiento de presupuesto y reutilización por hash, y documentar el comportamiento.
- [x] 2.2 Auditar la definición original NDWI sin etiquetas; entregar evidencia de fórmula/bandas/procesamiento o exclusión semántica comprobada, conservando la identidad original.
- [ ] 2.3 Recuperar y extraer la alternativa Sentinel-2 L2A cuando corresponda; verificar reflectancia, B8A/B11/SCL, georreferencia, fechas únicas y superficie mediante pruebas y entregar manifiesto/serie o motivo explícito de no viabilidad dentro del presupuesto.
- [ ] 2.4 Recuperar CHIRPS v3 final diario `sat` y verificar NASA local; probar unidades, fechas, NoData, celdas compartidas y lagunas, y entregar auditoría/tabla o exclusión con evidencia sin sustitución de productos.
- [ ] 2.5 Auditar estaciones SMN y ERA5-Land con acceso ya disponible; entregar contraste de cobertura/escala o motivos de exclusión, verificando que no cambian los predictores primarios ni exponen credenciales.
- [ ] 2.6 Publicar `docs/sources.md` con fuentes consultables, descargadas, admitidas y excluidas; verificar cada afirmación contra su manifiesto, versión y archivo local.

## 3. Variables y soporte temporal

- [x] 3.1 Construir calendario de 14 días y reproducir el diagnóstico semanal sin rendimientos; probar fechas límite, intervalo truncado y duplicados, y entregar cobertura por parcela/ventana con las reglas de viabilidad predeclaradas.
- [ ] 3.2 Construir D con nueve variables, cobertura y faltantes; probar acumulados, percentiles y rachas estimadas que no cruzan lagunas, y documentar unidades, método de desagregación y soporte.
- [ ] 3.3 Construir H y sus covariables de calidad compartidas; probar máscara espacial, ponderación por duración, mínimos de fechas/intervalos y conservación de las 197 filas, y entregar diccionario de señal y calidad.
- [ ] 3.4 Construir M/I con pares climáticos/vegetales comunes y ajustes solo en entrenamiento; probar cambio de etiquetas/entradas externas, varianza nula y no duplicación de celdas en umbrales, y documentar indicadores sin diagnóstico fisiológico.
- [ ] 3.5 Resolver D/H/M/I como viables o no viables antes del entrenamiento; verificar las reglas de 90%/70%, soportes individuales y dependencias de bloques mediante `registry/viability.json`, sin bajar mínimos ni eliminar parcelas.

## 4. Metadatos opcionales

- [x] 4.1 Implementar importación local opcional de siembra, variedad y riego; probar archivo ausente, IDs ajenos, duplicación, unidades y conflictos, conservando original y normalización vinculados a campaña.
- [x] 4.2 Documentar formato y carácter descriptivo de esos registros; verificar que su ausencia o incorporación tardía no modifica ventanas, catálogo ni tablas predictivas congeladas.

## 5. Controles, catálogo y congelación

- [x] 5.1 Recuperar F00-ACT con código/política originales y sus tres OOF/59 consultas; verificar hashes y reproducción a tolerancia absoluta 1e-10, relativa cero, sin reentrenar ni alterar controles históricos.
- [ ] 5.2 Implementar F00 y perfiles D/H/M/I con GPR/ElasticNet, dos representaciones y dos opciones de fuentes de base; probar parejas equivalentes, referencias y máximo de 82 candidatos únicos, documentando diferencia entre método nuevo y activa.
- [ ] 5.3 Implementar selección interna, admisión y elegibilidad exclusiva de F05; probar contaminación deliberada de etiquetas externas, perjuicio estatal, esquema ausente y respaldo sin bloques nuevos, preservando criterios completos.
- [ ] 5.4 Implementar registro de estados, métricas pareadas y paquetes locales; probar interrupción, incompatibilidad de contratos y prohibición de sobrescribir ejecuciones completadas, y documentar recuperación/reanudación.
- [ ] 5.5 Ejecutar preflight sintético de entrenamiento y recuperación, registrar ajustes previstos y límites de seis horas/6 GiB por ejecución y congelar protocolo; verificar hashes, dependencias y rechazo de modificaciones antes del primer ajuste predictivo real.

## 6. Comparaciones reales e informe incremental

- [ ] 6.1 Ejecutar F00 en los tres esquemas y publicar su diferencia frente a F00-ACT; verificar 138 predicciones externas por esquema, métricas recalculadas y 59 consultas mediante recibo de ejecución.
- [ ] 6.2 Ejecutar F01 o registrar D no viable según la auditoría congelada; verificar comparación pareada con F00 o exclusión sin métricas inventadas y actualizar `docs/results.md`.
- [ ] 6.3 Ejecutar F02 o registrar H no viable según la auditoría congelada; verificar comparación pareada con F00 o exclusión sin métricas inventadas y actualizar `docs/results.md`.
- [ ] 6.4 Ejecutar F03/F04 o registrar sus dependencias no viables; verificar pareja de efectos principales/interacciones con idéntico soporte y publicar diferencias o exclusiones documentadas.
- [ ] 6.5 Ejecutar F05 con el catálogo viable predeclarado, incluido respaldo; verificar selección final interna, bloques realmente usados y los tres esquemas completos, sin sustituirlo por ganadores aislados.

## 7. Recuperación integral y cierre

- [ ] 7.1 Recuperar cada ejecución completada en proceso nuevo sin red; verificar modelos, tablas, contratos, hashes y exactamente 59 consultas finitas en lote e individualmente.
- [ ] 7.2 Recalcular métricas y diferencias por parcela/esquema desde OOF, y emitir decisión F05; verificar todos los criterios frente a regional y activa y la distinción entre completada, elegible e incompleta.
- [ ] 7.3 Comparar el inventario protegido inicial/final; entregar recibo de integridad y bloquear cierre ante cualquier diferencia sin actualizar expectativas para aceptarla.
- [ ] 7.4 Cerrar registro e informe con fuentes disponibles/usadas, fallos, presupuesto real y limitación de campaña única; verificar enlaces recuperables y activación/despliegue/envío en falso.
