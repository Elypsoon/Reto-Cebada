## 1. Versionado y protocolo experimental

- [x] 1.1 Crear un paquete recuperable de la ejecución vigente con código, dependencias, tablas requeridas, modelos, contratos e informes; verificar en un proceso nuevo las 59 predicciones y las métricas OOF actuales.
- [x] 1.2 Preparar el directorio aislado y destinos explícitos de ejecución en `common.py`/`cli.py`, sin sobrescribir artefactos ni grupos vigentes; verificar con una prueba que los hashes de la versión activa permanecen intactos.
- [x] 1.3 Registrar la política de 26 candidatos oficiales, seis ablaciones externas cuando ambas fuentes estén disponibles, cuatro promedios y criterios de promoción; verificar contenido y hash antes del primer entrenamiento de la fase.
- [x] 1.4 Guardar particiones `principal-5`, `balanceado-4` y `rotado-45-5` por identificador; verificar igualdad del esquema principal con `folds.csv`, determinismo, independencia de valores de y y mínimos de quince casos externos/ochenta de train.

## 2. Diagnóstico regional y calidad

- [x] 2.1 Cruzar OOF vigentes, parcelas, calidad satelital y cobertura de rásteres para generar tablas parcelarias, estatales y municipales; verificar uniones uno a uno, conteos y reproducción de la contribución de Hidalgo al error cuadrático.
- [x] 2.2 Revisar los casos de Hidalgo con mayor error contra archivos originales y registrar hallazgos, muestras municipales pequeñas y ausencia de evidencia cuando corresponda; verificar que cada señalada como discrepancia tenga fuente y campo recuperables.
- [x] 2.3 Incorporar un registro versionado de correcciones verificadas de valores/variables y exclusiones de observaciones de fuentes; verificar conservación de originales y pruebas que prohíban retirar parcelas por residuos o continuar si se invalidan las 138 etiquetas.

## 3. Modelos con corrección regional

- [x] 3.1 Implementar el estimador compuesto y serializar medias aprendidas, columnas e intensidad; verificar referencia exacta con intensidad cero y media global sin corrección para un estado ausente en train.
- [x] 3.2 Ajustar residuos objetivo, `CompactSelector`, escala y corrección dentro de cada `fit`; verificar con pruebas que alterar etiquetas y covariables de validación no cambie estadísticas, configuración ni predicciones sobre una entrada de consulta idéntica, manteniendo fijo el entrenamiento.
- [x] 3.3 Extender candidatos y ensamblado para modelos directos/compuestos, intensidades 0.5/1 y las dos tablas previstas; verificar los 26 candidatos únicos, round-trip de serialización y equivalencia numérica de predicción antes/después de guardar.
- [x] 3.4 Adaptar recopilación de variables y explicaciones a los componentes regionales; verificar referencia más corrección ponderada igual a predicción, pesos de ensamble y distinción de sensibilidades no aditivas de GPR.

## 4. Selección y fuentes opcionales

- [x] 4.1 Implementar selección interna de dos familias, referencias y cuatro promedios uniformes, con admisión de 2%, dos folds y protección regional de 10%; verificar fallback, rechazo por perjuicio regional y desempate por menor complejidad.
- [x] 4.2 Comparar NASA, DGSIAP y NASA+DGSIAP sobre cada ganador oficial interno; verificar comparaciones pareadas sin fuente, independencia del orden de evaluación, registro de rechazos y ausencia de externos en `--official-only`.
- [x] 4.3 Registrar por ajuste interno candidatos, fuentes, componentes, columnas, estadísticas y decisiones; verificar que cambiar etiquetas outer-test no altere ninguna selección ni peso, y que cada contrato refleje las fuentes efectivas de cada componente.

## 5. Evaluación de robustez y decisión

- [x] 5.1 Ejecutar el procedimiento congelado en los tres esquemas para rutas oficial/enriquecida; verificar una OOF finita por cada uno de los 138 identificadores en cada esquema, sin duplicados y con métricas recalculables.
- [x] 5.2 Generar comparaciones pareadas con la media regional, métricas por estado/área/fold, frecuencia de selección y el diagnóstico regional nuevo; verificar igualdad de filas y versión de datos, y comparación histórica solo donde las particiones coincidan.
- [x] 5.3 Implementar la decisión de promoción con todas las condiciones de la especificación; verificar casos de un solo esquema favorable, perjuicio regional, esquema no viable y referencia de RMSE cero/no finito, además de un caso sintético que cumpla todos los umbrales.
- [x] 5.4 Ejecutar sensibilidad leave-one-state-out y buffer de 1 km para el procedimiento congelado; verificar exclusión real del estado, separación geométrica y registro explícito de escenarios inviables.
- [x] 5.5 Recalibrar intervalos sin etiquetas de calibración en selección y publicar cobertura/amplitud por esquema/estado; verificar contaminación de etiquetas externas, mínimo de 25, nominal 90% y desactivación cuando no se alcance 85% en el esquema principal.

## 6. Integración y resultados de la fase

- [x] 6.1 Preparar modelos finales experimentales oficial/enriquecido, contratos y exactamente 59 predicciones sin cotas artificiales; verificar en un proceso nuevo hashes, compatibilidad, fuentes y reproducción con tolerancia absoluta 1e-10.
- [x] 6.2 Ejecutar la suite completa y las pruebas de aplicación sin red contra la versión experimental, incluyendo explicaciones del estimador compuesto y producción por superficie; verificar que la versión vigente también siga reproduciendo su salida en su paquete.
- [x] 6.3 Regenerar documentación, informe técnico y PDF experimentales desde las métricas de la fase; verificar cifras, limitaciones de reutilización de etiquetas, fuentes efectivas, tablas de 59 identificadores y diseño visual, sin sustituir informes vigentes si falla la promoción.
- [x] 6.4 Aplicar la decisión registrada: promover código/datos/modelos/contratos/informes como una versión íntegra solo si pasa todas las verificaciones, o conservar la vigente y el informe negativo si falla; verificar restauración completa y registro de la decisión y versiones.
- [x] 6.5 Entregar la comparación de esta fase y una lista priorizada de datos futuros —nuevas campañas y manejo verificable— con disponibilidad pendiente; verificar que no se declare validación temporal, despliegue o evaluación oficial no realizados.
