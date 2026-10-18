# Resultado de la ampliación de entrenamiento con CIMMYT

Estudio diagnóstico sobre las mismas 138 etiquetas oficiales de 2025. Las 59 consultas ocultas siguen sin etiquetas.

Aporte estable de etiquetas bajo el supuesto de puntos: **no**.
Competitividad frente a la versión activa: **no**.

| Esquema | RMSE A00 activa | RMSE A01 común | RMSE A02 procedimiento ampliado | RMSE media regional | Ajustes A02 con donantes |
| --- | ---: | ---: | ---: | ---: | ---: |
| principal-5 | 0.764573 | 0.807573 | 0.829548 | 0.743976 | 1/5 |
| balanceado-4 | 0.808494 | 0.808509 | 0.828063 | 0.744156 | 2/4 |
| rotado-45-5 | 0.761048 | 0.762833 | 0.762833 | 0.911941 | 0/5 |

RMSE en t/ha. A01 y A02 comparten columnas, algoritmo y selección interna. A02 conserva respaldos oficiales cuando no se admite ampliación; las predicciones de respaldo no se atribuyen a donantes.

Disponibilidad: 48 candidatos agronómicos; 45 registros con celda única y clima completo, 37 parcelas, 28 productores conocidos, 8 campañas, 27 grupos y 5 celdas meteorológicas. Por ajuste principal quedan 40–43 candidatos mexicanos. No sumar los tres esquemas como 414 etiquetas independientes.

Los 29 candidatos locales no superan el mínimo de 30; A04 permanece no viable y no recibió métricas del experimento TabPFN anterior.

Procedimiento A03: **completado y recuperado**. En los tres ajustes externos con auxiliares, las fracciones 25% y 50% no alcanzaron el mínimo de soporte; el 100% reprodujo A02. Los otros once ajustes no requieren curva porque A02 eligió el respaldo oficial. No se obtuvo una curva completa que permita atribuir mejora a aumentar el tamaño. Los soportes y estados por ajuste se conservan en `runs/A03/artifacts/curve-status.json`; no se elige retrospectivamente el tamaño más favorable.

Sensibilidad geográfica de admisión: **detectada**, con cambios en 133 comparaciones de población entre márgenes examinados. WGS84 es un supuesto; datum de origen, semántica del punto y precisión efectiva no están verificados. La política principal usa ±0,01° y 2.000 m. La separación ECEF es un límite inferior conservador, no la distancia exacta ni una garantía de separación parcelaria.

Las diferencias pareadas por parcela se conservan en los tres CSV de `docs/paired-*`. Las métricas RMSE, MAE, R², sesgo, estado, fold y tercil de área, y las decisiones internas completas se conservan por ejecución. `conclusions.json` contiene cada comprobación de los umbrales congelados, sin significación estadística inferida de errores correlacionados.

Recuperación: cada comparación completada reprodujo modelos, pesos, contextos, contratos, predicciones y métricas en otro proceso sin red, con tolerancia absoluta 1e−10 y relativa 0. El protocolo y sus entradas quedaron congelados antes del primer ajuste real.

Las métricas describen evidencia de desarrollo, no validación independiente en otra campaña. El sesgo de asistencia técnica, cambio temporal, medición externa heterogénea y modalidad/humedad oficial desconocidas limitan la transferencia. No se activó, desplegó ni envió ningún modelo; E08/P06 conserva sus decisiones.

Más registros compatibles pueden seguir siendo útiles, pero esta fase no prueba otras fuentes ni todas las combinaciones posibles. Cualquier ampliación de proveedores, ventanas, modelos o criterios requiere otro protocolo previo a sus resultados.

Referencias y software:

- [CIMMYT, Historical Agronomic Dataset, V6](https://hdl.handle.net/11529/10548986). Originales y contextos locales bajo sus condiciones de uso; no redistribuidos.
- [Descriptor del dataset](https://www.nature.com/articles/s41597-025-06143-w) y [revisión del código de autores](https://github.com/gmonpr/Historical-Agronomic-Dataset/tree/bcc359c2323284def49521dbb5d4fe8538350ae2).
- [NASA POWER: fuentes](https://power.larc.nasa.gov/docs/methodology/data/sources/) y [API diaria](https://power.larc.nasa.gov/docs/services/api/temporal/daily/).
- Kassis, T., Agarwal, V., He, Y., Patel, D. y Brueckner, A. M. (2026). [Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://doi.org/10.48550/arXiv.2609.00065). Versión actual verificada el 9 de octubre de 2026; guías GeoPandas/scikit-learn empleadas en el procedimiento.

Verificación final: 29/29 tareas, validación estricta OpenSpec satisfactoria y 52 pruebas aprobadas. Los manifiestos de las cinco ejecuciones y las 229 entradas congeladas coinciden; los 2.596 archivos protegidos siguen intactos. Máximo observado en los procesos reales: 229,63 MB, con un trabajador y dos hilos. La recuperación comprobó 129 predicciones de modelos/ajustes en A01, 471 en A02 y tres reutilizaciones en A03, además del control A00 histórico.
