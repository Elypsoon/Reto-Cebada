## Context

Ver `proposal.md` para motivación y alcance. Esta fase estima retrospectivamente rendimiento en t/ha entre 2025-04-01 y 2025-10-31; no es un pronóstico previo a cosecha. Mantiene 197 parcelas, 138 etiquetas oficiales y 59 consultas. Los tres esquemas espaciales ya utilizados son evidencia de desarrollo, no un test nuevo.

La inspección del proyecto muestra que `external.py` deriva VPD diario de Tmin/Tmax y punto de rocío, después guarda medias por ventana y radiación acumulada. La documentación local identifica tres celdas meteorológicas asignadas y dos series solares distintas. El modelo activo seleccionado usa VPD de junio–julio, pero no pendiente, NDWI ni radiación entre sus diez columnas finales; una tabla de entrada no acredita uso final. `CompactSelector` realiza selección marginal, por lo que copiar sus diez columnas finales como selección global para experimentos nuevos contaminaría la comparación. Las temperaturas oficiales son mensuales; las cuatro series NASA locales no tienen Tmin bajo cero en el periodo, sin que ello descarte heladas locales.

El diccionario entregado define NDWI genéricamente, sin fórmula ni bandas. La tabla parcelaria procesada no contiene variedad o siembra. SoilGrids no está adquirido ni admitido en la versión activa. Las fases anteriores conservan particiones, orquestación, contratos y recuperación; las comparaciones P06 y CIMMYT no activaron una versión nueva.

## Goals / Non-Goals

**Goals:**

- Separar una propiedad estática de almacenamiento del suelo, la exposición atmosférica y la señal espectral observada, con unidades y escalas recuperables.
- Comparar cambios de información con controles que compartan procesamiento, familias, particiones y calidad; identificar cuándo la ganancia depende de una fuente regional o de cobertura.
- Definir un combinado antes de observar errores y permitir resultados negativos o bloques no viables sin alterar criterios.

**Non-Goals:**

- Ajustar un índice fisiológico universal, confirmar daño por heladas o estimar humedad diaria real del suelo desde capacidad de retención.
- Incorporar metadatos encontrados después de congelar, ampliar familias por resultados desfavorables o reutilizar protocolos cerrados con archivos modificados.
- Añadir balance hídrico, nuevas imágenes, reanálisis o coeficientes de cultivo/raíces no observados. La lista completa de exclusiones está en la propuesta.

## Decisions

### 1. Fase aislada y procedencia verificable

La futura implementación creará `experiments/hidrica-estres-20261009/` con `src/`, `scripts/`, `tests/`, `data/`, `registry/`, `runs/` y `docs/`. Copiará únicamente entradas y módulos necesarios; registrará origen y SHA-256, dependencias y rutas. No copiará entornos completos, temporales ni resultados como ejecuciones nuevas. `workspace.json` y el aislamiento de importaciones impedirán escribir en destinos activos; cada control histórico se recuperará con su código y dependencias originales en un proceso propio.

Se importarán por ID las asignaciones `principal-5`, `balanceado-4` y `rotado-45-5` de la fase prioritaria, verificando sus hashes y versiones. No se regenerarán grupos para favorecer una hipótesis. Antes y después de la fase se comprobarán las entradas protegidas del modelo activo y fases anteriores.

Alternativa: editar `src/agrocebada` directamente. Se descarta porque cambiaría contratos activos y dificultaría separar antecedente de experimento.

### 2. Auditorías previas sin rendimiento

Preparación tendrá tres recibos: `spectral-audit.json`, `soil-admission.json` y `agronomic-metadata-audit.json`. Cada uno conservará fuentes, alcance de lectura, estado y motivo, incluyendo archivos/URLs no disponibles. La conversación es origen de hipótesis, no evidencia de mecanismos observados.

- NDWI: revisar originales y documentación identificable del proveedor. La interpretación vegetal solo se habilita con fórmula y bandas comprobadas pertinentes a humedad de vegetación, disponibilidad real por sensor y una orientación documentada del índice. Si falta, conservar las columnas oficiales con su nombre histórico en los controles, pero excluir el bloque S que depende de esa semántica. No renombrar NDWI como NDMI ni adquirir reflectancias para sustituirlo en esta fase.
- Suelo: verificar versión y capas oficiales de retención a 33 y 1500 kPa para 0–5, 5–15, 15–30 y 30–60 cm, con media y quantiles 0.05/0.95. Resolver los códigos de producto desde metadatos, no solo desde sus nombres. La auditoría incluirá significado del volumen de referencia, escala de almacenamiento, resolución, CRS, licencia, fechas y cobertura. Las capas a 10 kPa solo tendrán una sensibilidad descriptiva si se recuperan bajo el mismo límite; no competirán como recetas predictivas.
- Metadatos: inventariar únicamente evidencia accesible de variedad, siembra y temperaturas locales vinculable a ID/campaña. No contactar a personas ni utilizar recomendaciones regionales como asignaciones. Si aparece evidencia suficiente, documentar una evaluación futura separada; no ampliar W05.

La documentación ISRIC informa una API pausada: priorizar recortes de GeoTIFF/VRT mediante acceso oficial WebDAV/WCS que se compruebe operativo. Limitar adquisición a envolvente de parcelas más una celda nativa; máximo 2 GiB de transferencia almacenada y 30 minutos por intento completo de adquisición. Un exceso o acceso fallido cierra la inviabilidad con motivo; no descarga mapas globales ni cambia de proveedor. Se congelarán archivos locales recuperables antes del entrenamiento, sin red durante inferencia.

Alternativa: usar textura y una función de transferencia elegida después de fallar la descarga. Se difiere para evitar sustituir silenciosamente fuente y definición.

### 3. Capacidad estimada por estrato

Para cada celda y estrato j, convertir los enteros a fracción volumétrica siguiendo metadatos verificados. En capas almacenadas en milésimas de m³/m³, la conversión a fracción es dividir entre 1000; dividir entre 10 produce porcentaje, no fracción.

`AWC_j_mm = 1000 * (theta_33_j - theta_1500_j) * espesor_j_m`.

`AWC_0_30_mm` suma espesores 0.05, 0.10 y 0.15 m; `AWC_30_60_mm` usa 0.30 m. La definición a 33 kPa es una aproximación convencional cartográfica, no capacidad de campo medida en cada suelo. No sumarlas como almacenamiento radicular observado. Si el volumen de referencia no permite esta interpretación sin una corrección no verificada, excluir el bloque; no introducir un factor de fragmentos gruesos por suposición.

Validar `0 <= theta_1500 <= theta_33 <= 1` por celda y capa; valores incoherentes son faltantes diagnosticados, sin recorte artificial. Extraer por intersección de celdas y ponderación de área proyectada, respetando resolución y máscara común de todas las capas integrantes, sin crear detalle parcelario por remuestreo. Exigir al menos 95% de superficie válida común para el valor de cada parcela/estrato. El bloque G requiere al menos 90% de las 197 parcelas con ambos estratos válidos; el resto permanece en la población y con faltantes imputables exclusivamente desde train.

Las envolventes `theta33_Q05 - theta1500_Q95` y `theta33_Q95 - theta1500_Q05`, agregadas por espesor y superficie común, describirán sensibilidad. No son quantiles conjuntos ni un intervalo calibrado de AWC; conservar valores negativos de la envolvente inferior como incertidumbre, no como agua negativa. Quantiles y cobertura se reportan, no se añaden automáticamente como predictores.

Alternativa: humedad actual regional ERA5-Land. Responde a otra magnitud, exige adquisición distinta y queda fuera de este protocolo. La pendiente conserva su papel de covariable; no se convierte en un coeficiente fijo de retención ni se supone que todo terreno plano almacena más agua.

### 4. Señal principal, interacciones y coexposición

Calendario único: early abril–mayo, middle junio–julio, late agosto–octubre. Mantener temperatura mensual CHIRTS y VPD regional aproximado ya implementado; no simular extremos diarios desde CHIRTS. El VPD no es una medición de demanda en cada parcela.

El bloque S exige NDWI vegetal comprobado para Sentinel-2. Con captura a nube <=20%, obtener medianas por ventana y semanas fijas de siete días desde 2025-04-01, truncando la última en el corte. Asignar cada semana a una ventana por su fecha central y usar exactamente sus fechas para el promedio VPD; documentar los intervalos que cruzan mes. Una semana requiere al menos dos fechas distintas observadas para NDWI; no interpolar ni extrapolar. Guardar fechas originales, número de semanas utilizables y fracción de soporte. El resumen semanal de una ventana requiere al menos cuatro semanas válidas y 50% de sus semanas; si no cumple queda faltante, sin interpretar no observación como no estrés.

W03-M conserva efectos principales y añade por ventana las fracciones marginales de VPD semanal alto y NDWI semanal bajo, más soporte compartido. Umbral alto = quantile 0.75 del VPD semanal en train; bajo = quantile 0.25 del NDWI semanal en train. El sentido bajo = menor humedad requiere comprobar orientación del índice. Para NASA, computar quantiles sobre pares celda/semana únicos de train; para NDWI, ponderar para que cada parcela de train aporte peso total igual. Aprender estos parámetros nuevamente en cada inner/outer/final fit. Un umbral no aprendible excluye las columnas semanales que dependen de él en ese ajuste, sin usar toda la población para completarlo. Ambas fracciones marginales y la conjunta comparten el mismo denominador de semanas con ambas señales válidas.

W03-I añade a W03-M: seis productos `z(VPD_ventana)*z(NDWI_ventana)` y `z(Tmean_ventana)*z(NDWI_ventana)`, y tres proporciones conjuntas de semana con VPD alto y NDWI bajo sobre semanas con ambas señales válidas. Z usa media y desviación de train. No sumar magnitudes incompatibles; no incluir un término triple ni umbrales térmicos arbitrarios. S comprende efectos principales adicionales e interacciones, y es indivisible en W05. Su disponibilidad a nivel de fuente se resuelve antes de congelar; disponibilidad estadística por ajuste y columnas constantes se resuelven solo con train. No descartar el bloque al observar errores externos.

Los porcentajes semanales son coexposición estadística, sin confirmar cierre estomático ni semana exacta de pérdida productiva; solo existe rendimiento final por parcela. La falta de apoyo semanal puede dejar sus columnas fuera de train mientras sobreviven productos por ventana, con razón registrada.

Alternativa: un índice escalar `VPD + T - NDWI`, incluso normalizado con pesos iguales. Se descarta como receta principal porque impone pesos no validados, puede duplicar temperatura ya contenida en VPD y no mide fisiología.

### 5. Controles y catálogo previo a resultados

Usar una representación oficial `monthly_20_10` recuperada, preservando sus columnas y calidad; las variantes nuevas no reconstruyen picos ni etapas. Control enriquecido agrega las tres medias VPD y GDD NASA existentes, sin radiación. El bloque R contiene únicamente tres acumulados solares por ventana en MJ/m². No convertir nubes de captura en días nublados.

| ID | Información y objetivo | Control pareado |
| --- | --- | --- |
| W00 | Recuperar activa oficial y seleccionada con su procedimiento histórico original | Contratos y antecedentes propios |
| W01-O | Procedimiento común con tabla oficial | Referencias global/regional; W00 oficial |
| W01-E | Mismo procedimiento con VPD y GDD NASA, sin G/S/R | W01-O; W00 seleccionada |
| W02 | W01-E + G: dos estimaciones AWC | W01-E |
| W03-M | W01-E + efectos principales y soporte semanal de S | W01-E |
| W03-I | W03-M + productos y coexposición de S | W03-M |
| W04 | W01-E + R: tres acumulados solares | W01-E |
| W05 | Selección interna entre subconjuntos predeclarados de G/S/R | W01-E, regional y W00 seleccionada |

Cada variante común usa dos familias directas: Ridge con alpha {0.1,1,10} y GPR Matérn 2.5 con longitud {1,5}, ruido 0.15, sin optimización continua, objetivo normalizado y semilla 2026. Incluir referencias global/regional. Aprender imputación mediana, disponibilidad >=50%, eliminación de constantes, escalado y codificación de estado solo en train; no hacer ranking marginal ni selección con las diez columnas finales de la activa. Indicadores estatales desconocidos son cero; modelos directos registran transferencia y referencia regional usa media global aprendida. Seleccionar entre cinco modelos y dos referencias por variante: siete candidatos.

W05 define desde el inicio los ocho subconjuntos de tres bloques: ninguno, G, S, R, G+S, G+R, S+R, G+S+R. Tiene como máximo 8*5+2 = 42 candidatos únicos, incluidas las referencias una vez. Deduplicar bloques excluidos por las auditorías previas sin crear recetas nuevas. La tabla de catálogo conservará los subconjuntos originalmente previstos y su estado. No usar ensambles ni incorporar algoritmos de P07/P08. Los seis controles/diagnósticos comunes anteriores a W05 suman como máximo 6*7=42; catálogo común total <=84 candidatos por selección, sin contar repeticiones de CV ni el catálogo histórico intacto de W00. No afirmar 84 ajustes totales.

La selección interna parte del ganador W01-E y referencias; un candidato con bloques nuevos requiere RMSE >=2% menor que W01-E y que la mejor referencia interna, mejora en al menos dos folds frente a ambos y MAE estatal <=110% de ambos con >=10 etiquetas. La selección base W01-O/E admite complejidad únicamente con la misma puerta de 2%, dos folds y protección estatal frente a la mejor referencia interna. Usar desempate determinista: menor complejidad, luego ID, a tolerancia 1e-10. Si ninguno cumple, conservar W01-E o su referencia de respaldo según la misma selección base. Un bloque requiere al menos una columna nueva informativa en train; S en W03-I/W05 requiere al menos un producto o proporción conjunta informativa, no solo soporte. Un candidato no viable en un fold se excluye completo, sin promediar solo folds favorables. La selección de familias/configuraciones no utiliza errores externos de W02/W03/W04. Cada diagnóstico publica además el ganador de su variante y la decisión de mejora frente a su control, sin convertir un rechazo en una selección externa alternativa.

Alternativa: elegir los bloques con menor RMSE externo y combinarlos. Se descarta porque usaría etiquetas externas para diseñar W05.

### 6. Validación, elegibilidad y recursos

Cada ejecución viable produce 138 predicciones externas por esquema. Retirar un grupo existente por fold interno, recomputando transformaciones aprendidas. Mantener mínimos históricos de 15 casos de validación y 80 de entrenamiento externo; si un esquema resulta inviable, conservar el fallo y bloquear elegibilidad. Las 59 consultas no aportan etiquetas ni decisiones de selección.

W05 es el único procedimiento elegible y enriquecido de esta fase. Aplicar íntegramente `specs/yield-model/spec.md`: razones frente a regional <=0.98 en principal y >=2 esquemas, media <=0.98, máximo <=1.05; protección estatal <=1.10; principal <=0.98 frente a W00 seleccionada y máximo <=1.05 frente a ella; controles y recuperación verificados. Además, el ajuste final debe admitir al menos un bloque nuevo y superar la puerta interna frente a W01-E. Los resultados parciales o el respaldo puro no son promoción. La ruta oficial W01-O sigue recuperable; no redefine elegibilidad oficial E08/P06.

Reportar RMSE, MAE, R², sesgo firmado, errores por estado/fold/tercil, soporte de train, celdas compartidas, selección de bloques y columnas utilizadas. Comparar W02/W03/W04 con sus controles explícitos y W05 con W01-E y activa, separando ganancia de receta de ganancia de información. No inferir significación estadística de errores espaciales correlacionados. No incluir intervalos nuevos: los de la activa pertenecen a su calibración original y no se centran sobre W05.

Un proceso de entrenamiento por vez, dos hilos numéricos y límite agregado de 4 GiB RSS; máximo 120 minutos por bloque incluyendo sus tres esquemas y recuperación. Un límite produce interrupción registrada, sin subir automáticamente recursos ni reducir catálogo tras ver resultados. Preflight sintético y dependencias fijadas antes de congelar; adquisición es la única etapa con red. Recuperar cada ejecución completada en proceso nuevo sin red, con tolerancia absoluta 1e-10 y rtol=0, modelos/contexto, contratos, predicciones y métricas. Exportar float64 con 17 dígitos cuando corresponda.

### 7. Entregables y pruebas

Los recibos previos, `frozen-protocol.json`, catálogo efectivo, hashes de esquemas y dependencias constituirán la fuente de ejecución. Cada `runs/<id>/` guardará configuración, eventos, OOF de tres esquemas, decisiones internas, modelo final, contratos y paquete de recuperación. `docs/` contendrá auditoría de fuentes, resultados incrementales, comparación pareada y conclusiones con límites reales.

Pruebas necesarias: unidades y espesores AWC; NoData/máscara común/cobertura parcial; incoherencia física; envolventes sin cobertura probabilística inventada; fecha de corte; semanas sin observación; umbrales y escalas invariantes ante etiquetas externas alteradas; celdas meteorológicas duplicadas; columnas no aprendibles; presupuesto <=84/42; combinación congelada independiente de ganadores externos; conservación de las 197 filas; predicciones finitas/59 IDs; hashes alterados; recuperación individual/lote sin red. Pruebas sintéticas de definición faltante deben demostrar exclusión S; de suelo inaccesible, exclusión G con continuidad de R y controles. No modificar pruebas congeladas de fases anteriores para aceptar un resultado nuevo.

## Risks / Trade-offs

- Cartografía gruesa o suelo correlacionado con región -> conservar escala, celdas y validación espacial; no atribuir causalidad parcelaria.
- NDWI ambiguo o escaso soporte semanal -> puerta semántica previa, faltantes y exclusión registrada; no fabricar una curva ni buscar un índice sustituto al ver errores.
- Suelo publicado después de 2025 -> declarar uso retrospectivo y fecha; no simular disponibilidad histórica de un pronóstico.
- Diferencias de retención y quantiles sin distribución conjunta -> diagnóstico físico y envolventes descriptivas, sin un intervalo de AWC falsamente calibrado.
- VPD, temperatura y radiación correlacionados -> efectos principales conservados, interacciones escasas y regularización; no ampliar parámetros por errores desfavorables.
- Reutilización de 138 etiquetas y tres esquemas observados -> congelar hipótesis y tratar toda mejora como desarrollo; la confirmación requiere campaña/etiquetas independientes o evaluación oficial.
- Ausencia de fuentes esenciales -> registrar cobertura de investigación incompleta aunque terminen los controles; no afirmar que se evaluó suelo o estrés vegetal cuando sus bloques fueron no viables.

## Migration Plan

La fase crea artefactos nuevos aislados, sin migrar datos activos ni cambiar la aplicación. Preparar y verificar fuentes; ejecutar preflight; congelar protocolo; recuperar controles; ejecutar variantes secuencialmente; verificar paquetes y reportar elegibilidad. Un control que no reproduzca su antecedente bloquea comparaciones predictivas hasta resolver identidad, sin cambiar hashes históricos.

Activación, despliegue y envío quedan en falso incluso si W05 resulta elegible. Una decisión posterior tendría que seleccionar un paquete íntegro y un plan de integración propio. Recuperación/retroceso de la fase consiste en utilizar sus paquetes o la activa conservada, sin sobrescribir versiones anteriores.

## Open Questions

- ¿Qué documento verificable del proveedor especifica las bandas y fórmula del NDWI entregado? Su ausencia ya tiene una rama definida: excluir S.
- ¿Qué versión y vía oficial permite recuperar las capas de retención y quantiles dentro del presupuesto? Su ausencia excluye G, sin ampliar fuentes.
- ¿Existen registros por ID de variedad, siembra o temperatura local? La auditoría determinará su disponibilidad para una propuesta futura; no cambia este catálogo.

Estas preguntas son verificaciones de datos con resultados previstos, no decisiones pendientes sobre alcance o criterios.

## References

- Estado local: `src/agrocebada/{features,external,modeling,inference}.py`, `docs/{features,external-data}.md`, contrato/modelo seleccionado, diccionario original y `experiments/prioridades-predictivas-20261006/{registry/scheme-validation.json,src/agrocebada/priority_validation.py}`; lectura de originales, sin adjudicar métricas nuevas.
- [FAO 56, capítulo 8](https://www.fao.org/4/x0490e/x0490e0e.htm): capacidad disponible, espesores y distinción respecto a balance/estrés real.
- [ISRIC, capas](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html) y [acceso](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_02.html): unidades, profundidades, quantiles y acceso alternativo. Documentación consultada en esta planificación; disponibilidad local aún pendiente.
- [USGS, NDMI](https://www.usgs.gov/landsat-missions/normalized-difference-moisture-index): interpretación del índice NIR–SWIR, sin asumir que corresponda al NDWI entregado.
- [NASA POWER, metodología](https://power.larc.nasa.gov/docs/methodology/): contexto regional y procedencia de meteorología/radiación.
- [Fu et al., 2022](https://www.nature.com/articles/s41467-022-28652-7): hipótesis de sequedad atmosférica y humedad, sin validar un índice escalar o umbral universal para cebada local.
