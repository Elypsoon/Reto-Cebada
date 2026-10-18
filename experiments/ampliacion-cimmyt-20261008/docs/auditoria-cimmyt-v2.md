# Auditoría CIMMYT: protocolo espacial revisado

Actualización del 9 de octubre de 2026. Los antecedentes del 8 de octubre se conservan en `registry/history/` y `docs/auditoria-cimmyt.md`.

| Etapa | Registros |
| --- | ---: |
| Cebada descargada V6 (todos los productos) | 1.396 |
| Rendimientos únicos de grano antes de filtros | 1.130 |
| Candidatos después de filtros agronómicos | 48 |
| Candidatos locales incluidos en los 48 | 29 |
| Población mexicana con celda única y clima completo bajo política principal | 45 |

La admisión por ajuste externo conserva 42–43 rendimientos mexicanos; los ajustes internos conservan 40–43. Se mantienen los mínimos de 30 etiquetas, diez grupos y dos campañas. La cohorte local y A04 siguen no viables.

La revisión permite puntos aproximados con WGS84 asumido, caja ±0,01° y buffer de 2.000 m. El origen de la referencia, semántica del punto y precisión permanecen desconocidos. No se reconstruyen polígonos reales ni se certifica independencia espacial.

La distancia usa un límite inferior: separación entre cajas cartesianas ECEF que contienen toda la caja auxiliar y la envolvente oficial, menor o igual a la cuerda y a la distancia superficial. Puede excluir de más; evita usar distancias angulares o medir únicamente el centro.

La sensibilidad de admisión es **detected**: 133 poblaciones cambian entre las políticas estrecha, principal y amplia. Las alternativas no consultan clima ni entrenan modelos. No es una comprobación de sensibilidad predictiva.

Se verificaron 13 pares celda/año históricos y se reutilizaron las cuatro respuestas originales 2025 sin cambiarlas. Las 197 filas oficiales y 45 auxiliares tienen las mismas 14 características, completas.

Modalidad y humedad oficial desconocidas; método externo de medición heterogéneo sin identificación por fila. El área auxiliar procede del tratamiento registrado en ha y el área oficial de los polígonos verificados.

Estado final del 9 de octubre de 2026: auditoría de admisión y procedimientos A01–A03 completados y recuperados. La ampliación no mostró aporte estable ni competitividad frente a la versión activa. A03 conserva fracciones 25%/50% inviables y 100% reutilizado; A04 sigue sin entrenamiento por soporte local insuficiente. Consultar [resultados y limitaciones](conclusions.md) y [cobertura](../registry/coverage-v2.json). No se activó ningún modelo.

Fuentes: [catálogo CIMMYT](https://hdl.handle.net/11529/10548986), [descriptor](https://www.nature.com/articles/s41597-025-06143-w), [código de autores](https://github.com/gmonpr/Historical-Agronomic-Dataset/tree/bcc359c2323284def49521dbb5d4fe8538350ae2), [e-Agrology](https://www.cimmyt.org/es/noticias/e-agrology-una-herramienta-que-cruza-fronteras/), [NASA POWER](https://power.larc.nasa.gov/docs/methodology/data/sources/).

Los datos y contextos se conservan localmente bajo los términos de CIMMYT; no se redistribuyen los originales.
