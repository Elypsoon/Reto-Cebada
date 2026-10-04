# AgroCebada: selección robusta y corrección regional (experimental)

Documento técnico con resultados ejecutados e integrantes proporcionados por el equipo. Corte: 31 octubre 2025. Integrantes: Leonardo Alvarez Gonzalez; Ángel de Jesús Elvis Gutiérrez Pacheco; Diego Cannata Cárdenas.

## Introducción

La estimación del rendimiento agrícola permite relacionar información ambiental, comportamiento del cultivo y producción esperada. Para parcelas de cebada, una solución útil debe expresar el resultado en unidades comprensibles, conservar la relación con la superficie y ofrecer evidencia sobre sus limitaciones. El reto AgroCebada 2026 plantea ese problema en Hidalgo, Tlaxcala y Puebla, combinando una evaluación predictiva con una herramienta tecnológica para consultar resultados. Esta propuesta transforma datos satelitales y ambientales entregados por el organizador en estimaciones retrospectivas de rendimiento y una aplicación local verificable.

El conjunto contiene 197 parcelas georreferenciadas. Se conocen 138 rendimientos de la campaña abril–octubre de 2025 y permanecen ocultos 59 para evaluación oficial. Las observaciones satelitales son considerablemente más numerosas que las parcelas, pero no constituyen nuevas etiquetas independientes. Por ello, la unidad de análisis es una parcela, representada por variables temporales compactas, características ambientales y superficie. No se replicó el rendimiento de 2025 sobre campañas anteriores ni se inventaron rendimientos para completar datos faltantes.

Sentinel-2 y Planet aportan índices ópticos y estadísticas por captura. Landsat presenta una estructura distinta: únicamente VI6T tiene información disponible. Mezclar columnas vacías con índices existentes o interpretar ese índice como temperatura introduciría errores semánticos. La precipitación y las temperaturas entregadas son mensuales; su resolución tampoco permite afirmar que se observaron heladas diarias en cada parcela. La ingeniería de variables conserva estas diferencias y explicita el origen de cada magnitud utilizada.

Las dos investigaciones iniciales se complementaron de manera selectiva. Se retomaron la representación temporal y la necesidad de validación geográfica de la primera, junto con el catálogo concreto de modelos de la segunda. Las recomendaciones se contrastaron con archivos y bases. Cuando una hipótesis requería bandas inexistentes, cultivo histórico confirmado o fuentes externas no verificadas, no se convirtió en una capacidad declarada del producto. Se consiguieron datos NASA POWER y DGSIAP como candidatos regionales y municipales, sujetos a controles de calidad y a una evaluación interna de utilidad.

La dependencia espacial constituye una dificultad central: parcelas próximas pueden compartir clima, manejo o condiciones no observadas. Una separación aleatoria podría favorecer una evaluación demasiado optimista. Se congelaron tres esquemas geográficos sin utilizar magnitudes de rendimiento, conservando cada grupo fuera del entrenamiento cuando se estimaron sus resultados. La selección de variables, configuración temporal, fuentes y combinaciones de modelos ocurrió dentro del resto.

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

La nueva fase congeló tres esquemas por identificador: principal de cinco bloques vigentes, cuatro cortes medianos y cinco bloques tras rotación de 45 grados. Todos conservaron quince casos mínimos de validación y ochenta de entrenamiento. Los mismos 138 rendimientos participaron en cada esquema; no se consideraron 414 muestras independientes. La referencia se recalculó sobre la misma versión de datos en cada partición.

Se registraron 26 candidatos: ocho configuraciones directas de GPR y CatBoost, dieciséis correcciones regionales con intensidad 0.5 o 1, y medias global y regional. Dos tablas con nube máxima 20% compararon medianas mensuales y reconstrucción Whittaker. Cada corrección aprendió medias por estado, residuos, imputación, selección y escala exclusivamente dentro del entrenamiento. Un estado ausente recibió la media global sin corrección.

La evaluación interna retiró un bloque de entrenamiento por vez. Reemplazar la referencia exigió mejorar RMSE 2%, mejorar dos folds y proteger MAE regional con deterioro máximo 10%. Se probaron NASA, DGSIAP y ambas sobre cada ganador oficial, con comparación pareada independiente del orden. Cuatro promedios uniformes completaron la búsqueda; no se ajustaron pesos continuos ni se amplió la grilla tras observar resultados.

Se diagnosticaron residuos, faltantes, soporte satelital y cobertura por estado y municipio. Diez casos difíciles de Hidalgo se contrastaron con originales; no se demostraron discrepancias y se conservaron todas las etiquetas. Las sensibilidades excluyeron estados completos o polígonos a menos de un kilómetro. Intervalos nominales 90% separaron al menos 25 etiquetas de calibración de la selección. La promoción exigió mejora estable en esquemas y protección regional, además de contratos, exportación y pruebas. Modelos, código e informes experimentales permanecieron separados de la versión vigente.

## Resultados y discusión

La fase conservó las 197 parcelas, 138 etiquetas y 59 casos ocultos, sin modificar los originales ni las fórmulas satelitales. Hidalgo tuvo 36 etiquetas, Puebla 71 y Tlaxcala 31. La cuantización de Tlaxcala, con tres valores de rendimiento, limita la interpretación física de pequeños errores. Los municipios con menos de diez casos se señalaron como muestras pequeñas.

El procedimiento enriquecido obtuvo RMSE 0.749 t/ha, MAE 0.597 t/ha y R² 0.219 en el esquema principal. La versión previa obtuvo RMSE 0.764; la referencia regional alcanzó 0.744. La reducción frente a la selección previa fue 1.91%, pero no superó la referencia. La variante oficial registró RMSE 0.756 t/ha.

En principal-5, el RMSE seleccionado fue 0.749 t/ha y el regional 0.744; razón 1.007. En balanceado-4, el RMSE seleccionado fue 0.769 t/ha y el regional 0.744; razón 1.034. En rotado-45-5, el RMSE seleccionado fue 0.749 t/ha y el regional 0.912; razón 0.822. 

Promoción rechazada: se conserva la versión vigente íntegra. Los umbrales requerían al menos 2% de ganancia principal y en dos esquemas, razón media máxima 0.98 y ninguna superior a 1.05, sin empeorar MAE regional más de 10%. También se verificó la ruta oficial; su decisión quedó registrada por separado. Estas comparaciones reutilizan etiquetas del desarrollo y no representan confirmación temporal ni puntuación oficial.

Hidalgo concentró 54.2% del error previo y 38.6% del nuevo principal. La revisión de diez residuos elevados confirmó concordancia con CSV y geometría oficiales; no aporta evidencia para retirar etiquetas. Calidad por sensor, faltantes por variable y cobertura de rásteres acompañan el diagnóstico. Las fuentes externas se admitieron exclusivamente dentro del entrenamiento y no sustituyeron etiquetas parcelarias.

El ajuste final experimental utilizó gpr direct, con fuentes nasa. Se serializaron ambas rutas y se generaron 59 estimaciones por ruta, reproducidas en un proceso nuevo. El contrato conserva código, dependencias, columnas, fuentes, intensidades y estadísticas aprendidas. Referencia más corrección ponderada reproduce el cálculo; los efectos individuales de GPR permanecen como sensibilidades no aditivas. La aplicación calcula producción multiplicando rendimiento por superficie y opera sin red.

Los intervalos nominales 90% alcanzaron cobertura principal 87.7% y amplitud media 2.867 t/ha. Su presentación quedó admitida. Hidalgo alcanzó 69.4%; la cobertura global no garantiza cobertura de cada región. Las etiquetas de calibración permanecieron fuera de selección. Se publicaron los tres esquemas y estados sin ajustar radios con etiquetas externas.

La sensibilidad dejó estados completos fuera de entrenamiento y excluyó vecinos mediante distancia entre polígonos para el buffer de 1 km. Cada escenario inviable conserva su razón y tamaño. La fase terminó en 4.04 minutos de cómputo local. No se modificó la política para buscar un resultado favorable; siguen pendientes nuevas campañas y datos de manejo verificables.

## Uso de la ciencia de datos en la inclusión financiera del sector agro

Una estimación parcelaria con unidades y procedencia claras puede mejorar la conversación entre productores, técnicos e instituciones financieras. Relacionar rendimiento y superficie permite expresar escenarios productivos en toneladas, revisar supuestos y reconocer qué información falta. El dashboard facilita esa consulta mediante geometrías, curvas, calidad y errores regionales. Su posible valor reside en organizar evidencia revisable, no en reemplazar la valoración integral de una operación de crédito.

Los datos regionales y municipales aportan contexto, pero no describen costos, precio recibido, liquidez, contratos, deuda, historial de pagos o capacidad de absorber pérdidas. Tampoco permiten identificar por sí solos causas de rendimiento ni asignar responsabilidad al productor. Un modelo retrospectivo de una campaña no acredita probabilidad de incumplimiento. Convertir directamente su estimación en una aprobación, rechazo o límite crediticio excedería la evidencia disponible y podría perjudicar a quienes tienen cobertura insuficiente o condiciones diferentes.

Una incorporación responsable requeriría validar campañas adicionales, documentar incertidumbre relevante, revisar desempeño por población atendida y obtener información económica consentida. Técnicos y productores deberían poder corregir datos, discutir anomalías y comprender los límites de la herramienta. Las diferencias entre estados y la cuantización de etiquetas deben acompañar cualquier interpretación de riesgo, evitando que una aproximación regional se presente como medición individual exacta.

Esta versión prepara una base tecnológica para ese trabajo: conserva trazabilidad, muestra datos parciales y separa estimación de rendimiento de garantía crediticia. La revisión humana permanece necesaria. El resultado puede apoyar diagnóstico, planificación y solicitud de información complementaria, mientras nuevas evaluaciones determinan si existe utilidad operacional. La inclusión financiera exige considerar acceso, pertinencia y consecuencias de las decisiones, además del error predictivo. Por ello, el producto comunica incertidumbres y permite examinar resultados antes de cualquier despliegue institucional o uso para decisiones sobre personas.

## Conclusiones

Se implementó y evaluó una selección acotada con corrección regional, fuentes pareadas y tres particiones espaciales congeladas. El RMSE principal fue 0.749 t/ha frente a 0.764 previo y 0.744 de la media regional. Promoción rechazada: se conserva la versión vigente íntegra. La mejora respecto de una versión anterior no basta para acreditar utilidad frente a una referencia sencilla.

Se conservaron todas las etiquetas y originales; ningún residuo elevado justificó retirar casos. Modelos, contratos, predicciones y documentación experimentales forman una versión separada y recuperable. Las verificaciones incluyen contaminación de etiquetas y covariables, serialización, composición de explicaciones, producción por superficie y aplicación sin conexión. La descarga contiene exactamente 59 identificadores ocultos por ruta, sin cotas artificiales.

La incertidumbre sigue siendo desigual por región y las tres evaluaciones reutilizan las mismas 138 etiquetas. No hay test independiente, evaluación oficial, validación temporal ni despliegue nuevo. La siguiente fase debería obtener rendimientos de otra campaña y fechas, variedad, riego y fertilización verificables. Esos insumos permanecen pendientes; su disponibilidad debe comprobarse antes de ampliar la complejidad del modelo.

## Bibliografía


Fase regional de 2026-10-03: asistencia de Codex con openspec-apply-change, scikit-learn, developing-with-streamlit y pdf para implementar el protocolo aprobado, comprobar contaminación, recuperar versiones, evaluar particiones, generar informes y revisar los PDF. Los prompts solicitaron aplicar la fase de selección robusta con corrección regional a la revisión previa. La política fue congelada antes de entrenar; las mismas 138 etiquetas se reutilizaron para desarrollo, sin evaluación temporal ni oficial. Se conservaron originales y versión vigente al rechazarse la promoción.

Fuentes primarias de datos y método:

- FIRA (2026). *Reto AgroCebada: Bases de participación*, *Lineamientos y Guía de Registro de Proyectos* y *Ecuaciones_indices_AgroCebada_FIRA_2026*. Documentos originales del proyecto; corte y unidades se comprobaron contra los insumos.
- NASA POWER. *Methodology and data access documentation*. https://power.larc.nasa.gov/docs/methodology/ . Datos diarios AG de abril–octubre 2025; solicitudes y hashes en evidencia OpenSpec. Consulta y descarga: 2 octubre 2026.
- DGSIAP/SADER. *Datos abiertos del cierre agrícola municipal*, 2018–2024, y diccionario. https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php . Consulta y descarga: 2 octubre 2026.
- scikit-learn. *User Guide: pipelines, preprocessing, model selection and GroupKFold*. https://scikit-learn.org/stable/user_guide.html . Versión ejecutada 1.9.1; se consultó también la documentación instalada y la skill local.
- GeoPandas. *User Guide*. https://geopandas.org/en/stable/docs/user_guide.html . Versión ejecutada 1.2.0; CRS y extracciones se comprobaron con archivos y controles pequeños.
- CatBoost. *Feature importance: ShapValues*. https://catboost.ai/en/docs/concepts/shap-values . La comprobación de aditividad se realiza contra la predicción guardada.
- Streamlit. Documentación y skill incluidas en la instalación 1.65.0, patrones de dashboard, caché, accesibilidad y AppTest. https://docs.streamlit.io/develop . Se verificaron APIs con documentación local de esa versión.
- Kassis, T., Agarwal, V., He, Y., Patel, D. y Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065v2. https://doi.org/10.48550/arXiv.2609.00065 . Atribución de las skills GeoPandas/scikit-learn utilizadas como asistencia procedimental; no es evidencia de desempeño agronómico. Metadatos comprobados en https://arxiv.org/abs/2609.00065 .

Los documentos de estrategia del usuario y `Reto-Cebada/src/propuestas_modelos.md` aportaron hipótesis y opciones de modelos. Sus cifras no verificadas no se trataron como observaciones; se retuvieron las ideas compatibles con las bases y los datos disponibles. No se usaron supuestos históricos municipales inventados.

Herramienta de asistencia: OpenAI Codex con agente basado en GPT-6, dentro de Codex Desktop. Se utilizó para exploración de archivos, elaboración de OpenSpec, código, controles, documentación e interfaz. Skills invocadas: `openspec-explore`, `openspec-propose`, `openspec-apply-change`; apoyo de `geopandas`, `scikit-learn` y `developing-with-streamlit`. Las métricas proceden de ejecución local registrada, no de afirmaciones del modelo de lenguaje.

Prompts humanos relevantes, conservados textualmente de la conversación:

> «revisa las bases y la invesitigación»

Propósito: contrastar la investigación inicial con los requisitos, datos y unidades del reto.

> «Acabo de subir un repo el cual contiene el dataset e investigaciones que mi colega ha empezado, revisalas, saca lo mejor de ambas, que se complementen»

Propósito: revisar el repositorio del colega y combinar las propuestas compatibles con los insumos reales.

> «si faltan datos, trata de conseguirlos primero (el reto lo permite), si no puedes o no son confiables o de calidad, limítate a lo que tenemos»

Propósito: obtener fuentes adicionales y comprobar su calidad antes de admitirlas al modelado.

> Invocación de `openspec-apply-change` para implementar el cambio propuesto.

Propósito: implementar el procedimiento, la aplicación y las verificaciones definidos en la propuesta.

También se solicitaron habilidades de modelado y visualización, instalación de OpenSpec y valoración de cómputo local. La asistencia de IA no sustituye la revisión humana de interpretación agronómica, atribución de trabajo, requisitos de entrega y cualquier publicación posterior. Los nombres fueron proporcionados por el usuario; la distribución de aportaciones se realizó por su indicación y no representa una auditoría individual del historial de trabajo.

> «Integrantes: Leonardo Alvarez Gonzalez, Ángel de Jesús Elvis Gutiérrez Pacheco, Diego Cannata Cárdenas, en aportaciones, solo repartelas»

Propósito: incorporar integrantes y distribuir aportaciones para completar el informe y los anexos. Se usó Codex con la skill `pdf` para maquetar y verificar esos documentos; `openspec-archive-change` se invocó para preparar el cierre del cambio.

> «Revisa el proyecto, crea pruebas y mejora los resultados: El modelo obtuvo RMSE 0.790 t/ha; la media regional logró 0.744. La selección todavía necesita mejorar. NASA y DGSIAP quedaron excluidas del ajuste final.»

Propósito: revisar la selección, agregar pruebas de separación de etiquetas y referencias regionales, comparar ensambles diversos, repetir la evaluación anidada y regenerar resultados e informes. Se usaron las skills `openspec-explore`, `scikit-learn` y `pdf`; la implementación se realizó por la solicitud explícita del usuario. Los resultados anteriores se conservaron y se declaró la reutilización de etiquetas durante el desarrollo.


## Anexos

El archivo `output/pdf/agrocebada-anexos.pdf` contiene dos páginas: la tabla de las 59 parcelas de PREDICCION con su rendimiento final en t/ha, y el resumen de validación, trazabilidad e integrantes. Los valores se toman de `artifacts/predictions_59.csv` y las métricas de `artifacts/validation.json`. La distribución de aportaciones se realiza por indicación del usuario y se registra en `docs/team-contributions.json`.

**Leonardo Alvarez Gonzalez**: Coordinación e integración del proyecto; diseño del procedimiento analítico, selección de modelos y validación espacial; interpretación de resultados y consolidación del informe técnico.

**Ángel de Jesús Elvis Gutiérrez Pacheco**: Investigación y revisión de fuentes; auditoría y preparación de datos satelitales, climáticos y geoespaciales; construcción de variables y documentación de procedencia, unidades y calidad.

**Diego Cannata Cárdenas**: Desarrollo e integración del dashboard; visualización de parcelas y resultados, consulta y exportación de predicciones; pruebas de la aplicación, empaquetado local y preparación de la demostración.
