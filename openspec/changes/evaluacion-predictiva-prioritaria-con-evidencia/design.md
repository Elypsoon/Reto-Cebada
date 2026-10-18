## Context

Ver `proposal.md` para la motivación. La unidad es la parcela de abril–octubre de 2025: 197 identificadores, 138 etiquetas, 59 consultas sin rendimiento conocido, corte 2025-10-31 y salida en t/ha. No existe otra campaña etiquetada. Los grupos espaciales de la fase anterior y sus resultados ya fueron observados; repetirlos aporta evidencia de desarrollo, no un test nuevo.

La versión activa usa `src/agrocebada/modeling.py`: `CompactSelector` imputa y ordena por correlación marginal antes de limitar variables. La fase recuperable `experiments/soporte-regional-20261003` añade `variants.py`, `segments.py`, `phase.py`, `tracking.py` y `optional.py`, con catálogo congelado, contextos opcionales, contratos y recuperación. Se reutilizarán estos mecanismos en otra carpeta; no se editarán las fases cerradas. `common.py` resuelve datos/artefactos desde la carpeta del módulo y `workspace.json`, por lo que los procesos de cada versión deben aislar también importaciones y rutas.

El control regional E00-v2 tiene RMSE oficial principal 0.756346; la activa declara 0.764573 oficial y 0.764053 enriquecido. E08-v2 obtuvo 0.687622 enriquecido en principal, pero el MAE de Puebla rotado fue 0.424265 frente a 0.377922 regional y no hubo activación. Su cobertura principal de intervalos fue 84.78%, menor al mínimo 85%. Estos antecedentes proceden del informe local y no se asignan a ejecuciones nuevas.

## Goals / Non-Goals

**Goals:**

- Separar el efecto de cinco mecanismos prioritarios y evaluar un combinado ya definido, con resultados pareados, presupuestos acotados y recuperación local.
- Incorporar la evidencia como justificación falsable, distinguiendo fuente externa, observación local e hipótesis de diseño.
- Cerrar cada comparación con un resultado verificable o un motivo concreto de ausencia, preservando la población completa.

**Non-Goals:**

- Buscar continuamente parámetros hasta lograr un error deseado o reinterpretar las particiones observadas como confirmación independiente.
- Incorporar nuevas fuentes ambientales, imágenes originales, radar, rotaciones históricas como campañas etiquetadas, correcciones de etiquetas, redondeo de Tlaxcala o simulaciones agronómicas completas.
- Activar modelos, modificar el dashboard activo, desplegar ni enviar predicciones en esta fase.

## Decisions

### 1. Evidencia y límites de interpretación

Fecha de consulta de la investigación: 2026-10-06. El registro que se implementará conservará estos vínculos, el alcance de lectura y la relación con cada hipótesis; no descargará nuevamente fuentes durante inferencia.

| ID | Fuente primaria o local | Evidencia disponible y alcance | Uso en esta fase |
| --- | --- | --- | --- |
| L01 | [Código del selector](../../../src/agrocebada/modeling.py), [historial de la fase](../../../experiments/soporte-regional-20261003/docs/phase-results.md) | Archivos locales leídos: filtro marginal, resultados negativos y protección regional fallida. No demuestra que el filtro sea la causa del error. | P01 y criterios de P06. |
| L02 | Franch et al., 2026, [The yield strikes back](https://doi.org/10.1016/j.jag.2026.105140) | Resumen y fragmentos indexados del PDF institucional sobre trigo/cebada, tiempo térmico y fusión óptica–SAR. No se recuperó íntegramente el texto; no se copian sus parámetros ni ganancias. | P02; adaptación explícita con NASA existente, sin reproducir el método completo ni usar radar. |
| L03 | Zou y Okhrin, 2026, [Stagewise crop yield prediction with multisource functional indices](https://onlinelibrary.wiley.com/doi/full/10.1002/cjs.70043) | Texto consultado: GAM y modelos funcionales; también resultados negativos de representaciones excesivas y componentes ruidosos. Datos, objetivos y escalas difieren del reto. | P04/P05; pocas bases y componentes, sin promesa de mejora. |
| L04 | [Tutorial de modelos multinivel de Stan](https://mc-stan.org/learn-stan/case-studies/tutorial_rstanarm.html) | Documentación de interceptos/pendientes y pooling parcial. Es fundamento estadístico, no evidencia de rendimiento agrícola local. | P03/P06, regularización de efectos regionales. |
| L05 | [Documentación oficial de EBM](https://interpret.ml/docs/ebm.html), [GPML](https://gaussianprocess.org/gpml/chapters/) | Modelos aditivos, interacciones y covarianzas. No fija una complejidad óptima para 138 etiquetas. | GAM/EBM y kernel aditivo jerárquico. |
| L06 | Qu et al., ICML 2026, [TabICLv2](https://proceedings.mlr.press/v306/qu26a.html), [implementación oficial](https://github.com/soda-inria/tabicl) | Resumen del paper y documentación: soporte de regresión y benchmark tabular; pesos concretos aún no verificados localmente. | P07, comparación opcional independiente. |
| L07 | Prior Labs, mayo 2026, [TabPFN-3: Technical Report](https://arxiv.org/abs/2605.13986), [implementación oficial](https://github.com/PriorLabs/TabPFN) | Informe/resumen y documentación. Su benchmark no valida estas parcelas y no sustituye TabPFN 2.5 retroactivamente. | P08, comparación opcional independiente. |
| L08 | [Cawley y Talbot, 2010](https://www.jmlr.org/papers/v11/cawley10a.html), [Roberts et al., 2017](https://doi.org/10.1111/ecog.02881) | Selección repetida y validación con estructura espacial. No aporta un umbral universal de mejora o distancia. | Congelación, separación interna/externa y límites de inferencia. |

No se afirman lecturas completas de documentos inaccesibles ni se utilizan porcentajes publicados como expectativa local. Las ecuaciones y parámetros siguientes son decisiones del proyecto basadas en esa evidencia.

### 2. Aislamiento, controles y versiones

Crear durante la implementación `experiments/prioridades-predictivas-20261006/`, con identidad única de cada ejecución y sufijos de reintento cuando corresponda. Copiar únicamente código, tablas y dependencias necesarias de la fase recuperable; no copiar entornos, temporales ni resultados como si fueran ejecuciones nuevas. Guardar origen, hashes y una versión inmutable antes del primer entrenamiento.

P00 consta de dos controles recuperables: C-activa reproduce el procedimiento histórico activo original, incluidas selección interna y rutas oficial/enriquecida; C-soporte reproduce E00-v2. Se ejecutan con su propio código/dependencias en destinos nuevos y los mismos IDs/folds/datos. C-activa se evalúa en los tres esquemas; su principal debe reproducir el antecedente dentro de tolerancia 1e-10. C-soporte se contrasta con sus tres vectores existentes. Un desacuerdo se investiga y conserva; no se modifica el manifiesto para aceptarlo. P06 se compara con la ruta oficial de C-activa porque P06 usa solo insumos oficiales; la ruta enriquecida activa se publica como sensibilidad distinta.

Reutilizar por ID el manifiesto `registry/schemes.csv` revisión 2: `principal-5`, `balanceado-4`, `rotado-45-5`; no regenerar grupos ni cambiar límites al consultar errores. El esquema `intraestado-3` se conserva como diagnóstico para P00/P06. Leave-one-state-out y buffer de 1 km siguen siendo sensibilidades de P06 con inviabilidad explícita.

### 3. Catálogo congelado y presupuesto

P00 y P01–P06 son obligatorios; P07/P08 son opcionales. Congelar todos sus protocolos, la receta P06, decisiones de desempate y límites antes de consultar cualquier resultado externo nuevo, incluidos los controles reproducidos. Las decisiones de factibilidad previas utilizan solo inventario, tipos, geometría, soporte de señales, pruebas sintéticas y recursos, no búsqueda de desempeño. Semilla 2026; dos hilos por proceso; ejecución secuencial, un solo entrenamiento simultáneo.

| ID | Hipótesis y control de mecanismo | Familias y representaciones | Grilla prevista de modelos base, incluidas dos referencias |
| --- | --- | --- | --- |
| P00 | Reproducción de C-activa/C-soporte. | Procedimientos históricos originales; ninguna búsqueda ampliada. | Sus catálogos históricos, con resultados separados por control/ruta. |
| P01 | Ranking marginal frente a conjunto agronómico fijo y todas las columnas elegibles; control: la variante con ranking de este mismo bloque. | GPR/CatBoost; `monthly_20_10` y `whittaker_20_10`; mismos parámetros y fuentes oficiales. | 2 tablas × 3 selectores × (2 longitudes GPR + 2 profundidades CatBoost) + 2 = 26. |
| P02 | Eje térmico frente a calendario; control: resumen calendarizado del mismo bloque enriquecido, con los mismos datos NASA y covariables. | GPR/CatBoost; resúmenes por segmentos calendario/térmico; NASA como dependencia de ambas variantes. | 2 ejes × (2 longitudes + 2 profundidades) + 2 = 10. |
| P03 | Compartir efectos estatales con regularización; control: variantes sin efecto estatal del mismo bloque, además de media regional. | Ridge jerárquico/GPR jerárquico; tablas monthly/whittaker oficiales con selector fijo. | 2 tablas × (4 penalizaciones estatales × 3 ridge + 3 varianzas estatales × 2 longitudes GPR) + 2 = 38. |
| P04 | Efectos suaves/aditivos y pocas interacciones frente al control congelado. | GAM/EBM; tabla mensual y conjunto agronómico fijo. | GAM: 2 números de nudos × 3 penalizaciones; EBM: 2 resoluciones × 2 conjuntos de interacciones; + 2 = 12. |
| P05 | Forma de las curvas frente a sus resúmenes; control: resúmenes calendarizados con idénticas covariables y calidad. | GPR/Ridge; resúmenes de calendario/proyección funcional de calendario. | Resúmenes: 5 ajustes; funcional con 2 o 3 componentes por rama: 10 ajustes; + 2 = 17. |
| P06 | Combinado predeclarado de selección compacta, jerarquía y curvas; elegibilidad oficial únicamente. | GPR jerárquico/GAM jerárquico; compacto mensual/proyección funcional calendarizada con 2 componentes por rama. | 2 representaciones × (3 varianzas estatales × 2 longitudes GPR + 3 penalizaciones estatales × 2 GAM) + 2 = 26. |
| P07 | TabICLv2 frente a C-soporte y TabPFN 2.5 histórico. | Un modelo, dos tablas oficiales fijas: monthly/whittaker. | Dos configuraciones, evaluadas individualmente; sin seleccionar la mejor con OOF externa. |
| P08 | TabPFN-3 frente a los mismos controles. | Un modelo, las mismas dos tablas fijas. | Dos configuraciones independientes, sin incorporación a P06. |

No existe producto cartesiano entre todos los bloques. C-soporte, C-activa y media regional acompañan el reporte de P01–P05; los controles dentro de cada bloque aíslan su mecanismo. Las referencias global/regional son una vez por bloque, no copias por representación. Las alternativas de intensidad y ensamble se cuentan antes de congelar: en P01/P04/P05 se permiten modelo directo y corrección regional con intensidades 0.5/1; P02 evalúa directos para aislar el eje. P03/P06 utilizan su formulación jerárquica conjunta como corrección regularizada, sin una segunda envoltura de atenuación sobre ella. Los modelos/correcciones/referencias suman 74/10/38/32/47/26; cada bloque incluye además cuatro recetas de ensamble predeclaradas. Los totales máximos previstos son P01=78, P02=14, P03=42, P04=36, P05=51 y P06=30. La corrección del conteo fue autorizada por el usuario antes de congelar y no incorpora modelos ni parámetros adicionales. La implementación puede deduplicar configuraciones algebraicamente idénticas; conserva un listado explícito y prueba que el total oficial final de cada bloque no supera 160. Las dos familias y dos representaciones de P06 no cambian.

Solo se permiten los promedios uniformes predeclarados: ganadores internos de las dos familias, referencia regional más ganador de una familia, o los tres componentes. No ajustar pesos continuos ni mezclar candidatos de P01–P05. P06 conserva ambas representaciones y todos sus parámetros originales aun cuando una ablación aislada fracase; la selección interna, no el resultado externo, elige el candidato viable.

### 4. Selección de variables y covariables comunes

Tres modos P01: ranking actual con disponibilidad ≥50%, constantes excluidas, redundancia absoluta >0.95 y k=10/20 según familia; lista agronómica fija; todas las columnas numéricas elegibles sin ranking ni exclusión por correlación, con imputación train y eliminación de constantes. No aplicar el límite k de la variante histórica a la variante sin ranking. Registrar dimensiones efectivas y disponibilidad por fold.

La lista agronómica numérica fija contiene 16 variables disponibles en el diccionario: `s2_evi_{early,middle,late}`, `planet_msavi_{early,middle,late}`, `landsat_vi6t_late`, `climate_PREC_{early,middle,late}`, `climate_Tmean_{early,middle,late}`, `elevation`, `slope`, `log_area`. Es una hipótesis del proyecto, no una lista publicada óptima. Los indicadores de estado necesarios para referencias se conservan separadamente; no entran ID, conjunto, objetivo ni coordenadas. Los directos conservan el tratamiento estatal declarado de su control; los jerárquicos reciben el estado como índice de grupo, no como predictor espectral.

Para P02/P05, compartir nueve covariables ambientales (`PREC`/`Tmean` en las tres ventanas, elevación, pendiente y log-área) y calidad calculada sin etiquetas por las mismas cinco ramas: número de observaciones y fracción de días respaldados. P02 añade el total GDD a ambas variantes para aislar el cambio de eje. P06 usa siete variables espectrales compactas más las nueve ambientales o componentes funcionales más esas nueve ambientales; en ambas representaciones añade exactamente los mismos diez indicadores de calidad. Estos indicadores derivan de las observaciones aceptadas, no de una reconstrucción ficticia. Columnas ausentes se registran; imputación y escala son train-only.

### 5. Tiempo térmico con NASA existente

Reutilizar `read_nasa()` y el mapeo nativo de `external.py`, verificando nuevamente fechas, unidades, valores físicos y hashes locales sin obtener fuentes nuevas. Las cuatro respuestas no son 197 series independientes; el reporte conserva celdas y parcelas por celda. No usar CHIRTS mensual para simular días.

Mantener base 0 °C y tope 26 °C ya declarados, con temperaturas extremas recortadas antes de promediar, como el cálculo existente. Para cada día:

\[
g_d=\frac{\operatorname{clip}(T_{min,d},0,26)+\operatorname{clip}(T_{max,d},0,26)}{2},\qquad
G(t)=\sum_{d=2025-04-01}^{t}g_d.
\]

Eje térmico `G(t)-G(2025-04-01)` y eje calendario `t-2025-04-01`, ambos con origen cero. Las ventanas relativas son tercios del rango entre origen y corte de cada eje; los extremos de integración usan el eje original con unidades. No estimar una siembra ni elegir parámetros térmicos con etiquetas.

Cinco ramas independientes: Sentinel-2 NDVI/EVI, Planet NDVI/MSAVI, Landsat VI6T. Nubes ≤20%; segmentación por lagunas >21 días calendario y ≥4 observaciones distintas por segmento. Reutilizar curvas locales semanales lambda=10; cambiar solo la coordenada temporal para P02, sin unir segmentos ni reinterpretar suavizado como observación. Resumir por rama medias de las tres ventanas, integral respaldada por unidad de eje respaldado y máximo local. Fechas/picos de temporada solo se publican cuando cumplen soporte ≥8 observaciones y al menos dos a cada lado del máximo; de otro modo permanecen ausentes. Agrupar tiempos térmicos coincidentes por peso dentro del segmento; un segmento sin al menos dos coordenadas térmicas distintas no aporta integral térmica y se registra. No introducir incremento positivo artificial.

NASA se evalúa aquí como fuente que define la representación, no como una columna que se puede retirar conservando en secreto el eje. P02 es enriquecido y diagnóstico; su control calendarizado contiene la misma información NASA. Se publica asimismo el control oficial para que la utilidad del eje no se confunda con añadir una fuente. Su resultado nunca modifica P06 en esta fase.

### 6. Proyección funcional compacta sin completar lagunas

P05/P06 trabajan con las cinco ramas anteriores en calendario. Para cada parcela/rama, estimar seis coeficientes de una base B-spline cúbica de nudos uniformes fijos en [0,1] (calendario origen/corte), minimizando error ponderado en puntos respaldados más penalización 10 de segundas diferencias. Los bins sin soporte tienen peso cero. Los coeficientes son una proyección estadística latente; no se guardan valores reconstruidos fuera de segmentos ni se usan para integrar lagunas. No interpretar componentes como antesis o fase observada.

Una proyección individual requiere ≥8 observaciones distintas aceptadas en segmentos utilizables y soporte en al menos dos tercios calendario. Una base compartida requiere ≥20 parcelas de train con coeficientes válidos y ≥50% de disponibilidad de la rama en train. Centrar y ajustar PCA de los coeficientes únicamente con esas parcelas de train; fijar signo por el coeficiente de mayor magnitud para recuperación determinista. P05 selecciona internamente 2/3 componentes por rama; P06 fija dos. No llamar a PCA ordinario de resúmenes mensuales una FPCA de curvas: el contrato declara la aproximación mediante coeficientes de funciones.

Transformar validación/ocultos con la misma base, medias y escalas; coeficientes insuficientes producen scores faltantes con diagnóstico. La imputación de scores aprende de train, sin rellenar curvas. Si una rama no es aprendible, se omite para ese ajuste de acuerdo con la regla; si ninguna rama es aprendible, el candidato funcional es inviable y no se reemplaza por una receta nueva. La referencia global/regional y representación compacta conservan viabilidad y las 138 predicciones externas del procedimiento.

### 7. Modelos jerárquicos y aditivos acotados

Separar la nueva jerarquía del E01b histórico: E01b interpolaba la salida con `n/(n+10)` sobre una referencia estatal sin pooling. P03 aprende conjuntamente efectos regionales y señal parcelaria, con intensidad elegida internamente.

Ridge/GAM jerárquicos utilizan:

\[
\hat y_i=\bar y_{train}+u_{s(i)}+f(x_i),\qquad
\min\sum_i(y_i-\hat y_i)^2+\lambda_s\sum_s u_s^2+\lambda_f J(f).
\]

Centrar efectos de f en train e imponer suma estatal ponderada cero para separar referencia, efectos y señal. Estandarizar y con train y convertir la salida a t/ha. Ridge comparte pendientes; no aprender pendientes independientes por municipio. P03 usa `lambda_s={1,10,50,infinito}` (infinito anula efecto estatal) y ridge `{0.1,1,10}`. P06 GAM usa `lambda_s={1,10,50}` y penalización `{1,10}`.

GPR jerárquico usa media global train y kernel aditivo:

\[
k((x,s),(x',s'))=k_{Matern\,2.5}(x,x')+\tau^2\mathbf1[s=s']+0.15\mathbf1[i=j].
\]

Varianza estatal normalizada `tau²={0,0.25,1}`, longitudes `{1,5}`, sin optimización continua; tau²=0 es el control sin efecto estatal, pero conserva las mismas entradas/normalización. Registrar los componentes posterior estatal/parcelario y la normalización. Cualquier corrección jerárquica sobre un estado no visto se anula y devuelve exactamente la media global aprendida, también en leave-one-state-out.

GPR/CatBoost de P01/P02/P05 conservan longitud `{1,5}`, ruido 0.15, Matérn 2.5 sin optimización y CatBoost profundidad `{2,3}`, 220 iteraciones, tasa 0.03, L2=10. Ridge de P05 usa `{0.1,1,10}`. GAM es una suma de splines cuadráticas, nudos `{3,4}`, penalización ridge `{1,10,100}`; P06 fija tres nudos. Los nudos basados en datos, centramiento y codificación categórica se aprenden solo en train.

EBM tiene `max_bins={8,16}`, interacciones ninguna o exactamente dos pares predefinidos: EVI medio × precipitación media y MSAVI tardío × temperatura tardía. Fijar ocho bags, 1000 rondas máximas, tasa 0.01 y sin early stopping aleatorio; validar la parametrización contra la dependencia exacta antes de congelar. Los conjuntos de interacciones no se descubren en OOF externa. En GAM/EBM directos, un estado ausente se identifica como transferencia; la regla de media global exacta se exige a las correcciones jerárquicas, no se atribuye a un predictor directo.

Alternativas consideradas: efectos sin pooling son frágiles con soporte escaso; pendientes estatales, kernels con una longitud por cada variable y muchas interacciones multiplican parámetros para tres estados/138 etiquetas. Se difieren esas ampliaciones y no se agregan si las grillas actuales pierden.

### 8. Modelos fundacionales separados

P07/P08 usan las tablas oficiales completas `monthly_20_10` y `whittaker_20_10`, las mismas del TabPFN 2.5 histórico. No aplicarles el selector histórico ni otra optimización supervisada externa. Registrar tratamiento nativo de faltantes, preprocessing/contexto train, versiones, dispositivo y parámetros efectivos.

Verificar en preparación identidad de checkpoint de regresión, revisión, SHA-256, formato y condiciones de uso de cada proveedor. Usar un checkpoint por modelo, sin cambiarlo después de observar errores. TabICLv2: ocho estimadores y semilla 2026; TabPFN-3: ocho estimadores y semilla 2026, con parámetros adicionales obligatorios fijados por su versión antes de entrenar. Si la versión no soporta la configuración, cerrar la inviabilidad o registrar un protocolo nuevo antes de cualquier evaluación, sin sustituir por el default de otra generación.

Primero preflight sintético; límite opcional por modelo: 4 GiB RSS y 30 minutos para una configuración completa sobre tres esquemas. CPU inicial, dos hilos, sin servicios pagados/remotos. Si rebasa un límite, interrumpir y registrar resultados parciales/no verificados; no suprimir folds. Preparar pesos y entorno locales para recuperar en un proceso sin red. Exportar float64 con 17 dígitos, aprendiendo de la incidencia E07 de float32; tolerancia absoluta 1e-10 y rtol=0.

### 9. Selección interna, aceptación y cierre

Outer: tamaños mínimos heredados, 15 validación y 80 entrenamiento, sin utilizar y para grupos. Inner: retirar un grupo espacial existente por vez. Bases funcionales, imputación, escala, nudos, efectos estatales, fuentes y ensambles se vuelven a ajustar dentro de cada inner-train; no precomputar PCA global sobre las 197 parcelas.

Reemplazar referencia interna exige RMSE al menos 2% menor, mejora en al menos dos folds internos y MAE estatal ≤110% de referencia con ≥10 etiquetas evaluadas. Orden determinista: referencias global/regional, candidatos por ID de protocolo, ensambles declarados; empates a tolerancia 1e-10 favorecen referencia, luego menor complejidad, luego ID. Un candidato inviable en algún inner-fold se excluye de esa selección con motivo; no se recalcula su promedio quitando el fold. El pipeline debe devolver las 138 predicciones externas mediante candidatos completos o referencia, sin retirar parcelas difíciles.

P06 oficial solo es elegible con los umbrales completos de `specs/yield-model/spec.md`: tres esquemas íntegros, ≥2% frente a regional en principal y al menos dos esquemas, media de razones ≤0.98, ninguna >1.05, protección MAE estatal y además ≥2% principal frente a C-activa oficial y ninguna razón frente a C-activa >1.05. Resultados opcionales y P01–P05 no alteran la receta o umbrales. No se flexibiliza la protección de Puebla por el fallo anterior.

Conservar OOF, sesgo, RMSE/MAE/R² por esquema/estado/fold/tercil, soporte, diferencias por parcela y frecuencias de selección. Las diferencias son descriptivas; no presentar 414 predicciones como etiquetas independientes ni intervalos estadísticos de la mejora como confirmación de generalización.

La incertidumbre de P06 conserva calibración interna independiente con ≥25 etiquetas, nominal 90%, cobertura principal mínima 85% y reporte estatal/amplitud. Ajustar selección y bases nuevamente sin calibración; no fijar un nominal nuevo al ver fallos ni usar todo train para producir el centro de un intervalo calibrado en otro modelo. Si no alcanza el criterio, exportar puntos y disponibilidad de intervalo falsa. La elegibilidad puntual no equivale a cobertura válida.

Cierre: matriz de P00–P08 con estados reales, hipótesis y evidencia; reporte incremental tras cada ejecución. Diferenciar cierre administrativo, cobertura obligatoria evaluada, cobertura opcional y elegibilidad P06. Un fallo/inviabilidad puede cerrar una incidencia, pero no certifica evaluación completa. No afirmar "todas las posibilidades probadas"; alternativas secundarias quedan explícitamente diferidas con motivo.

### 10. Recursos, contratos y pruebas necesarias

No estimar tiempo total a partir de los 6 minutos históricos: nuevos ajustes funcionales y anidados requieren medición. Medir RSS y tiempos por bloque; umbral de los obligatorios: 4 GiB RSS o 120 minutos por bloque, sin ampliar grilla. Si se rebasa, cerrar interrupción e investigar antes de un nuevo protocolo. No reemplazar entrenamiento local por cómputo remoto automáticamente. El preflight comprueba capacidad y compatibilidad, no el error de validación.

Los contratos guardan selectors, covariables, bases funcionales, máscaras/reglas, codificación, normalización objetivo, nudos, efectos estatales, kernel efectivo y fuente que define el eje. Las recetas fundacionales conservan checkpoint y contexto; no asumir formato joblib universal. La explicación debe reconstruir referencia + efecto estatal + corrección ponderada, y tratar sensibilidades no aditivas como tales.

Pruebas esenciales: contaminación de etiquetas/curvas externas, invariancia de consulta individual/lote, soporte n=0/1/pocas, tiempos térmicos coincidentes, lagunas, falta estructural de índice, FPCA no aprendible, total de candidatos y congelación de P06, fallos por alteración de hashes, exportación precisa y recuperación de 59 consultas en proceso nuevo sin red. Para EBM y fundacionales, asegurar que preprocessing/early stopping no usan outer-test. Reutilizar la suite histórica en su versión, sin modificar pruebas congeladas para aceptar nuevos resultados.

## Risks / Trade-offs

- [Selección sobre las mismas 138 etiquetas] → Protocolos previos, resultados negativos e identificación de evidencia de desarrollo; se requiere otra campaña o evaluación oficial para confirmación independiente.
- [NASA comparte celdas y usa origen convencional] → P02 separado, celdas/fechas/unidades visibles, sin fase agronómica confirmada ni dependencia de NASA para P06 oficial.
- [Solo tres estados para efectos jerárquicos] → Regularización fuerte, variantes sin efecto, soporte explícito y estado ausente igual a media global en correcciones.
- [Coeficientes funcionales sensibles a huecos] → Peso cero fuera de soporte, mínimos previos, componentes pocos y alternativas/reference viable sin retirar etiquetas.
- [Filtro sin ranking eleva dimensión] → Ablación con el mismo presupuesto/modelos, regularización y reporte dimensional; no presumir mejora.
- [Dependencias/pesos opcionales incompatibles] → Entornos aislados, hashes y límites; omisión individual, sin degradar los requisitos de P06.
- [Combinado menos favorable que una ablación] → Mantener P06 original, publicar la diferencia; un combinado distinto requiere fase nueva, nunca ajuste post hoc.
- [Reglas de versiones ligadas a rutas históricas] → Resolver workspace/importaciones por proceso y verificar fuentes/artefactos antes y después; no copiar hashes para legitimar código cambiado.

## Migration Plan

1. Preparar carpeta nueva y versiones completas de controles, copiar particiones y verificar datos sin alterar originales.
2. Implementar mecanismos y pruebas en esa fase; resolver dependencias y pesos opcionales, preflight sintético y de soporte sin revisar métricas externas.
3. Congelar catálogo/evidencia/protocolos completos, incluida receta P06, antes de entrenar P00–P08.
4. Ejecutar controles, bloques obligatorios, combinado y opcionales disponibles, con publicación incremental y recuperación verificable.
5. Producir matriz de cobertura, decisión de elegibilidad y paquetes sin activación. Comprobar hashes y 59 predicciones de la activa al cerrar.

No hay migración del modelo activo en este cambio. Si un paquete es elegible, su activación sería un paso posterior explícito. Recuperación: conservar activa y controles completos; un fallo de fase deja sus artefactos/registro y no obliga a revertir el modelo en uso.

## Open Questions

- Revisiones y hashes exactos de `interpret`, TabICLv2 y TabPFN-3: se resolverán en el preflight y quedarán congelados antes de ajustar. No está verificada la disponibilidad local de los dos nuevos checkpoints.
- Tiempo/RSS real en esta computadora: se medirá dentro de los límites anteriores; un exceso produce interrupción registrada, sin cambiar aceptación ni elegir otra grilla por sus métricas.
