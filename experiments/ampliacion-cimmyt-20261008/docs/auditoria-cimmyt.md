# Auditoría de etiquetas CIMMYT: resultado parcial verificable

Se descargaron y verificaron los tres originales de CIMMYT V6. Hay 48 etiquetas candidatas que superan los filtros no espaciales aprobados; todavía no están admitidas para entrenar. Solo 29 pertenecen a Puebla/Hidalgo/Tlaxcala, por debajo del mínimo de 30 exigido antes de cada ajuste. No se ha medido una mejora de exactitud con estos datos.

| Etapa | Filas restantes |
| --- | ---: |
| Rendimientos de todos los cultivos en el segundo archivo | 80.555 |
| Filas con cultivo BARLEY, incluyendo productos distintos | 1.396 |
| Grano de cebada | 1.131 |
| Identificadores únicos de rendimiento de grano | 1.130 |
| Unidad y rendimiento verificables | 1.119 |
| Área de tratamiento válida | 1.114 |
| Verano y temporal | 441 |
| Siembra dentro de abril–octubre del año indicado | 428 |
| Inicio de cosecha dentro de esa ventana | 53 |
| Fin de cosecha dentro de esa ventana y fechas ordenadas | 48 |

La cifra de 968 del artículo es evidencia publicada, no el tamaño del archivo V6 efectivamente auditado. La diferencia permanece registrada sin atribuirla a un error del proveedor ni presentar las 1.396 filas como parcelas nuevas independientes.

| Cohorte candidata, antes de admisión espacial | Etiquetas | Parcelas | Productores identificados | Campañas | Grupos de dependencia |
| --- | ---: | ---: | ---: | ---: | ---: |
| Puebla/Hidalgo/Tlaxcala | 29 | 21 | 19 | 4 | 19 |
| México | 48 | 40 | 30 | 8 | 29 |

La cohorte nacional comprende Hidalgo (24), Estado de México (19), Puebla (4) y Tlaxcala (1). Un componente de dependencia puede enlazar productores distintos mediante una misma parcela; por eso grupos y productores no son necesariamente el mismo conteo.

El primer archivo tiene 69.008 filas y dos columnas LOGBOOK ID iguales. La bitácora sola no es clave única: 10.305 bitácoras tienen dos filas de tratamiento. La unión verificada usa bitácora + identificador de práctica/tratamiento, es muchos-a-uno y conserva exactamente las 1.396 filas originales de cebada, sin faltantes en el cruce. Se conservan claves mixtas numéricas/UUID como texto, con los XLSX originales intactos.

Las conversiones admiten TON/ha y KG/ha. Los ceros legítimos se conservan; no se rellenan fechas ni se corrigen rendimientos mediante residuos del modelo. Cuando no hay prueba de producción incremental, no se suman ni promedian varias cosechas/tratamientos de una parcela y campaña. El área usada se identifica como área sembrada del tratamiento; no se infiere desde coordenadas ni se confunde con el área total declarada por el productor.

## Diferencia espacial que impide continuar con el diseño vigente

El diseño aprobado pide envolventes de todos los vértices de polígonos anonimizados, una incertidumbre verificable y exclusión a 1.000 m frente a las parcelas de validación. Los originales descargados contienen LATITUDE N y LONGITUDE W, sin vértices de parcela. El bloque geoespacial del catálogo solo declara México; no declara datum o sistema de referencia. El artículo describe truncamiento de vértices a tres decimales, pero eso no establece por sí solo cómo interpretar los puntos de estos archivos.

Asignar silenciosamente WGS84 a los puntos y tratarlos como esas envolventes no implementaría el control aprobado. La admisión espacial está pendiente, no es una demostración de inexistencia de datos ni un experimento predictivo negativo.

Se requieren una de estas dos rutas, todavía sin ejecutar:

1. Mantener el protocolo: obtener documentación verificable del sistema de referencia, significado y precisión de los puntos, y los polígonos necesarios para las envolventes previstas. No se ha contactado al proveedor.
2. Revisar el protocolo para un diagnóstico basado en puntos aproximados: declarar explícitamente la referencia geográfica asumida, sustituir el contrato de envolventes de polígonos por uno de incertidumbre puntual y predefinir sensibilidades espaciales antes de entrenar. Esa revisión debe conservar etiquetas/filtros/mínimos y los tres esquemas; no declarará comprobadas las ubicaciones. Tendrá su propia versión y distinguirá separación por puntos aproximados de separación por límites parcelarios.

La segunda ruta es una propuesta de revisión, no una excepción aplicada. Ninguna de las dos permite aumentar el peso de la cohorte local ni reducir su mínimo para hacer viable A04.

## Trabajo implementado y comprobaciones

- Fase aislada con 174 copias verificadas y manifiesto inicial de 2.596 archivos protegidos.
- Población oficial intacta: 197 identificadores, 138 etiquetas, 59 consultas sin etiqueta; particiones principales conservadas por hash.
- Control A00 recuperado en proceso nuevo sin red: 59 predicciones y métricas de 138 OOF por esquema, tolerancia absoluta 1e−10.
- Adquisición pública, hashes del proveedor y SHA256 locales, diccionario real, claves y embudo recuperables.
- Ridge ponderado con preprocesamiento dentro del ajuste, masa auxiliar limitada y pesos iguales por grupo de dependencia.
- 20 pruebas aprobadas: cardinalidad, duplicados/conflictos, productos, unidades, fechas, ceros, grupos, pesos, función objetivo y contrato de características.

A01–A03 no se han ejecutado. A04 queda no viable bajo el protocolo actual: 29 candidatas locales son un límite superior menor que 30 antes de los controles espaciales. No se le asignan resultados del TabPFN-3 de la fase anterior. No se modificó, activó, desplegó ni envió un modelo.

Los originales y derivados con datos se conservan únicamente para uso local autorizado. No redistribuirlos; dirigir a terceros al repositorio de origen. Los manifiestos, `registry/label-audit.json`, `registry/column-map.json` y las filas de auditoría locales permiten recalcular los conteos y los motivos por observación.

## Fuentes y software

- Gardeazábal-Monsalve, A.; Ramirez Ortega, M. L.; Pacheco Rodríguez, G. M.; Garza Sánchez, E. (2024). [Historical Agronomic Dataset - Insights from Mexico (2012 - 2022)](https://hdl.handle.net/11529/10548986). CIMMYT Research Data & Software Repository Network, V6. Consulta y adquisición: 8 de octubre de 2026.
- [Descriptor científico de la fuente](https://www.nature.com/articles/s41597-025-06143-w), utilizado para interpretar procedencia y limitaciones, sin asumir que sus conteos son los de la cohorte admitida.
- [Código de uniones de los autores](https://github.com/gmonpr/Historical-Agronomic-Dataset/blob/main/Dataset_joins.R), como antecedente de la clave de prácticas; el archivo V6 se verificó directamente.
- Python 3.12.14; pandas 3.0.6; NumPy 2.5.3; scikit-learn 1.9.1; GeoPandas 1.2.0; pyproj 3.8.0; openpyxl 3.1.5; et-xmlfile 2.0.0. El lector Excel está aislado en `vendor`; no se modificaron los entornos históricos.
- Kassis, T., Agarwal, V., He, Y., Patel, D., y Brueckner, A. M. (2026). [Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://doi.org/10.48550/arXiv.2609.00065). Referencia de las guías procedimentales scikit-learn y GeoPandas utilizadas; metadatos contrastados el 8 de octubre de 2026.
