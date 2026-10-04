# AgroCebada: rendimiento parcelario con datos verificables

Documento técnico con resultados ejecutados e integrantes proporcionados por el equipo. Corte: 31 octubre 2025. Integrantes: Leonardo Alvarez Gonzalez; Ángel de Jesús Elvis Gutiérrez Pacheco; Diego Cannata Cárdenas.

## Introducción

La estimación del rendimiento agrícola permite relacionar información ambiental, comportamiento del cultivo y producción esperada. Para parcelas de cebada, una solución útil debe expresar el resultado en unidades comprensibles, conservar la relación con la superficie y ofrecer evidencia sobre sus limitaciones. El reto AgroCebada 2026 plantea ese problema en Hidalgo, Tlaxcala y Puebla, combinando una evaluación predictiva con una herramienta tecnológica para consultar resultados. Esta propuesta transforma datos satelitales y ambientales entregados por el organizador en estimaciones retrospectivas de rendimiento y una aplicación local verificable.

El conjunto contiene 197 parcelas georreferenciadas. Se conocen 138 rendimientos de la campaña abril–octubre de 2025 y permanecen ocultos 59 para evaluación oficial. Las observaciones satelitales son considerablemente más numerosas que las parcelas, pero no constituyen nuevas etiquetas independientes. Por ello, la unidad de análisis es una parcela, representada por variables temporales compactas, características ambientales y superficie. No se replicó el rendimiento de 2025 sobre campañas anteriores ni se inventaron rendimientos para completar datos faltantes.

Sentinel-2 y Planet aportan índices ópticos y estadísticas por captura. Landsat presenta una estructura distinta: únicamente VI6T tiene información disponible. Mezclar columnas vacías con índices existentes o interpretar ese índice como temperatura introduciría errores semánticos. La precipitación y las temperaturas entregadas son mensuales; su resolución tampoco permite afirmar que se observaron heladas diarias en cada parcela. La ingeniería de variables conserva estas diferencias y explicita el origen de cada magnitud utilizada.

Las dos investigaciones iniciales se complementaron de manera selectiva. Se retomaron la representación temporal y la necesidad de validación geográfica de la primera, junto con el catálogo concreto de modelos de la segunda. Las recomendaciones se contrastaron con archivos y bases. Cuando una hipótesis requería bandas inexistentes, cultivo histórico confirmado o fuentes externas no verificadas, no se convirtió en una capacidad declarada del producto. Se consiguieron datos NASA POWER y DGSIAP como candidatos regionales y municipales, sujetos a controles de calidad y a una evaluación interna de utilidad.

La dependencia espacial constituye una dificultad central: parcelas próximas pueden compartir clima, manejo o condiciones no observadas. Una separación aleatoria podría favorecer una evaluación demasiado optimista. Se construyeron cinco grupos geográficos sin utilizar rendimientos y se mantuvo cada grupo fuera del entrenamiento cuando se estimaron sus resultados. La selección de variables, configuración temporal, fuentes y combinaciones de modelos ocurrió dentro del resto.

Finalmente, el dashboard conecta esa evaluación con una consulta real. Muestra geometría, superficie, rendimiento observado cuando existe, cálculo del modelo guardado, producción estimada, curvas y calidad. El corte de información es fijo al cierre de octubre. El producto aporta una estimación retrospectiva de 2025; extenderlo a pronósticos anticipados, campañas futuras o decisiones financieras requiere información adicional y nueva validación.

## Justificación

La disponibilidad de datos satelitales no asegura una estimación confiable si faltan controles de integridad, separación de evaluación y claridad de unidades. Con 138 etiquetas, la prioridad fue limitar complejidad, aprovechar información verificable y comunicar errores. La solución reúne modelo e interfaz mediante un servicio compartido de inferencia, evitando que una pantalla muestre valores desconectados del artefacto evaluado.

La contribución consiste en una cadena reproducible desde archivos originales hasta predicciones y consulta. Se preservan hashes, fechas, fuentes, dependencias y configuraciones. El enriquecimiento externo se admite únicamente cuando satisface un criterio predefinido dentro del entrenamiento. Un modelo independiente con datos del reto conserva funcionalidad cuando una fuente no aporta mejora.

La ejecución local facilita revisión y demostración sin depender de APIs. Esto responde al objetivo tecnológico del reto y permite examinar resultados negativos, cobertura parcial y diferencias regionales antes de cualquier uso operativo o publicación.

## Objetivos

El objetivo general es desarrollar y evaluar una solución analítica que estime rendimiento de cebada en toneladas por hectárea para las parcelas oficiales de Hidalgo, Tlaxcala y Puebla durante 2025, y permita consultar resultados mediante una aplicación funcional.

El primer objetivo específico es auditar identificadores, etiquetas, geometrías, áreas, fechas, sensores y unidades, conservando originales y trazabilidad. El segundo es construir una representación por parcela con información disponible hasta octubre, integrales temporales, resúmenes ambientales y controles de soporte para evitar fases aparentes derivadas de lagunas.

El tercer objetivo es comparar modelos compactos y referencias mediante evaluación espacial anidada, ajustando transformaciones, fuentes y ensambles únicamente dentro del entrenamiento. El cuarto es evaluar datos públicos regionales y municipales sin confundir su escala con observación parcelaria ni sustituir etiquetas.

El quinto objetivo es guardar artefactos compatibles, reproducir las 59 predicciones ocultas y ejecutar inferencia real desde una ficha interactiva. El sexto es evaluar incertidumbre, documentar diferencias entre estados y registrar limitaciones de transferencia temporal y geográfica. Finalmente, se busca preparar código, instrucciones y una demostración local que permita verificar cálculos y procedencia antes de definir alojamiento y entrega oficial.

## Metodología

Se importó una tabla maestra con clave canónica ID_POLIGONO, normalizando el alias truncado del shapefile. Se exigieron 197 identificadores únicos, 138 etiquetas positivas finitas y 59 casos PREDICCION sin rendimiento. Se compararon área y conjunto entre CSV y geometría. La auditoría incluyó CRS, geometrías inválidas, solapamientos, nube, codificaciones, fechas y estadísticas. Los originales permanecieron intactos; un manifiesto SHA-256 registró contenido, proveedor, escala, unidades y condiciones. Una segunda ejecución comprobó igualdad de auditoría y hashes.

Las capturas se limitaron a abril–octubre de 2025. Sentinel-2 se representó mediante NDVI, EVI y NDWI; Planet mediante NDVI, EVI y MSAVI; Landsat mediante VI6T. Se conservaron medianas mensuales y resúmenes compactos de abril–mayo, junio–julio y agosto–octubre. Las integrales emplearon regla trapezoidal con intervalos reales en días. Conteos y variabilidad espacial acompañaron la señal principal de cada sensor. No se imputaron índices ópticos inexistentes de Landsat ni se utilizó LAI negativo como magnitud física.

Se compararon umbrales de nube de 10, 20 y 40%, representación mensual y Whittaker semanal con penalización 10 o 100. Los pesos dependieron de nubosidad; bins sin observación tuvieron peso cero. Menos de ocho observaciones o lagunas mayores de 21 días invalidaron reconstrucción. Las fenométricas requirieron soporte a ambos lados del máximo y no se interpretaron como floración exacta. Las campañas 2022–2024 quedaron como contexto excluido porque cultivo y rotación no están confirmados.

El clima mensual y la topografía se extrajeron por intersección de celdas, máscara NoData y ponderación de área proyectada a UTM 14N. Este método contempla parcelas sin centros de píxel. Precipitación se acumuló por ventana; temperaturas se resumieron como media y amplitud. Elevación y pendiente conservaron resolución de 120 m y cobertura parcial explícita. Las tablas oficiales tuvieron entre 53 y 60 variables, según disponibilidad de fenométricas.

NASA POWER aportó cuatro respuestas diarias completas en tiempo solar local. Se verificaron 214 fechas, unidades y rangos físicos; asignación al nodo nativo más cercano mantuvo escala regional. Se evaluaron radiación, VPD aproximado y GDD con base y tope explícitos. DGSIAP se normalizó por año, cultivo, ciclo, modalidad y unidad. La unión estado–municipio produjo 63 registros de nueve municipios y siete años; rendimiento fue producción agregada dividida entre superficie cosechada. No se utilizó 2025 municipal.

Cinco grupos geográficos de 34, 34, 35, 17 y 18 etiquetas definieron evaluación externa. La evaluación interna retiró un grupo espacial por partición para imputación, estandarización, disponibilidad, redundancia, selección y configuración. Se compararon ElasticNet, Bayesian Ridge, SVR, CatBoost de poca profundidad y GPR reducido mediante 81 configuraciones. Las medias global y regional participaron como modelos elegibles, ajustados exclusivamente con entrenamiento.

Reemplazar la referencia interna, añadir una fuente o ensamble exigió mejora de RMSE de al menos 2%, mejora en dos folds internos y deterioro regional de MAE no mayor de 10%. Las fuentes se probaron sobre cada familia. Se evaluaron promedios diversos y pesos convexos internos. Se ejecutaron sensibilidades con ubicación, buffer viable y transferencia entre estados. Intervalos nominales 90% usaron calibración interna separada con al menos 25 etiquetas; solo se admitieron con cobertura externa global mínima de 85%.

Finalmente, el mismo procedimiento interno seleccionó la configuración sobre 138 etiquetas. Se guardaron pipelines y contratos, se comprobaron 59 salidas finitas sin cotas artificiales y se conectó Streamlit al servicio de inferencia. Pruebas verificaron contaminación de etiquetas, compatibilidad, aritmética de producción y operación sin red.

Cada familia también conservó predicciones externas de su configuración interna elegida. Las comparaciones utilizaron idénticas parcelas y grupos, permitiendo recalcular errores desde un archivo común. La selección final no incorporó automáticamente el algoritmo con mejor resultado externo, porque hacerlo convertiría esa comparación en información de ajuste. El contrato incluye columnas ordenadas, fuentes requeridas, versión de código, dependencias y hashes de tablas. La descarga oficial siempre considera los 59 identificadores ocultos, independientemente de los filtros del mapa; los intervalos se verifican con el modelo separado que generó su calibración.

## Resultados y discusión

La auditoría confirmó las 197 parcelas, 138 rendimientos y 59 etiquetas ocultas previstos. Los identificadores, áreas y conjuntos concordaron; no aparecieron geometrías inválidas ni solapamientos mayores de un metro cuadrado. Sentinel-2 aportó 59 040 registros, Landsat 48 626 y Planet 47 804. Esas cifras describen capturas, no tamaño muestral independiente. La exclusión de índices ausentes de Landsat y el corte temporal impidieron incorporar información posterior a octubre o convertir columnas vacías en señales ficticias.

Tlaxcala presentó tres rendimientos distintos: 2.5, 3.0 y 3.5 t/ha, con nueve, catorce y ocho parcelas respectivamente. Hidalgo tuvo 36 etiquetas y Puebla 71. Esta estructura aconseja interpretar errores regionales junto con composición y cuantización. Una predicción continua cercana a un valor observado no confirma la precisión física con que se midió la cosecha. Las salidas no se redondearon a esas categorías.

La preparación generó nueve tablas oficiales de una fila por parcela. Las representaciones mensuales conservaron 60 predictores; las reconstrucciones semanales, 53, al no generar ciertas fenométricas sin soporte general. El modelo posteriormente redujo ese espacio dentro de cada entrenamiento. El diccionario, los contratos y los indicadores de calidad permiten distinguir una variable no disponible de una observación válida. La comprobación adicional sin NASA ni DGSIAP reprodujo las nueve tablas oficiales idénticamente.

Los rásteres climáticos cubrieron las parcelas, pero la topografía mostró información parcial: una parcela tuvo elevación sobre menos de 95% de su superficie y cuatro tuvieron pendiente parcial. La cobertura mínima de pendiente fue aproximadamente 2.1%. Una media ponderada de celdas válidas puede, por tanto, representar una fracción reducida. Se mantuvo visible esa limitación y no se presentó el resumen como observación completa del terreno.

Las respuestas NASA superaron integridad temporal y física, aunque solo tres nodos se asignaron a parcelas y dos series solares fueron distintas entre las cuatro consultas. El contraste mensual definitivo frente a CHIRTS tuvo diferencias absolutas medias de 1.248°C en Tmax y 1.314°C en Tmin. Esto confirma diferencias entre productos y resolución, sin identificar cuál reproduce mejor una estación local inexistente. DGSIAP produjo 63 municipio-años completos; aporta contexto histórico de cebada grano, no una etiqueta de calidad maltera o de parcela.

La evaluación principal produjo 138 predicciones externas, una por etiqueta. El procedimiento seleccionado obtuvo RMSE __RMSE__ t/ha, MAE __MAE__ t/ha y R² __R2__. La variante oficial obtuvo RMSE __OFFICIAL_RMSE__ t/ha y la referencia de media regional __BASELINE_RMSE__ t/ha. Estos resultados evalúan el procedimiento completo de ajuste interno. No constituyen una puntuación del test oculto ni permiten elegir retrospectivamente pesos externos y conservar la misma interpretación independiente del error.

Por estado, los RMSE del procedimiento fueron __HIDALGO_RMSE__ t/ha en Hidalgo, __PUEBLA_RMSE__ t/ha en Puebla y __TLAXCALA_RMSE__ t/ha en Tlaxcala. Las comparaciones por tercil de superficie, familia y fold quedaron publicadas en los artefactos. El catálogo incluyó ElasticNet, Bayesian Ridge, SVR, CatBoost y GPR reducido, con configuración elegida dentro del entrenamiento de cada evaluación. Las diferencias describen este conjunto; no demuestran superioridad universal de un algoritmo.

La selección final utilizó __FINAL_MODELS__ con estrategia __STRATEGY__. Las fuentes externas elegidas para el rendimiento principal fueron __FINAL_SOURCES__. Las decisiones por fold y ajuste final permiten distinguir calidad formal de ganancia predictiva. El criterio previo conserva un modelo oficial independiente y rechaza enriquecimientos que no muestran mejora suficientemente estable. Las sensibilidades con ubicación, buffer y estado excluido ofrecen escenarios complementarios, sin sustituir la evaluación principal por el resultado más favorable.

__BASELINE_COMPARISON__ La revisión surgió porque la selección anterior obtuvo RMSE de 0.790 t/ha frente a 0.744 de la media regional. Se incorporaron referencias elegibles, protección regional y promedios de familias diversas; NASA y DGSIAP se volvieron a evaluar. La ejecución anterior se conservó íntegra. La nueva evaluación repite las mismas parcelas y particiones, por lo que describe el procedimiento revisado, pero no es un test independiente de la decisión de desarrollo. Confirmar generalización requiere nuevas etiquetas o la evaluación oficial. No se escogió una familia directamente por su menor error externo.

Los intervalos nominales 90% tuvieron cobertura externa __COVERAGE__ y amplitud media __WIDTH__ t/ha; presentación admitida: __INTERVAL_AVAILABLE__. Su centro proviene de un modelo separado y su cobertura no está garantizada para cada estado o año nuevo. El ajuste completo tardó __MINUTES__ minutos y registró __MEMORY__ MB de memoria máxima observada al cierre de folds. No requirió GPU ni cómputo remoto. La aplicación ejecuta el modelo guardado, calcula toneladas como t/ha por hectáreas y mantiene la descarga de 59 filas pese a filtros visuales. La reproducción, las pruebas y los reportes sustentan estos resultados; siguen pendientes la evaluación oficial, validación temporal, datos de manejo y revisión humana del documento.

## Uso de la ciencia de datos en la inclusión financiera del sector agro

Una estimación parcelaria con unidades y procedencia claras puede mejorar la conversación entre productores, técnicos e instituciones financieras. Relacionar rendimiento y superficie permite expresar escenarios productivos en toneladas, revisar supuestos y reconocer qué información falta. El dashboard facilita esa consulta mediante geometrías, curvas, calidad y errores regionales. Su posible valor reside en organizar evidencia revisable, no en reemplazar la valoración integral de una operación de crédito.

Los datos regionales y municipales aportan contexto, pero no describen costos, precio recibido, liquidez, contratos, deuda, historial de pagos o capacidad de absorber pérdidas. Tampoco permiten identificar por sí solos causas de rendimiento ni asignar responsabilidad al productor. Un modelo retrospectivo de una campaña no acredita probabilidad de incumplimiento. Convertir directamente su estimación en una aprobación, rechazo o límite crediticio excedería la evidencia disponible y podría perjudicar a quienes tienen cobertura insuficiente o condiciones diferentes.

Una incorporación responsable requeriría validar campañas adicionales, documentar incertidumbre relevante, revisar desempeño por población atendida y obtener información económica consentida. Técnicos y productores deberían poder corregir datos, discutir anomalías y comprender los límites de la herramienta. Las diferencias entre estados y la cuantización de etiquetas deben acompañar cualquier interpretación de riesgo, evitando que una aproximación regional se presente como medición individual exacta.

Esta versión prepara una base tecnológica para ese trabajo: conserva trazabilidad, muestra datos parciales y separa estimación de rendimiento de garantía crediticia. La revisión humana permanece necesaria. El resultado puede apoyar diagnóstico, planificación y solicitud de información complementaria, mientras nuevas evaluaciones determinan si existe utilidad operacional. La inclusión financiera exige considerar acceso, pertinencia y consecuencias de las decisiones, además del error predictivo. Por ello, el producto comunica incertidumbres y permite examinar resultados antes de cualquier despliegue institucional o uso para decisiones sobre personas.

## Conclusiones

Se construyó una solución local que integra preparación de datos, evaluación espacial, artefactos compatibles e inferencia interactiva para parcelas oficiales de cebada. La cadena conserva originales y permite rastrear estimaciones hasta fuentes, unidades, corte y configuración. Se generaron 59 predicciones de rendimiento sin completar etiquetas ocultas ni aplicar límites artificiales derivados de entrenamiento o estadísticas municipales. La aplicación comparte el cálculo con la ejecución reproducible y transforma t/ha en producción total mediante superficie.

La revisión de ambas investigaciones resultó útil cuando sus propuestas se contrastaron con insumos reales. Representaciones temporales, familias de modelos y validación geográfica se combinaron; supuestos no confirmados quedaron excluidos. La diferenciación de sensores evitó reconstruir bandas inexistentes y la auditoría de fechas mantuvo el corte de octubre. Las campañas previas no se trataron como etiquetas adicionales ni como cultivo de cebada confirmado.

La búsqueda anidada permitió evaluar transformaciones, fuentes y ensambles sin utilizar el grupo externo para ajuste. El procedimiento obtuvo RMSE __RMSE__ t/ha en 138 predicciones espaciales. Esa cifra corresponde a la campaña y separación geográfica disponibles, no al test oculto ni a una garantía de rendimiento futuro. La publicación de referencias, errores regionales y sensibilidades permite valorar el resultado con sus restricciones, incluyendo cuantización de Tlaxcala y dependencia entre parcelas cercanas.

Los datos externos se incorporaron como candidatos verificables, con escala explícita y un criterio previo de ganancia estable. NASA no se presentó como estación de cada parcela; DGSIAP no sustituyó rendimiento parcelario ni aportó cotas de salida. La existencia del modelo oficial independiente conserva una ruta funcional cuando el enriquecimiento no mejora suficientemente. Las coberturas parciales de topografía y las lagunas temporales permanecen visibles para evitar una falsa impresión de información completa.

La computadora local fue suficiente para esta ejecución y se registraron tiempo y memoria. La inferencia utiliza modelos guardados y archivos locales, facilitando revisión y demostración. El paquete técnico conserva configuración, documentación y pruebas; alojamiento, URL y envío requieren decisiones posteriores.

Las siguientes mejoras deberían priorizar etiquetas de más campañas, fechas de manejo, características varietales y evidencia de calidad de cosecha. Esos datos permitirían evaluar pronósticos anticipados y transferencia temporal. Cualquier aplicación financiera también requiere información económica, revisión humana y evaluación de consecuencias. La solución entregada ofrece evidencia consultable y reproducible; sus límites deben mantenerse explícitos durante demostración, interpretación y evolución futura.

## Bibliografía

Véase `ai-tools-and-bibliography.md` para fuentes primarias, documentación de versiones, atribución de skills y registro de herramientas/prompts de IA. Incorporar esas referencias al formato final de entrega.

## Anexos

El archivo `output/pdf/agrocebada-anexos.pdf` contiene dos páginas: la tabla de las 59 parcelas de PREDICCION con su rendimiento final en t/ha, y el resumen de validación, trazabilidad e integrantes. Los valores se toman de `artifacts/predictions_59.csv` y las métricas de `artifacts/validation.json`. La distribución de aportaciones se realiza por indicación del usuario y se registra en `docs/team-contributions.json`.

__TEAM_CONTRIBUTIONS__
