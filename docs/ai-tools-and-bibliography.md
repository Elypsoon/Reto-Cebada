# Fuentes y registro de asistencia de IA

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

Herramientas de asistencia de IA: Se utilizaron exclusivamente OpenAI Codex y Google Gemini. Su propósito se limitó al apoyo para la discusión y contraste de ideas, diseño y creación de la interfaz del dashboard, automatización del flujo de experimentación y apoyo en la redacción, maquetación y revisión del reporte técnico. Las métricas y tablas proceden estrictamente de la ejecución local registrada en el repositorio, no de afirmaciones de modelos de lenguaje.

Prompts humanos relevantes, conservados textualmente de la conversación:

> «revisa las bases y la invesitigación»

Propósito: contrastar la investigación inicial con los requisitos, datos y unidades del reto.

> «Acabo de subir un repo el cual contiene el dataset e investigaciones que mi colega ha empezado, revisalas, saca lo mejor de ambas, que se complementen»

Propósito: revisar el repositorio del colega y combinar las propuestas compatibles con los insumos reales.

> «si faltan datos, trata de conseguirlos primero (el reto lo permite), si no puedes o no son confiables o de calidad, limítate a lo que tenemos»

Propósito: obtener fuentes adicionales y comprobar su calidad antes de admitirlas al modelado.

> Invocación de `openspec-apply-change` para implementar el cambio propuesto.

Propósito: implementar el procedimiento, la aplicación y las verificaciones definidos en la propuesta.

También se solicitaron habilidades de modelado y visualización, instalación de OpenSpec y valoración de cómputo local. La asistencia de IA no sustituye la revisión humana de interpretación agronómica, atribución de trabajo, requisitos de entrega y cualquier publicación posterior. Los nombres y aportaciones fueron asignados por el equipo para el registro oficial de AgroCebada 2026.

> «Integrantes y aportaciones: Ángel de Jesús Elvis Gutiérrez Pacheco (Modelado, Experimentación y Estrategia Analítica); Leonardo Álvarez González (Desarrollo Web, Diseño UI/UX y Producción Audiovisual); Ángel Gabriel Aguilar Saldívar (Estadística de Datos y Validación Matemática); Iván Pérez Sánchez (Auditoría Técnica, Investigación y Fuentes Externas); Diego Cannata Cárdenas (Auditoría de Dashboard y Aseguramiento de Calidad de Datos)»

Propósito: incorporar los 5 integrantes del equipo y sus aportaciones oficiales para completar el informe, los anexos y el repositorio. Se usaron Codex y Gemini para maquetar y verificar los documentos y la sincronización técnica.

> «Revisa el proyecto, crea pruebas y mejora los resultados: El modelo obtuvo RMSE 0.790 t/ha; la media regional logró 0.744. La selección todavía necesita mejorar. NASA y DGSIAP quedaron excluidas del ajuste final.»

Propósito: revisar la selección, agregar pruebas de separación de etiquetas y referencias regionales, comparar ensambles diversos, repetir la evaluación anidada y regenerar resultados e informes. Se usaron las skills `openspec-explore`, `scikit-learn` y `pdf`; la implementación se realizó por la solicitud explícita del usuario. Los resultados anteriores se conservaron y se declaró la reutilización de etiquetas durante el desarrollo.
