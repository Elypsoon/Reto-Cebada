## 1. Fase aislada y controles

- [x] 1.1 Crear `experiments/ampliacion-cimmyt-<fecha-real-de-inicio>/` con código y dependencias versionados, sin editar la fase congelada ni la activa; verificar manifiesto inicial de archivos protegidos y estructura de la fase.
- [x] 1.2 Importar el maestro oficial y las asignaciones `principal-5`, `balanceado-4` y `rotado-45-5`; verificar 197 identificadores únicos, 138 etiquetas, 59 consultas sin etiqueta y equivalencia exacta de asignaciones y hashes con la fase prioritaria.
- [x] 1.3 Preparar recuperación A00 de P00-C-activa en su ruta oficial; verificar los tres vectores OOF, métricas y 59 consultas en proceso nuevo con tolerancia absoluta 1e−10, sin alterar contratos históricos.

## 2. Adquisición y auditoría CIMMYT

- [x] 2.1 Registrar C01–C05, versión resuelta, archivos iniciales, términos, condiciones efectivas de descarga y redistribución; verificar un manifiesto de fuentes que distinga publicaciones consultadas de archivos adquiridos y documente cualquier acceso pendiente.
- [x] 2.2 Implementar adquisición y lectura de los tres archivos iniciales con hashes y lector XLSX fijado; verificar archivos íntegros y esquema real o conservar tarea pendiente de adquisición si falta acceso, sin evadir autenticación ni inventar una tabla vacía equivalente.
- [x] 2.3 Mapear diccionario, claves y cardinalidades hacia el esquema canónico, resolviendo grano, unidades, área, campaña y ubicación; verificar un informe de columnas reales y pruebas que rechacen duplicados conflictivos y multiplicación muchos-a-muchos.
- [x] 2.4 Implementar deduplicación y agregación documentada de cosechas, conversiones explícitas y filtros de producto/ciclo/modalidad/fechas; verificar casos de forraje, resiembra ambigua, unidades desconocidas, cosecha cruzada, área inválida y rendimiento cero legítimo.
- [x] 2.5 Construir `C-local`, `C-mexico`, espacios de nombres y grupos de dependencia por productor/parcela/campañas bajo la revisión autorizada de puntos; verificar conteos y trazabilidad de cada exclusión, colisiones con claves oficiales y agrupación de campañas repetidas sin copiar etiquetas, distinguiendo candidatos agronómicos de admisión espacial pendiente.
- [x] 2.6 Publicar resultado de auditoría y compatibilidad, incluyendo modalidad/humedad oficial conocidas o desconocidas, fuentes C06/C07 y búsqueda geográfica del 9 de octubre de 2026; verificar embudo recalculable de registros publicados, descargados, armonizados y admitidos, referencia/precisión/semántica desconocidas frente al supuesto autorizado y reconciliación del bloqueo e informe previos conservando antecedentes, con diagnóstico explícito si la población auxiliar resulta insuficiente.

## 3. Características comunes y separación espacial

- [x] 3.1 Implementar `cimmyt-point-assumption-v2` con coordenadas originales, referencia de origen desconocida, WGS84 asumido, controles de coherencia con México y caja principal ±0,01°; verificar asignación de toda la caja a una única celda nativa, rechazo de contacto con límites, puntos faltantes/incompatibles y documentación posterior contradictoria, preservación de longitudes negativas y ausencia de precisión deducida de decimales, polígonos reales o índices ópticos reconstruidos.
- [x] 3.2 Preparar adquisición histórica NASA por celda/año, parámetros y fechas fijados, con caché, máximo 1.000 consultas y tres intentos; verificar reutilización de caché, preservación de respuestas oficiales 2025 y pruebas con respuestas locales para fallos, rellenos, unidades y cobertura de 214 días.
- [x] 3.3 Construir `common-area-nasa-v1` con diez variables continuas y cuatro indicadores estatales; verificar mismas columnas, definiciones y unidades entre fuentes, clima correspondiente al año de cada observación y 197 filas oficiales completas sin modificar representaciones históricas.
- [x] 3.4 Implementar exclusión auxiliar por caja principal ±0,01°, buffer de 2.000 m y grupo de dependencia en cada ajuste externo/interno; verificar límite inferior conservador de distancia en metros para toda la caja, incertidumbre en el umbral, zonas geográficas distintas, todos los puntos del grupo, exclusión conjunta de campañas y aplicación simultánea frente a validaciones interna y externa.
- [x] 3.5 Aplicar mínimos de 30 rendimientos, diez grupos y dos campañas después de exclusión/muestreo; verificar inviabilidad del candidato completo si falla un fold interno y respaldo oficial trazable sin eliminar ninguna etiqueta de la evaluación.
- [x] 3.6 Publicar antes de adquirir clima auxiliar o entrenar la sensibilidad de admisión por cohorte y ajuste para políticas estrecha (±0,001°/1.000 m), principal (±0,01°/2.000 m) y amplia (±0,02°/3.000 m); verificar claves, hashes, conteos, cambios de viabilidad y etiquetas de sensibilidad, sin consultar clima ni ajustar modelos con las políticas alternativas, escoger el margen por resultados o ampliar el catálogo.

## 4. Modelo y protocolo experimental

- [x] 4.1 Implementar Ridge ponderado y escalado aprendido con pesos oficiales 1 y auxiliares λn/(G n_g); verificar masa auxiliar total λn, igual influencia por grupo y equivalencia numérica con la función objetivo documentada.
- [x] 4.2 Implementar catálogo de como máximo 16 candidatos, selección de α, cohorte e influencia solo en validación interna oficial, desempates y regla de admisión; verificar catálogo deduplicado por hash, alternativa sin auxiliares y registro íntegro de candidatos rechazados o inviables.
- [x] 4.3 Implementar A03 por fracciones 25/50/100% de grupos y A04 opcional con dos contextos TabPFN-3 fijos y máximo 256 auxiliares locales; verificar muestreo reproducible, conservación de claves, renormalización de pesos en A03 y ausencia de replicación artificial en A04.
- [x] 4.4 Ampliar el registro de la nueva fase para auditoría, acceso pendiente, ejecución y cierre predictivo separado, y aplicar supervisor de recursos y trabajador sin red; verificar transiciones, integridad del protocolo, límites agregados del proceso y rechazo de resultados parciales como completados.
- [x] 4.5 Completar pruebas de contaminación: alterar etiquetas externas e internas retenidas manteniendo fijos los ajustes correspondientes; verificar que sus auxiliares, transformaciones, elección, pesos y predicciones no cambian, y que las 59 consultas nunca aportan etiquetas ni calibración.
- [x] 4.6 Ejecutar preflight sintético de recursos, contexto opcional y recuperación; verificar identidad del checkpoint/licencia/entorno ya autorizados, tiempos y memoria, y registrar disponibilidad u omisión de A04 sin reabrir la pregunta de finalidad no comercial.
- [x] 4.7 Congelar `cimmyt-point-assumption-v2`, autorización y antecedente, hashes de los siete documentos de planificación, cohortes, políticas espaciales/sensibilidad, contratos de características, particiones, catálogo, criterios, semillas y manifiestos antes del primer ajuste real; verificar rechazo de alteraciones bajo un mismo identificador y que las reglas coinciden con este diseño.

## 5. Ejecuciones condicionadas a datos admisibles

- [x] 5.1 Ejecutar A01 y las dos referencias sobre los tres esquemas; verificar una OOF por cada una de las 138 parcelas y esquema, métricas recalculables, soporte estatal y 59 consultas compatibles, o documentar bloqueo si no existe representación oficial común completa.
- [x] 5.2 Ejecutar A02 cuando existan candidatos auxiliares viables, conservando resultados de selección y respaldo por fold; verificar comparación pareada con A01 y A00, conteos y pesos reales, o registrar no viabilidad demostrada sin presentar un modelo oficial renombrado como ampliación probada.
- [x] 5.3 Ejecutar A03 donde la receta A02 admita auxiliares; verificar curvas con grupos y pesos congelados, identidad del 100% con A02 y estados no aplicables/inviables donde corresponda, sin escoger retrospectivamente el mejor tamaño externo.
- [x] 5.4 Ejecutar las dos configuraciones A04 si supera acceso, soporte y preflight; verificar sus tres comparaciones oficiales pareadas y contextos recuperables, o registrar omisión/no viabilidad con motivo sin atribuirle métricas de P08.

## 6. Conclusión y recuperación

- [x] 6.1 Generar informe de disponibilidad, aporte de etiquetas y competitividad operativa por separado; verificar criterios congelados frente a A01/A00/media regional, RMSE/MAE/R²/sesgo, estado/fold/área, frecuencia de respaldo y conteos de parcelas/productores/campañas sin sumar repeticiones como etiquetas independientes, y expresar cualquier mejora como estabilidad predictiva condicionada al supuesto de puntos junto con sensibilidad de admisión e incertidumbres geográficas pendientes.
- [x] 6.2 Recuperar cada ejecución realmente completada en proceso nuevo sin red y recalcular métricas desde OOF; verificar predicciones a 1e−10, modelos, contextos, cohortes, exclusiones, pesos, contratos y manifiestos respetando las restricciones de redistribución.
- [x] 6.3 Cerrar la cobertura con estados predictivos y de auditoría diferenciados, dependencias pendientes explícitas y conclusiones positivas o negativas sustentadas; verificar manifiesto final de archivos protegidos, ausencia de activación/despliegue/envío y conservación de las decisiones E08/P06.

Un requisito de acceso pendiente mantiene abiertas las tareas dependientes. Una tarea condicional solo puede cerrarse con ejecución verificada o con el diagnóstico de omisión/no viabilidad que su descripción exige; ese cierre administrativo nunca significa que el modelo o la fuente se hayan probado predictivamente.

Revisión documental del 9 de octubre de 2026: se conservan las nueve tareas completadas y se añade 3.6 pendiente. Ninguna modificación de este archivo acredita implementación de la revisión espacial. A04 mantiene su cierre de no viabilidad por el máximo local de 29 etiquetas.
