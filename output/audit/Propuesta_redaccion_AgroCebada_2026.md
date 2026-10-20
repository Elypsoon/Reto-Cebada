# AgroCebada 2026: estimación retrospectiva del rendimiento parcelario y evaluación de sus alcances

> Propuesta editorial basada en los resultados auditados. No representa una nueva ejecución experimental. Los apartados con una sola cifra se interpretan como límites máximos. Los conteos excluyen títulos y esta nota, pero incluyen el contenido de tablas. La bibliografía y la propuesta de anexos se contabilizan por separado. Las referencias [1]–[5] se desarrollan al final.

## 1. Introducción

La estimación del rendimiento de cebada maltera a escala parcelaria puede aportar información para organizar el abasto agroindustrial, comparar condiciones productivas y orientar la evaluación de riesgos agrícolas. En sistemas de temporal, la disponibilidad de agua, las temperaturas y el manejo del cultivo interactúan durante el ciclo. Estas diferencias dificultan trasladar un promedio regional a parcelas individuales y motivan el desarrollo de herramientas que combinen observaciones territoriales con información agronómica.

La teledetección permite describir trayectorias de vegetación y variaciones espaciales mediante observaciones repetidas. Sin embargo, sus índices son indicadores indirectos: un cambio de vigor puede responder a distintas condiciones de suelo, manejo, cobertura o desarrollo. Por ello, relacionar una señal satelital con el rendimiento no equivale a identificar la causa de una pérdida. La interpretación agronómica requiere contrastes adicionales, especialmente cuando se pretende diagnosticar heladas, sequía o daños localizados.

El aprendizaje automático ofrece métodos para integrar estas fuentes, pero su evaluación presenta dificultades cuando existen pocas etiquetas y dependencia entre parcelas cercanas. Una partición aleatoria puede mantener vecinos de una misma zona en entrenamiento y validación, mientras que una partición espacial plantea una transferencia territorial más exigente. Asimismo, un buen indicador global puede coexistir con desempeño limitado dentro de determinados estados. Resulta necesario examinar ambos niveles y comparar los modelos con referencias sencillas.

Este trabajo estudia 197 parcelas de Puebla, Hidalgo y Tlaxcala correspondientes al conjunto del reto. Se dispone de rendimiento observado en 138 parcelas y de 59 parcelas adicionales destinadas a predicción, cuyas etiquetas no están disponibles en el flujo analizado. Se integran series satelitales, variables meteorológicas, información topográfica y relaciones de proximidad para comparar configuraciones predictivas. La evaluación se concentra en la campaña 2025 y no constituye una comprobación de transferencia entre años.

La arquitectura E12 combina referencias territoriales, ponderación espacial y correcciones estadísticas. Su propósito experimental es aprovechar información complementaria y examinar si mejora la estimación frente a controles regionales y al modelo previo R08. La evaluación utiliza predicciones fuera de pliegue, particiones espaciales y sorteos repetidos; además, explora intervalos construidos con residuos. Estos intervalos se analizan como aproximaciones empíricas cuya cobertura externa todavía requiere comprobación.

El alcance temporal merece una delimitación explícita. La configuración evaluada incorpora información de todo 2025, incluidas observaciones de noviembre y diciembre, posteriores a la campaña abril–octubre definida en el proyecto. En consecuencia, los resultados describen una estimación retrospectiva. Su adaptación a pronósticos anteriores a la cosecha exigiría fijar una fecha de emisión y reconstruir las variables únicamente con datos disponibles hasta entonces. Bajo este alcance, el estudio busca documentar resultados reproducibles, reconocer diferencias regionales y establecer qué validaciones adicionales serían necesarias antes de apoyar decisiones operativas.

## 2. Justificación

Las decisiones sobre producción y abasto requieren información que represente la heterogeneidad entre parcelas. Los promedios territoriales ofrecen referencias útiles, pero pueden ocultar diferencias locales relevantes. Integrar observaciones satelitales, clima y topografía permite explorar estimaciones más específicas sin asumir que una fuente aislada describe completamente el rendimiento.

La pertinencia del proyecto radica en comparar esa información con controles sencillos y cuantificar sus límites. Con una muestra pequeña y territorialmente dependiente, presentar únicamente el mejor resultado global puede inducir expectativas que no se cumplen en todas las regiones. Por ello, se examinan errores por estado, sensibilidad a las particiones y alcance de los intervalos.

El estudio aporta una base experimental para futuras herramientas de seguimiento agrícola. Sus posibles aplicaciones financieras requieren validación adicional: estimar rendimiento no demuestra capacidad de pago ni determina una indemnización adecuada. Reconocer esta separación permite orientar el desarrollo hacia usos verificables, con información transparente sobre incertidumbre y condiciones de aplicación.

## 3. Objetivos

**Objetivo general.** Desarrollar y evaluar una arquitectura experimental para estimar retrospectivamente el rendimiento de cebada a escala parcelaria en Puebla, Hidalgo y Tlaxcala durante la campaña 2025, integrando información satelital, meteorológica, topográfica y territorial, y delimitando su desempeño e incertidumbre.

**Objetivos específicos.**

1. Construir variables que describan trayectorias de vegetación, condiciones meteorológicas y características del entorno, documentando su disponibilidad temporal y su interpretación como indicadores indirectos.
2. Comparar la arquitectura E12 con la media estatal B0 y el control R08 mediante errores globales y regionales, utilizando predicciones fuera de pliegue y particiones espaciales.
3. Examinar la variabilidad del desempeño mediante sorteos repetidos y distinguir estos resultados de una evaluación externa sobre nuevas campañas o parcelas con etiquetas independientes.
4. Describir la construcción y cobertura de los intervalos empíricos, identificar limitaciones del preprocesamiento y establecer los requisitos para una evaluación prospectiva y posibles aplicaciones de apoyo a decisiones.

## 4. Metodología

**Datos y alcance.** Se analizaron 197 parcelas: 138 con rendimiento observado, expresado en toneladas por hectárea, y 59 destinadas a predicción sin etiquetas disponibles. Las observaciones etiquetadas corresponden a Puebla, Hidalgo y Tlaxcala, con 71, 36 y 31 parcelas, respectivamente. No se dispone de evidencia evaluada de Guanajuato. La campaña documentada abarca abril–octubre de 2025; algunas características utilizan el año completo, por lo que la evaluación se interpreta retrospectivamente [5].

**Fuentes y características.** Se integraron series de Sentinel-2 y PlanetScope, variables meteorológicas, topografía y relaciones geométricas entre parcelas. Se construyeron indicadores de vigor, senescencia, variación intraparcelaria, condiciones previas y posteriores al ciclo, y ventanas meteorológicas asociadas al máximo de vegetación. La coincidencia entre ese máximo y una etapa fenológica específica se considera una aproximación que requiere contraste de campo. Los mínimos espectrales se utilizaron como descriptores, sin equipararlos a diagnósticos confirmados de siniestro.

Las consultas meteorológicas se agruparon en una malla de 0.05 grados. Este espaciamiento no representa la resolución nativa del producto descargado, que debe documentarse por fuente y variable [4]. La implementación incorpora ajustes por altitud y posición topográfica. Sus indicadores térmicos acumulan excesos sobre 25 °C y déficits bajo 5 °C o 4 °C, según la ventana; describen exposición térmica bajo esos umbrales, no conteos de heladas a 0 °C. Las características de noviembre–diciembre permanecen identificadas como información posterior al ciclo.

**Arquitectura.** E12 combina referencias de estado, municipio y régimen de reporte con estimaciones ponderadas por proximidad. El componente de linderos utiliza un kernel gaussiano con escala de 35 m; esta escala reduce progresivamente los pesos y no constituye un corte estricto. La arquitectura incorpora correcciones regionales Huber–Ridge y una rama residual de procesos gaussianos y CatBoost. CatBoost utiliza pérdida MAE en esa rama; no existe una pérdida Huber única compartida por todos los componentes. Las reglas de mezcla, contracción y recorte forman parte del algoritmo experimental.

**Validación.** Se aplicó validación estratificada de cinco pliegues sobre las 138 etiquetas, con 110 o 111 parcelas de entrenamiento y 28 o 27 de validación por pliegue. Adicionalmente, se evaluaron las particiones espaciales principal-5, balanceado-4 y rotado-45-5. Se realizaron 30 sorteos estratificados con proporción aproximada 70/30, equivalentes a 96 parcelas de entrenamiento y 42 de validación. Los sorteos reutilizan observaciones y no representan muestras de campañas independientes. Finalmente, se generaron predicciones para las 59 parcelas sin etiqueta, sin atribuirles métricas de prueba externa.

**Métricas e incertidumbre.** Se calcularon RMSE, MAE y R² globales y por estado sobre predicciones fuera de pliegue. Cada parcela recibió el mismo peso, independientemente de su superficie. El RMSE corresponde a la raíz del promedio de errores cuadrados y el MAE al promedio de errores absolutos. El R² compara la suma de errores cuadrados con la variación respecto a la media observada del conjunto evaluado; se calculó nuevamente para cada estado, sin promediar los valores regionales para obtener el resultado global.

Los intervalos se construyeron con cuantiles de errores absolutos y una mezcla de radios estatales y globales. Su cobertura se midió sobre los mismos residuos empleados en la calibración. Por ello, se reporta como cobertura de calibración y no como demostración de cobertura externa o garantía formal de split-conformal. Una construcción conformal validada requiere especificar sus supuestos, procedimiento y evaluación independiente [1].

**Limitaciones del procedimiento.** Algunas características se imputaron mediante medianas del conjunto completo antes de aplicar los pliegues. También existen referencias espaciales construidas con covariables de parcelas que posteriormente se evalúan. Estas decisiones deben declararse y contrastarse con una ejecución que ajuste el preprocesamiento exclusivamente en cada entrenamiento [2]. Se exploraron múltiples variantes y reglas regionales sin acreditar una evaluación externa que abarque toda su selección [3]. Los resultados actuales se consideran evidencia interna exploratoria. La trazabilidad disponible permite recalcular métricas archivadas, pero no sustituye la validación independiente de etiquetas, extracción satelital y comportamiento futuro.

## 5. Resultados y discusión

**Desempeño global.** E12 obtuvo RMSE de 0.4812 t/ha, MAE de 0.3399 t/ha y R² de 0.6781 en validación estratificada. Estas métricas se reprodujeron a partir de las 138 predicciones fuera de pliegue. Frente a R08, el RMSE disminuyó 0.0244 t/ha, equivalente a 4.83%, y el R² aumentó 0.0335. La mejora es favorable dentro del procedimiento evaluado, pero no acredita por sí sola generalización a campañas futuras [5].

| Modelo | RMSE, t/ha | MAE, t/ha | R² | RMSE principal-5, t/ha |
|---|---:|---:|---:|---:|
| B0 | 0.6053 | 0.4415 | 0.4906 | 0.7440 |
| R08 | 0.5056 | 0.3547 | 0.6446 | 0.6596 |
| E09 | 0.4880 | 0.3364 | 0.6690 | 0.5128 |
| E10 | 0.4852 | 0.3381 | 0.6726 | 0.5109 |
| E12 | 0.4812 | 0.3399 | 0.6781 | 0.5104 |

La evolución no mejora simultáneamente todos los indicadores. E09 presenta menor MAE que E12, aunque su RMSE es mayor. Por tanto, la selección depende de la importancia atribuida a errores grandes, error absoluto medio y comportamiento regional. La complejidad adicional debe valorarse frente al tamaño de la mejora y al uso previsto.

**Heterogeneidad territorial.** Los resultados de E12 varían considerablemente entre estados. En Hidalgo se observó R² de 0.8114; en Puebla, 0.0192; y en Tlaxcala, −0.0630. El desempeño global combina diferencias territoriales y variación entre parcelas, por lo que no debe interpretarse como una capacidad explicativa uniforme.

| Estado | Parcelas | RMSE, t/ha | R² estratificado | R² principal-5 |
|---|---:|---:|---:|---:|
| Puebla | 71 | 0.5747 | 0.0192 | −0.0441 |
| Hidalgo | 36 | 0.3330 | 0.8114 | 0.6870 |
| Tlaxcala | 31 | 0.3814 | −0.0630 | −0.0293 |

En Tlaxcala, E12 superó el error de B0: RMSE de 0.3814 frente a 0.3747 t/ha. Un R² negativo indica mayor error cuadrático que la referencia descriptiva basada en la media del subconjunto evaluado. Puebla presenta rendimientos observados entre 2.15 y 5.59 t/ha; su escasa capacidad explicativa interna exige cautela al interpretar predicciones individuales.

**Sensibilidad espacial y a las particiones.** En principal-5, E12 obtuvo RMSE de 0.5104 t/ha y R² de 0.6378, frente a RMSE de 0.6596 del control R08. En balanceado-4 y rotado-45-5, el RMSE fue 0.5112 y 0.5503 t/ha, respectivamente. El esquema rotado produjo R² de −1.6722 en Tlaxcala. Estos contrastes muestran sensibilidad a la partición y limitan cualquier afirmación de robustez territorial generalizada.

Los 30 sorteos registraron RMSE medio de 0.4741 t/ha, desviación estándar de 0.0597 y R² medio de 0.6728. Describen variación bajo remuestreo de las mismas etiquetas; no constituyen validación temporal ni 30 pruebas independientes de generalización. La selección entre múltiples configuraciones y el preprocesamiento global pueden influir en la estimación del desempeño.

**Intervalos e interpretación agronómica.** Los intervalos cubrieron 129 de 138 observaciones, equivalentes a 93.48%, con ancho medio de 1.5584 t/ha. La cobertura de calibración fue 97.22% en Hidalgo, 88.73% en Puebla y 100% en Tlaxcala. Como los radios se ajustaron y evaluaron sobre los mismos residuos, estas cifras no demuestran cobertura externa ni una garantía regional del 90% [1].

Las asociaciones entre rendimiento, vigor, temperatura y descriptores intraparcelarios son exploratorias. Pueden orientar hipótesis, pero no permiten atribuir causalmente pérdidas a heladas, humedad o manejo. Por ejemplo, la correlación negativa entre temperatura mínima y rendimiento en Hidalgo no demuestra directamente daño por heladas. Tampoco se estimó un límite irreducible que permita afirmar que nuevas mejoras algorítmicas serían inútiles.

**Escenario económico.** Con supuestos ilustrativos de 5,800 MXN/t, costo de 13,500 MXN/ha y rendimiento de 3 t/ha, el margen sería 3,900 MXN/ha. Un error de 0.34 t/ha equivale a 1,972 MXN/ha, aproximadamente 50.6% de ese margen. Su relevancia no puede calificarse como absorbible sin evaluar deuda, liquidez, calidad y decisiones concretas. Además, el MAE no acota cada error individual. La disponibilidad de datos posteriores al ciclo y la falta de prueba externa restringen la aplicación inmediata de estos resultados.

## 6. Uso de la ciencia de datos en la inclusión financiera del sector agro

La ciencia de datos puede contribuir a la inclusión financiera al organizar información productiva verificable y hacer explícita la incertidumbre. En este proyecto, las estimaciones parcelarias ofrecen una base experimental para estudiar esa contribución; todavía no se ha demostrado un efecto sobre acceso al crédito, incumplimiento o indemnizaciones.

En crédito agrícola, una aplicación futura podría complementar la evaluación mediante escenarios de producción e ingreso. Para ello sería necesario contar con predicciones disponibles antes de la decisión, precios y costos documentados, obligaciones financieras y sensibilidad ante pérdidas. El rendimiento estimado no equivale a capacidad de pago y no debería utilizarse como único criterio de aprobación o rechazo.

En seguros, la información satelital podría apoyar seguimiento y priorización de verificaciones. Un intervalo de rendimiento no define automáticamente una indemnización ni elimina el riesgo de que el pago difiera de la pérdida real. Cualquier regla propuesta tendría que contrastarse con siniestros observados y evaluar errores, cobertura y diferencias entre regiones.

En el abasto agroindustrial, las estimaciones podrían complementar escenarios de disponibilidad y necesidades de seguimiento. La utilidad dependería de su anticipación efectiva, la calidad del grano y el costo de decisiones equivocadas, además del error predictivo promedio.

Una implementación responsable requeriría explicar los límites al productor, proteger sus datos, permitir revisión de decisiones y supervisar el desempeño por territorio. El siguiente paso sería un piloto prospectivo con criterios de evaluación definidos previamente. Su objetivo consistiría en medir si la información mejora decisiones y condiciones de acceso, sin trasladar incertidumbre no cuantificada a los agricultores.

## 7. Conclusiones

El estudio desarrolló y evaluó una arquitectura experimental para estimar retrospectivamente el rendimiento parcelario de cebada en Puebla, Hidalgo y Tlaxcala. La integración de información territorial, satelital y meteorológica produjo mejoras globales frente a los controles considerados. Sobre 138 parcelas etiquetadas, E12 alcanzó RMSE de 0.4812 t/ha, MAE de 0.3399 t/ha y R² de 0.6781 en validación estratificada. La reducción de RMSE respecto a R08 fue de 4.83%.

Estos resultados deben interpretarse junto con su heterogeneidad. Hidalgo presentó el mayor R² regional, mientras Puebla mostró capacidad explicativa limitada y Tlaxcala obtuvo resultados inferiores a la media estatal de referencia en RMSE. Las particiones espaciales incrementaron el error y revelaron sensibilidad territorial. Por ello, el desempeño global no sustenta una aplicación uniforme ni acredita transferencia a regiones o campañas no observadas.

Los intervalos alcanzaron cobertura de calibración de 93.48%, con diferencias entre estados. Dado que su evaluación reutiliza los residuos empleados para ajustar los radios, la cobertura externa y la garantía formal permanecen pendientes. Asimismo, el uso de información de noviembre–diciembre sitúa la evaluación en un escenario retrospectivo. No se ha establecido todavía la precisión que ofrecería el sistema antes de la cosecha o al tomar una decisión crediticia.

Las prioridades de desarrollo son fijar fechas de emisión, ajustar el preprocesamiento dentro de cada entrenamiento, separar selección y evaluación, y comprobar resultados con etiquetas independientes. También se requiere documentar mejor la medición del rendimiento y validar las interpretaciones agronómicas con observaciones de campo. Estas acciones permitirían distinguir cuánto error procede de la información disponible, la medición, el diseño de evaluación o la arquitectura.

La contribución actual consiste en una base experimental trazable y en la identificación de condiciones necesarias para avanzar hacia aplicaciones operativas. No se ha demostrado proximidad a un límite irreducible ni eficacia crediticia o aseguradora. Un piloto prospectivo, acompañado de evaluación regional y análisis del costo de errores, permitiría determinar si las mejoras estadísticas se traducen en beneficios concretos para productores y participantes de la cadena agroindustrial.

## Bibliografía

1. Angelopoulos, A. N. y Bates, S. (2022). *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*. arXiv:2107.07511, v6. [Texto completo](https://arxiv.org/html/2107.07511v6).
2. Scikit-learn developers. (s. f.). *Common pitfalls and recommended practices*. Documentación oficial. Consulta: 19 de octubre de 2026. [Documento](https://scikit-learn.org/stable/common_pitfalls.html).
3. Scikit-learn developers. (s. f.). *Nested versus non-nested cross-validation*. Documentación oficial. Consulta: 19 de octubre de 2026. [Documento](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).
4. Open-Meteo. (s. f.). *Historical Weather API*. Documentación de productos, resoluciones y variables. Consulta: 19 de octubre de 2026. [Documento](https://open-meteo.com/en/docs/historical-weather-api).
5. Proyecto AgroCebada. (2026). *Resultados y código de la fase fisiologia-siniestros-20261018; verificación de métricas del 19 de octubre de 2026*. Material interno del proyecto: [fase experimental](../../experiments/fisiologia-siniestros-20261018/), [contrato de datos](../../docs/data-validation.md) y [recálculo](Reverificacion_calculos_AgroCebada_20261019.json).

## Anexos: distribución sugerida para un máximo de dos cuartillas

**Cuartilla 1: resultados complementarios.** Incluir una tabla compacta con RMSE, MAE y R² de E12 en los cuatro esquemas y tres estados; una segunda tabla con tamaños regionales, cobertura de calibración y ancho de intervalo. Mantener en resultados principales las limitaciones que cambian la interpretación. No trasladarlas exclusivamente al anexo.

**Cuartilla 2: trazabilidad y arquitectura.** Incluir un diagrama legible de las ramas de E12 y una tabla breve de familias de variables, ventana temporal, fuente y disponibilidad antes o después de cosecha. Añadir versión del código y enlace o identificador de los archivos de evidencia. Conservar listas extensas de variables, predicciones y parámetros en el material digital complementario.

Esta distribución es una propuesta de contenido, no una certificación de extensión: el cumplimiento de dos cuartillas debe verificarse después de aplicar tipografía, márgenes e interlineado de la convocatoria. Antes de entregar, completar la identificación pública o institucional del conjunto del reto y la procedencia de etiquetas; no inventar una referencia bibliográfica para datos sin identificación disponible.
