# Design

## Context

Véase `proposal.md` para la motivación y `evidence/source-assessment.md` para las fuentes conseguidas. No hay aplicación, módulos Python ni resultados de entrenamiento verificados. El repositorio anidado `Reto-Cebada` contiene CSV, shapefile, 146 rásteres y documentos; la raíz contiene OpenSpec y herramientas de planificación.

La auditoría confirmó 197 parcelas, 138 rendimientos y 59 casos ocultos. El objetivo es abril–octubre 2025. Sentinel aporta índices ópticos; Landsat únicamente VI6T; Planet aporta NDVI/EVI/LAI/MSAVI. Las columnas vacías de otros índices de Landsat son estructurales. Las etiquetas de Tlaxcala toman tres valores distintos, por lo que la cuantización debe figurar en el informe sin corregir ni redondear predicciones automáticamente.

Se consiguieron NASA POWER diario (cuatro puntos, nueve parámetros, 214 fechas cada uno) y siete CSV DGSIAP 2018–2024 con diccionario. El subconjunto histórico verificado tiene 63 registros municipio-año. Su integridad preliminar no equivale a utilidad predictiva demostrada. El punto de partida conserva un modelo independiente que usa únicamente los datos del reto.

## Goals / Non-Goals

**Goals:**
- Separar importación, variables, evaluación, inferencia e interfaz para reproducir resultados localmente y revisar el aporte de cada fuente.
- Usar la ingeniería temporal de ambas investigaciones con la disciplina de evaluación anidada de la primera y el catálogo concreto de modelos del colega.
- Aprovechar datos externos verificables sin comprometer ejecución ni rigor si resultan inadecuados.
- Mantener una cadena verificable desde cada salida hasta los archivos originales, corte temporal y artefacto del modelo.

**Non-Goals:**
- Crear un pronóstico anticipado, un modelo validado para años nuevos o una plataforma para cualquier polígono sin datos compatibles.
- Inferir directamente componentes del rendimiento, profundidad de tepetate o causas agronómicas no observadas.
- Entrenar redes profundas, descargar imágenes satelitales crudas para HLS o introducir infraestructura remota sin una necesidad medida.
- Publicar el proyecto en FIRA, contratar alojamiento, crear cuentas o desplegar sin una instrucción posterior que lo autorice.

## Decisions

### 1. Arquitectura local y preservación de insumos

Organización prevista en la raíz: `src/agrocebada/` para importación, calidad, variables, evaluación e inferencia; `app.py` para Streamlit; `tests/` para contratos críticos; `data/processed/` y `artifacts/` para resultados regenerables. Las rutas se configuran y los insumos de `Reto-Cebada/DataSet` permanecen de solo lectura. Los datos externos de `evidence/raw/` se promoverán a una caché versionada `data/external/` durante apply, conservando hashes y procedencia; la aplicación carga artefactos y no consulta APIs.

Un entorno Python local con dependencias fijadas es suficiente para 138 filas de entrenamiento. El procesamiento satelital se reduce temprano por parcela/fecha; los rásteres se leen por ventanas. Se medirá memoria y duración antes de considerar cómputo remoto. Alternativa descartada: almacenar notebooks como única fuente de verdad, porque dificulta reproducir el orden de ejecución y compartir inferencia con la aplicación.

### 2. Contrato de datos y calidad

La clave canónica es `ID_POLIGONO`; el shapefile la entrega truncada como `ID_POLIGON`. Normalizar ese alias sin cambiar los identificadores. Mantener una tabla maestra con área, estado, municipio, conjunto y rendimiento solo si es ENTRENAMIENTO. `ID`, `CONJUNTO` y rendimiento nunca son variables predictoras. Registrar y comparar áreas del CSV y shapefile; verificar CRS, geometrías vacías/inválidas, solapamientos y duplicados antes de extracción. Un error geométrico se diagnostica y cualquier reparación conserva el original y un reporte.

CSV satelital: interpretar fechas día/mes/año, separar sensores y preservar estadísticas por captura. Auditar valores no finitos, media fuera de min/max, desviación negativa, nubosidad fuera de 0–100 y ausencias estructurales. LAI negativo es un resultado no físico de una transformación entregada, no evidencia de área foliar negativa: conservar el original, marcarlo y comparar su exclusión o tratamiento como faltante dentro de la configuración de calidad. No recortar todos los índices a 0–1, porque varios tienen otros dominios. El nombre de un índice no autoriza reinterpretar su fórmula.

Las ecuaciones entregadas y su diccionario son referencias para interpretar valores, no autorización para reconstruir bandas inexistentes. El campo de nube no describe aerosoles ni fracción de píxeles válidos. No afirmar que se ha medido esta última.

### 3. Representación temporal compacta

Primera representación: resúmenes mensuales robustos durante abril–octubre, máximos, integrales temporales con intervalos reales en días, variabilidad espacial agregada y conteo/cobertura de observaciones. Sentinel: NDVI/EVI y una selección pequeña de señal hídrica/residuos; Planet: NDVI/EVI/MSAVI y variabilidad intraparcelaria; Landsat: estadísticas temporales de VI6T, sin interpretar ese índice como temperatura en °C.

Comparar esas variables con curvas en rejilla semanal y Whittaker ponderado por nube. Rejilla y pesos se documentan; registros faltantes no reciben peso de observación. Candidatos de corte de nube: 10%, 20%, 40%, elegidos dentro de CV interna. No interpolar ni reconstruir automáticamente lagunas mayores de 21 días para estimar un pico; una fenométrica requerirá al menos ocho observaciones utilizables y soporte a ambos lados del máximo. Un fallo produce faltante y bandera de calidad, no una curva aparentemente cierta. El suavizado actúa por parcela y sensor; sus hiperparámetros elegidos con rendimiento se ajustan dentro de cada entrenamiento externo.

Derivar pico, día del pico, amplitud, duración aproximada, integral total/postpico y senescencia. Sin fechas de manejo o floración, esos son indicadores aproximados. No asumir POS = antesis ni que EVI tiene que superar NDVI. El corte fijo 2025-10-31 rige incluso si una curva permitiría completar su descenso con diciembre. Para futuras fechas anticipadas habría que reconstruir todas las variables con cada nuevo corte y volver a validar; queda fuera de esta versión.

Presupuesto inicial: aproximadamente 35–60 variables de calidad; reducción por redundancia y regularización a conjuntos pequeños, evaluando 10–25 variables para GPR. Selección agronómica y estabilidad preceden a una búsqueda extensa. mRMR es opcional; Boruta/SHAP queda como auditoría complementaria, no un paso obligatorio que valide físicamente una característica.

### 4. Clima y topografía disponibles

Reproyectar geometrías al CRS de cada ráster y calcular resúmenes ponderados por cobertura. NoData nunca se interpreta como valor. Para parcelas pequeñas que no contengan centros de píxel, usar intersección/ponderación de celdas; si se recurre a un punto representativo, explicitar método y escala. Elevación/pendiente son entregadas a 120 m en EPSG:6372; clima a 0.05° en EPSG:4326. No aumentar su información por remuestreo fino.

CHIRPS: precipitación mensual y acumulados por ventanas documentadas. CHIRTS: medias mensuales de Tmin/Tmax, temperatura media y amplitud. No producir conteos diarios de helada, calor o días secos desde estos insumos. El reparto de una lluvia mensual entre fases inferidas es una aproximación uniforme, que debe declararse o evitarse mediante ventanas mensuales. Las campañas 2022–2024 solo se usan para contexto y anomalías cuando se compruebe comparabilidad; no está confirmado que todos esos años sean cebada.

### 5. Admisión de enriquecimiento externo

La calidad se evalúa por variable antes de usar etiquetas: metadatos completos, rango físico, ≥95% de cobertura temporal para la ventana utilizada, sin lagunas interpoladas >7 días y resolución adecuada al uso declarado. NASA usa LST, no la hora civil de México; unidades de la respuesta AG: radiación MJ/m²/día, presión kPa, viento m/s, temperaturas °C, lluvia mm/día. Deduplicar consultas por celda y no contar 197 series independientes cuando muchas parcelas comparten el dato. Dos series solares distintas en las cuatro respuestas indican escasa discriminación espacial; variables casi constantes se excluyen dentro del ajuste.

NASA puede aportar demanda atmosférica aproximada y radiación. VPD se calcula con una fórmula documentada a partir de temperaturas y punto de rocío diarios y se denomina aproximación diaria regional. El contraste mensual preliminar mostró diferencias de ~1.25–1.31 °C absolutas frente a CHIRTS; se repetirá con extracción geoespacial definitiva. No sustituir el clima entregado ni generar alertas parcelarias de extremos. GDD, si se ensaya, es regional y los umbrales base/corte son opciones de sensibilidad explícitas, no valores exactos de variedad desconocida. ET0 no se calcula solo por disponer de radiación descendente: requiere FAO-56 y todos los términos/unidades verificados; de lo contrario, se omite.

DGSIAP: normalizar nombres de columnas que cambian por año, verificar `Idcultivo=5920000`, Temporal y Primavera-Verano. Relacionar por estado/municipio verificado y agregar producción/superficie, nunca promedio no ponderado de rendimientos. Históricos propuestos: mediana, dispersión y tendencia 2018–2024. Es cebada grano municipal, no exclusivamente maltera ni rendimiento de parcela. No usar 2025, no recortar salidas por cotas históricas y no reemplazar las 138 etiquetas con estadísticas municipales.

Registrar estados `rechazado`, `candidato`, `admitido` por variable/familia. SoilGrids y fuentes no descargadas permanecen rechazadas/no disponibles; si ambas familias candidatas se descartan, el producto funciona íntegramente con datos del reto. Alternativa descartada: depender de API REST SoilGrids para 197 parcelas antes de obtener un primer resultado, por acceso no verificado e idoneidad local insuficiente.

### 6. Validación y criterio de selección predefinido

Proyectar puntos representativos a UTM 14N para distancias y construir cinco grupos geográficos reproducibles solo con geometrías, buscando al menos 15 etiquetas por validación y 80 en entrenamiento. Inspeccionar fronteras y vecindad sin usar rendimiento para optimizar los grupos. Si las restricciones no se satisfacen, documentar una reducción a cuatro grupos antes de entrenar. Un buffer se ensaya como sensibilidad y solo se usa si conserva tamaños suficientes; no adoptar 3.5 km por autoridad del documento. Apan/Tepeapulco tiene dos etiquetas, por lo que no será un fold independiente. Mantener el mismo reparto para todas las alternativas.

Outer: evaluación espacial. Inner: tres particiones de grupos dentro de outer-train para hiperparámetros, imputación, escalado, selección, familias externas, pesos y, cuando proceda, calibración. Las configuraciones precomputadas de curvas son transformaciones independientes por parcela; cualquier elección guiada por rendimiento pertenece a inner. Generar predicción OOF externa para cada una de las 138 etiquetas. No optimizar pesos ni elegir fuentes con el vector OOF y después presentar su error como una evaluación independiente del ensamble seleccionado.

Referencias: media/mediana global y media regional ajustadas únicamente con train; un estado no visto usa la referencia global. Comparar ElasticNet/Bayesian Ridge, SVR-RBF, CatBoost de poca profundidad y GPR con kernel Matérn/ruido tras reducción. Búsquedas pequeñas; early stopping nunca usa outer-test. No asumir que regularización impide todo sobreajuste. CatBoost y GPR son candidatos, no ganadores declarados.

Criterio interno previo: menor RMSE. Para añadir una familia externa o ensamble, exigir reducción relativa de RMSE de al menos 2% frente a su referencia equivalente y mejora en al menos dos de los tres folds internos; MAE regional no debe empeorar más de 10% cuando haya al menos diez ejemplos de esa región. Si hay empate o no se supera el umbral, elegir menos fuentes/menor complejidad. Las proporciones y comparaciones se registran antes de revisar resultados. Después, las métricas externas describen ese procedimiento completo de selección y se publican todas las variantes; no se vuelve a ajustar contra outer-test.

El ajuste final aplica el mismo procedimiento interno sobre las 138 etiquetas para elegir la configuración y entrena con ellas. Leave-one-state-out se publica como prueba de transferencia más exigente, no como sustituto del escenario del reto, que incluye los tres estados. Reportar RMSE/MAE/R² OOF global, errores por estado y tercil de superficie, composición de folds y variabilidad. MAPE es secundario y no certifica equidad. Auditar geografía con variantes sin/con ubicación; no eliminar coordenadas exclusivamente por importancia SHAP.

### 7. Ensamble, intervalos e inferencia

Primero evaluar un promedio simple de dos modelos complementarios. Una combinación optimizada se restringe a pesos no negativos que sumen uno y se ajusta con predicciones OOF internas. No implementar `RidgeCV(positive=True)`, que no existe, ni llamar convexa a cualquier regresión con coeficientes positivos.

Evaluar intervalos de 90% con calibración interna separada por grupos y al menos 25 observaciones de calibración; reportar cobertura OOF externa, amplitud y cobertura regional descriptiva. La referencia de aceptación es cobertura global ≥85% para el nominal 90%; no garantiza cobertura en cada estado ni en nuevos años. Si la calibración no tiene tamaño suficiente o no alcanza el criterio, no se publica un intervalo confiable. La desviación de GPR sin calibración no hereda automáticamente esa cobertura; la dependencia espacial limita garantías de métodos conformales. Decidir la presentación con el criterio predefinido, no alterando el nivel tras ver fallos.

El artefacto contiene pipeline, columnas/orden, fuentes requeridas, versión de datos/código/dependencias, corte y semilla. La aplicación valida ese contrato y ejecuta inferencia; no sustituye silenciosamente un modelo enriquecido por otro sin externos. Mantener el modelo oficial como artefacto separado compatible. Exportar 59 identificadores en orden determinista con rendimiento finito; no limitar salidas al min/max de train o SIAP. Salidas negativas u otras anomalías requieren diagnóstico antes de exportar; no arreglarlas silenciosamente.

### 8. Interfaz y evidencia para el reto

Streamlit comparte el módulo de inferencia con la ejecución reproducible. Mapa y filtros llevan a una ficha con área, rendimiento observado cuando exista, botón para ejecutar cálculo, producción total estimada, fuentes/calidad y curvas diferenciadas. La descarga oficial ignora filtros visuales y siempre entrega 59 filas. Mostrar el corte y la etiqueta de estimación retrospectiva. Explicaciones describen contribuciones del modelo, sin recomendaciones de crédito ni afirmaciones causales.

Preparar código, instrucciones de ejecución, documento técnico, tablas de validación, bibliografía y registro de herramientas/prompts de IA y aportaciones del equipo. Las bases ponderan modelo/justificación 70% e interfaz 30%; la demo debe mostrar inferencia real en hasta cinco minutos. Usar el límite conservador de dos páginas de anexos mientras se resuelve la diferencia con la guía. La publicación oficial y el alojamiento requerirán autorización específica; el paquete local es verificable antes de esos pasos.

## Risks / Trade-offs

- [138 etiquetas y cuantización regional] → variables compactas, búsqueda limitada, reporte regional y comparación con referencias; no fabricar precisión ni modificar etiquetas.
- [Muchas parcelas comparten clima] → registrar celdas y resolución, validación por geografía y pruebas de contribución; no confundir tamaño de las series con tamaño muestral.
- [Fuentes externas de calidad formal pero sin señal adicional] → umbral previo, selección interna y modelo completo de datos oficiales como alternativa.
- [Fenología aproximada y ventanas incompletas] → flags de calidad, ventanas mensuales como referencia y términos de pico/postpico.
- [Intervalos con dependencia espacial] → calibración dentro de train, cobertura empírica visible y omisión cuando no sea suficiente.
- [Despliegue accidental de datos del reto] → revisar sus condiciones de redistribución y preparar paquete local; ningún upload autorizado por este cambio.
- [Dependencias geoespaciales en Windows] → entorno reproducible y prueba de carga de ráster/shapefile antes de modelar; ninguna instalación global requerida.

## Migration Plan

1. Conservar los insumos y evidencia descargada, verificar manifiestos y preparar entorno aislado durante apply.
2. Construir y validar la variante del reto, después comparar candidatos externos con el mismo reparto.
3. Versionar artefactos finales y ejecutar controles de 59 salidas, reproducción y compatibilidad antes de cargar la aplicación.
4. Para revertir una fuente/modelo, cargar íntegramente una versión anterior compatible o el artefacto oficial independiente; nunca mezclar variables de una versión con otro modelo.
5. Preparar la demo y entrega local; decidir URL/alojamiento y publicación en una instrucción posterior.

## Open Questions

- Confirmación del comité sobre dos o cuatro páginas de anexos. No bloquea modelo/interfaz; preparar dos páginas mientras se aclara.
- Formato exacto de columnas y redondeo de la carga oficial cuando la plataforma lo muestre; internamente conservar precisión completa e identificadores canónicos.
