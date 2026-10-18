## 1. Isolated phase and provenance

- [x] 1.1 Crear `experiments/prioridades-predictivas-20261006/` con copia mínima versionada del código, tablas y dependencias de soporte regional; verificar manifiestos de origen y ausencia de copias de entornos/temporales o métricas adjudicadas a ejecuciones nuevas.
- [x] 1.2 Preparar versiones separadas de C-activa y C-soporte con rutas, importaciones y contratos originales en destinos nuevos; verificar con una prueba de resolución que cada proceso utiliza su propio código y no escribe en la activa ni en fases cerradas.
- [x] 1.3 Importar por ID `registry/schemes.csv` revisión 2 y validar población, etiquetas, corte y tamaños de los tres esquemas e intraestado; verificar igualdad de hashes/asignaciones y rechazo de duplicados, filas ocultas etiquetadas o folds incompatibles.
- [x] 1.4 Registrar L01–L08 y la matriz hipótesis–evidencia–control de P00–P08, además de las alternativas secundarias diferidas; verificar títulos, rutas/URLs, fecha, alcance de lectura y métricas pendientes sin convertir cifras bibliográficas en resultados locales.

## 2. Selectors and supported representations

- [x] 2.1 Implementar los tres selectores de P01 con lista agronómica de 16 variables y contratos de disponibilidad; verificar en datos sintéticos que el modo sin ranking conserva una relación no lineal con correlación marginal baja, mantiene imputación train-only y registra dimensiones efectivas.
- [x] 2.2 Preparar covariables ambientales y calidad común de las cinco ramas espectrales declaradas para P02/P05/P06; verificar una fila por parcela, mismos indicadores entre control y candidato, identidad de sensores y exclusión de índices estructuralmente ausentes.
- [x] 2.3 Reutilizar la auditoría NASA local y crear el eje GDD con base 0/tope 26/origen fijo definidos en diseño; verificar resultados manuales conocidos, unidades, fechas, mapeo de celdas y rechazo de temperatura diaria incompleta o incompatible.
- [x] 2.4 Crear los resúmenes calendario/térmico de P02 sobre los mismos segmentos aceptados; verificar que una laguna >21 días permanece sin integración, los tiempos repetidos se agregan sin incrementos artificiales y cada integral conserva unidades/soporte.
- [x] 2.5 Implementar proyección individual de curvas con seis coeficientes B-spline y penalización fija, sin reconstruir valores fuera del soporte; verificar mínimos de ocho observaciones/dos tercios, peso cero en lagunas y salida faltante para soporte insuficiente.
- [x] 2.6 Implementar base compartida y scores funcionales con PCA de coeficientes ajustada en train y signo determinista; verificar mínimos de 20 parcelas/50%, contratos de 2/3 componentes y rechazo explícito cuando no hay rama aprendible.
- [x] 2.7 Comprobar aislamiento de transformaciones aprendidas alterando etiquetas y curvas externas e incorporando consultas ocultas al lote; verificar invariancia de bases, selección, medias, nudos y predicción individual, sin aprender de validación ni quitar etiquetas difíciles.

## 3. Hierarchical and additive models

- [x] 3.1 Implementar Ridge jerárquico con pendientes compartidas, efectos estatales penalizados y descomposición en t/ha; verificar penalización infinita sin efecto estatal, suma estatal ponderada cero y comportamiento n=0/1/pocas etiquetas según diseño.
- [x] 3.2 Implementar GPR jerárquico con kernel Matérn más covarianza estatal y ruido fijo; verificar equivalencia del control tau²=0, parámetros efectivos serializables y media global exacta sin corrección para estado ausente.
- [x] 3.3 Implementar GAM directo y jerárquico con nudos/penalizaciones acotados y normalización train; verificar que la suma de términos reproduce la predicción y que nudos, efectos y escala no cambian con etiquetas externas.
- [x] 3.4 Fijar una versión compatible de `interpret` en el entorno de la fase e implementar EBM con los dos conjuntos de interacciones y sin early stopping aleatorio; verificar ajuste sintético, parámetros efectivos exactos y separación outer-test.
- [x] 3.5 Extender contratos y composición de referencias/correcciones para todos los estimadores nuevos; verificar consultas individuales/lotes, componentes en t/ha y errores explícitos ante contratos o transformaciones incompatibles.

## 4. Optional foundation model preflight

- [x] 4.1 Resolver pesos de regresión y dependencia de TabICLv2 desde su implementación oficial, o registrar ausencia con motivo; verificar revisión, SHA-256, condiciones de uso, ocho estimadores y semilla con preflight sintético sin medir desempeño externo.
- [x] 4.2 Resolver de forma independiente checkpoint y dependencia explícitos de TabPFN-3, o registrar ausencia con motivo; verificar que no se usa otra generación por default, identidad/hash y configuración sintética de ocho estimadores.
- [x] 4.3 Adaptar worker y receta recuperable de ambos modelos para las dos tablas fijas, preprocessing train y contexto compatible; verificar con datos sintéticos recuperación sin red, límite de recursos y rechazo de checkpoint/contexto alterado.
- [x] 4.4 Fijar entornos aislados, dispositivo, parámetros efectivos, límites opcionales y exportación float64 de 17 dígitos; verificar lectura/escritura y comparación en proceso nuevo con atol=1e-10/rtol=0 sin repetir el problema de precisión E07.

## 5. Protocols, selection and execution registry

- [x] 5.1 Construir el catálogo P00–P08, controles, representaciones, candidatos, correcciones y ensambles del diseño; verificar conteos máximos P01=78/P02=14/P03=42/P04=36/P05=51/P06=30, unicidad, dos familias/dos representaciones por bloque y límites opcionales individuales.
- [x] 5.2 Implementar selección interna anidada, orden/desempate, referencias elegibles y exclusión de candidatos inviables; verificar contaminación deliberada outer-test, reentrenamiento de FPCA/nudos/jerarquía en cada inner-train y ausencia de promedios que omiten folds fallidos.
- [x] 5.3 Extender registro para hipótesis/evidencia, fallos, omisiones, interrupciones y cierre administrativo distinto de cobertura evaluada; verificar transiciones, hashes, publicación incremental y rechazo de reutilización de IDs tras cambiar protocolos.
- [x] 5.4 Implementar evaluación de elegibilidad oficial P06 preservando E08 histórico y controles pareados; verificar rechazo por deterioro de Puebla, fallo de cualquier esquema, mejora insuficiente frente a activa y resultado diagnóstico opcional favorable.
- [x] 5.5 Integrar calibración interna separada para P06 y disponibilidad de intervalos; verificar exclusión de calibración del ajuste de bases/modelos, mínimos de 25 etiquetas, nominal 90% y bloqueo de presentación bajo cobertura principal 85%.
- [x] 5.6 Ejecutar pruebas sintéticas/integración y preflight de inventario, soporte y recursos, resolver manifiestos y congelar todos los protocolos incluidos controles/P06 antes del primer resultado externo nuevo; verificar recibo con fecha/hash y rechazo de cualquier ampliación posterior.

## 6. Paired priority experiments

- [x] 6.1 Ejecutar P00 C-activa en los tres esquemas y C-soporte con su procedimiento original, en procesos/versiones aislados; verificar principal contra antecedente a tolerancia registrada y reproducir métricas/59 consultas sin alterar hashes de la activa.
- [x] 6.2 Ejecutar P01 con los tres selectores y control de ranking; verificar OOF completa por esquema y diferencias pareadas, publicar dimensiones, selección y resultado individual sin reconfigurar P06.
- [x] 6.3 Ejecutar P02 calendario/térmico con el mismo contexto NASA, o cerrar inviabilidad documental si falta la fuente; verificar población completa, soporte/celdas/unidades y comparación con control calendarizado sin atribuir el eje a la ruta oficial.
- [x] 6.4 Ejecutar P03 jerárquico con variantes sin efecto estatal; verificar efectos/normalización aprendidos, soporte regional, OOF pareada y resultado negativo o positivo conservado en el reporte.
- [x] 6.5 Ejecutar P04 GAM/EBM con los parámetros congelados; verificar interacciones efectivas, ausencia de early stopping externo y métricas recalculadas sobre las 138 predicciones de cada esquema.
- [x] 6.6 Ejecutar P05 resúmenes/proyección funcional con componentes elegidos internamente; verificar masks y bases por fold, ausencia de curvas/etiquetas externas en ajuste y filas conservadas ante soporte insuficiente.
- [x] 6.7 Ejecutar P06 oficial con su receta original e intraestado diagnóstico, sin incorporar ganadores externos ni opcionales; verificar los tres vectores OOF, comparación frente a C-activa oficial/regional y decisión de elegibilidad sin activación.
- [x] 6.8 Ejecutar sensibilidades P06 de exclusión estatal y buffer heredado y calibración de intervalos; verificar estado ausente igual a media global, inviabilidad registrada y cobertura/amplitud por estado sin reemplazar esquemas de promoción.
- [x] 6.9 Ejecutar P07/P08 disponibles, cada uno con sus dos configuraciones fijas, o registrar omisiones individuales; verificar tres esquemas por configuración, 59 consultas recuperables y ausencia de selección por OOF externa o inclusión en P06.

## 7. Recovery and closure

- [x] 7.1 Generar paquetes por ejecución completada con código, datos, dependencias y objetos ajustados/contextos/pesos necesarios; verificar manifiestos y reproducción de métricas e inferencia de las 59 parcelas en proceso nuevo sin red.
- [x] 7.2 Publicar matriz final de cobertura y detalle por esquema, estado, superficie, fold, sesgo y diferencias pareadas, con fuentes y alternativas diferidas; verificar correspondencia de cada fila con estado/artefactos reales y declaración de evidencia de desarrollo sobre 138 etiquetas.
- [x] 7.3 Preparar decisión y paquete P06 elegible o resultado negativo con motivos completos; verificar que una omisión/fallo no cuenta como prueba completada, que un diagnóstico favorable no cambia elegibilidad y que activación/despliegue/envío permanecen falsos.
- [x] 7.4 Verificar al cierre hashes de activa, controles y fases anteriores y reproducción de sus 59 predicciones por ruta, además de la suite aplicable de la fase nueva; entregar un recibo de integridad y reportar cualquier fallo sin flexibilizar pruebas ni umbrales.
