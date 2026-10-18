# Evidencia y cobertura prioritaria

Los estados y métricas proceden de ejecuciones registradas y verificadas; un fallo u omisión no cuenta como prueba completada.

Las 138 etiquetas siguen siendo evidencia de desarrollo de una única campaña.

| Comparación | Estado | Ejecuciones verificadas | Evidencia | Hipótesis y control |
| --- | --- | --- | --- | --- |
| P00 | completed | 2/2 | L01, L08 | Reproducción de C-activa/C-soporte. |
| P01 | completed | 1/1 | L01, L08 | Ranking marginal frente a conjunto agronómico fijo y todas las columnas elegibles; control: la variante con ranking de este mismo bloque. |
| P02 | completed | 1/1 | L02, L08 | Eje térmico frente a calendario; control: resumen calendarizado del mismo bloque enriquecido, con los mismos datos NASA y covariables. |
| P03 | completed | 1/1 | L04, L05, L08 | Compartir efectos estatales con regularización; control: variantes sin efecto estatal del mismo bloque, además de media regional. |
| P04 | completed | 1/1 | L03, L05, L08 | Efectos suaves/aditivos y pocas interacciones frente al control congelado. |
| P05 | completed | 1/1 | L03, L08 | Forma de las curvas frente a sus resúmenes; control: resúmenes calendarizados con idénticas covariables y calidad. |
| P06 | completed | 1/1 | L01, L03, L04, L05, L08 | Combinado predeclarado de selección compacta, jerarquía y curvas; elegibilidad oficial únicamente. |
| P07 | completed | 2/2 | L06, L08 | TabICLv2 frente a C-soporte y TabPFN 2.5 histórico. |
| P08 | completed | 2/2 | L07, L08 | TabPFN-3 frente a los mismos controles. |

Las métricas completas, decisiones y motivos están en priority-results.md y coverage-final.json. Los contrastes de mecanismos permanecen descriptivos.

## Fuentes

- L01: [Código del selector](<C:/Users/leonf/OneDrive/Documentos/Hack Cebada 2026/src/agrocebada/modeling.py>), [historial de la fase](<C:/Users/leonf/OneDrive/Documentos/Hack Cebada 2026/experiments/soporte-regional-20261003/docs/phase-results.md>). Archivos locales leídos: filtro marginal, resultados negativos y protección regional fallida. No demuestra que el filtro sea la causa del error.
- L02: Franch et al., 2026, [The yield strikes back](https://doi.org/10.1016/j.jag.2026.105140). Resumen y fragmentos indexados del PDF institucional sobre trigo/cebada, tiempo térmico y fusión óptica–SAR. No se recuperó íntegramente el texto; no se copian sus parámetros ni ganancias.
- L03: Zou y Okhrin, 2026, [Stagewise crop yield prediction with multisource functional indices](https://onlinelibrary.wiley.com/doi/full/10.1002/cjs.70043). Texto consultado: GAM y modelos funcionales; también resultados negativos de representaciones excesivas y componentes ruidosos. Datos, objetivos y escalas difieren del reto.
- L04: [Tutorial de modelos multinivel de Stan](https://mc-stan.org/learn-stan/case-studies/tutorial_rstanarm.html). Documentación de interceptos/pendientes y pooling parcial. Es fundamento estadístico, no evidencia de rendimiento agrícola local.
- L05: [Documentación oficial de EBM](https://interpret.ml/docs/ebm.html), [GPML](https://gaussianprocess.org/gpml/chapters/). Modelos aditivos, interacciones y covarianzas. No fija una complejidad óptima para 138 etiquetas.
- L06: Qu et al., ICML 2026, [TabICLv2](https://proceedings.mlr.press/v306/qu26a.html), [implementación oficial](https://github.com/soda-inria/tabicl). Resumen del paper y documentación: soporte de regresión y benchmark tabular; pesos concretos aún no verificados localmente.
- L07: Prior Labs, mayo 2026, [TabPFN-3: Technical Report](https://arxiv.org/abs/2605.13986), [implementación oficial](https://github.com/PriorLabs/TabPFN). Informe/resumen y documentación. Su benchmark no valida estas parcelas y no sustituye TabPFN 2.5 retroactivamente.
- L08: [Cawley y Talbot, 2010](https://www.jmlr.org/papers/v11/cawley10a.html), [Roberts et al., 2017](https://doi.org/10.1111/ecog.02881). Selección repetida y validación con estructura espacial. No aporta un umbral universal de mejora o distancia.

La lectura bibliográfica se registró antes de la preparación. Los checkpoints y dependencias fundacionales se verificaron después en optional/*/preflight.json; sus hashes y pruebas están incluidos en la versión congelada.

## Alternativas diferidas

- BART, TabM y NGBoost: Prioridad secundaria; no ampliar familias sobre las mismas 138 etiquetas. No evaluada en esta fase.
- Radar e imágenes originales nuevas: Nueva adquisición y procesamiento fuera de esta fase. No evaluada en esta fase.
- ERA5, SoilGrids y AlphaEarth: Proveedores nuevos fuera del alcance aprobado. No evaluada en esta fase.
- Simulación completa de cultivo: No se observan fechas de siembra ni parámetros de cultivo suficientes. No evaluada en esta fase.
- Pendientes estatales, kernels anisotrópicos y muchas interacciones: Complejidad excesiva con tres estados y 138 etiquetas. No evaluada en esta fase.
