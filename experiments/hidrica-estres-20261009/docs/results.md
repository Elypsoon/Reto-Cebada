# Resultados de disponibilidad hídrica y estrés agroclimático

Estimación retrospectiva de abril–octubre de 2025. Las comparaciones reutilizan 138 etiquetas; las 59 consultas ocultas no tienen rendimiento conocido.

| Ejecución | Estado | RMSE principal | RMSE balanceado | RMSE rotado |
| --- | --- | ---: | ---: | ---: |
| W00 | completed | 0.764053 | 0.808494 | 0.776111 |
| W01-O | completed | 0.925988 | 0.926134 | 0.935749 |
| W01-E | completed | 0.925988 | 0.926134 | 0.934258 |
| W02 | not_viable | — | — | — |
| W03-M | not_viable | — | — | — |
| W03-I | not_viable | — | — | — |
| W04 | completed | 0.925988 | 0.926134 | 0.934620 |
| W05 | completed | 0.925988 | 0.926134 | 0.934258 |

RMSE en t/ha; menor es mejor. W00 muestra su ruta seleccionada; ambas rutas históricas se conservaron y recuperaron.

Elegibilidad W05: **no**. Activación, despliegue y envío permanecen en falso.

La cartografía de suelo G quedó no viable por integridad insuficiente del recorte/servicio; el intento y sus metadatos se conservan en la auditoría. Esto no prueba que el suelo carezca de utilidad predictiva.
El bloque S quedó excluido porque los originales no especifican fórmula/bandas del NDWI. Las funciones fueron probadas con datos sintéticos, sin atribuirles métricas de estrés vegetal observado.
Variedad, fecha de siembra y heladas locales permanecen desconocidas en los IDs oficiales. La radiación representa contexto regional y la nubosidad de captura representa soporte observacional.

La receta común cambia familias/selección respecto a la activa. Los pares W04–W01-E y W05–W01-E aíslan mejor el aporte nuevo que una comparación única con W00. Los CSV pareados conservan diferencias por parcela.

No hay intervalos nuevos para W05 ni validación de otra campaña. Repetir esquemas no crea 414 etiquetas independientes.

## Fuentes y software

- ISRIC SoilGrids: https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html y https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_02.html. Admisión local negativa documentada.
- NASA POWER: https://power.larc.nasa.gov/docs/methodology/. Datos locales verificados; VPD y radiación regionales.
- Habilidades Scientific Agent Skills de scikit-learn/GeoPandas, Kassis et al. (2026): https://doi.org/10.48550/arXiv.2609.00065. Versiones y fuentes comprobadas en preparación.
