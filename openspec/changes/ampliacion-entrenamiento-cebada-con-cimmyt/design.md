## Context

Véase `proposal.md` para motivación y alcance. El cargador `priority_data.py` y las pruebas `test_priority_population.py` exigen 197 parcelas oficiales y 138 etiquetas. `priority_selection.py` selecciona mediante grupos oficiales internos; no admite actualmente un contexto auxiliar distinto. `src/agrocebada/external.py` exige cuatro respuestas NASA, 214 días de 2025 y unidades concretas. Reutilizarlo modificando esas constantes rompería la ruta vigente.

La fase prioritaria está completada y congelada. Su informe `experiments/prioridades-predictivas-20261006/docs/conclusions.md` conserva el rechazo P06 y la señal diagnóstica de TabPFN-3 mensual; ninguna de esas métricas corresponde a entrenamiento con CIMMYT. Este diseño añade requisitos con nombres distintos a los del cambio anterior, todavía sin archivar. No modifica elegibilidad E08/P06 ni depende de sincronizar sus deltas para ejecutarse como estudio aislado.

La fase `experiments/ampliacion-cimmyt-20261008/` ya adquirió los tres originales V6 y auditó sus columnas y etiquetas. `registry/label-audit.json` registra 1.396 filas de cebada, 1.130 identificadores únicos de grano y 48 candidatos tras filtros agronómicos: 29 locales y 48 mexicanos, antes de admisión espacial o climática. El número de etiquetas efectivamente admitidas sigue pendiente. A00 está recuperado, A01–A03 pendientes y A04 no viable porque su cohorte local tiene como máximo 29 etiquetas frente al mínimo de 30. No se ha ajustado un modelo real nuevo en esta fase.

La revisión del 9 de octubre de 2026 responde a la instrucción del usuario de buscar los metadatos faltantes y revisar el protocolo si no se encuentran. La tabla de parcela contiene puntos `LATITUDE N` y `LONGITUDE W`, sin vértices; las fuentes revisadas no documentan su datum, precisión efectiva ni derivación desde los vértices descritos en el artículo. Se sustituye la exigencia imposible de vértices verificables por un diagnóstico explícitamente condicionado a puntos aproximados. No se revisan filtros agronómicos ni mínimos para aumentar el conteo.

## Goals / Non-Goals

**Goals:**

- Medir el aporte de etiquetas realmente nuevas, distinguiéndolo del cambio a características compartidas y del peso relativo de las fuentes.
- Poder cerrar una auditoría negativa o una ejecución inviable sin fabricar una comparación predictiva.
- Reproducir controles, cohortes por ajuste, predicciones y decisiones desde archivos locales autorizados.

**Non-Goals:**

- Reconstruir índices ópticos finos sobre geometrías anonimizadas, incorporar nuevos proveedores distintos de CIMMYT o ampliar automáticamente los modelos probados.
- Estimar rendimiento oculto para seleccionar recetas, afirmar validación independiente de 2025 o promover un candidato en esta fase.
- Obtener información personal o contactar autores; una necesidad real de credenciales se comunica al titular del acceso.

## Decisions

### 0. Revisión espacial autorizada y alcance de la evidencia

Identificar la revisión como `cimmyt-point-assumption-v2`, anterior a cualquier ajuste real. Conservar en el futuro manifiesto la versión previa, la instrucción del usuario, fecha de revisión, fuentes y hashes de los siete documentos de planificación. Los registros existentes que señalan metadatos pendientes describen el estado previo: deben actualizarse durante apply, sin sobrescribir la evidencia ni afirmar que esta revisión ya fue implementada.

La búsqueda revisó C01/C02, el repositorio público de los autores y documentación institucional BEM/e-Agrology. El artículo, apartados de privacidad y características de parcela, sustenta ubicación aproximada pero no identifica el datum ni el procedimiento de creación de los puntos V6. El catálogo solo declara cobertura México. El script público de estandarización tiene 568 líneas sin referencias a coordenadas, datum, CRS o truncamiento en la revisión examinada. Una búsqueda negativa se limita a estas fuentes; no demuestra que los metadatos no existan en otro lugar. La referencia 18 del artículo es una guía de medición de rendimiento, no documentación de la API geográfica.

Para este estudio se **asume**, sin presentarlo como verificado, que los puntos son latitud/longitud en grados bajo WGS84. Conservar valores originales, `source_crs=unknown`, `analysis_crs=EPSG:4326`, `crs_basis=explicit_assumption`, `location_kind=approximate_point` y `point_semantics=unknown`. No declarar centroide, GPS, vértice o precisión métrica. Verificar finitud, latitud entre 0 y 35 y longitud entre −120 y −85 como control de coherencia con México, no como prueba del datum. Conservar la longitud negativa observada; no invertirla otra vez por el encabezado W, intercambiar ejes ni corregir signos para forzar admisión. Puntos incompatibles quedan excluidos con motivo.

Política principal fija: caja cerrada `[lon−0,01; lon+0,01] × [lat−0,01; lat+0,01]` grados y buffer externo de 2.000 m. El margen ampliado reduce dependencia de una precisión que no se conoce; estos valores son decisiones experimentales, no límites superiores demostrados del error ni de la extensión de parcela. Las mismas reglas rigen todas las cohortes, esquemas y ajustes. Si aparece documentación de incertidumbre mayor o una referencia incompatible, bloquear y revisar antes de ajustar; no ignorarla ni modificar parámetros bajo el mismo identificador congelado.

Antes de entrenar, publicar sensibilidad **solo de admisión** para tres políticas fijadas: estrecha (±0,001°, 1.000 m), principal (±0,01°, 2.000 m) y amplia (±0,02°, 3.000 m). Recalcular en cada ajuste la celda única, exclusiones de grupos y soporte de 30 rendimientos/diez grupos/dos campañas; guardar conjuntos de claves, hashes y cambios de viabilidad. Solo la principal produce características para entrenamiento y selección. Las otras dos no consultan clima ni ajustan modelos y no amplían el catálogo de 16 candidatos o el presupuesto. Si cambian conjuntos o viabilidad, marcar `geographic_sensitivity=detected`; de lo contrario `not_detected_in_tested_policies`, nunca precisión validada. No elegir la política que conserva más registros o promete menor error. Esta comprobación no mide sensibilidad predictiva a otros supuestos ni garantiza ausencia de coincidencia real.

### 1. Fase aislada y evidencia identificada

Crear durante apply `experiments/ampliacion-cimmyt-<fecha-real-de-inicio>/` con código copiado y versionado, dependencias fijadas, `data/raw`, `data/processed`, `registry`, `runs`, `docs` y pruebas propias. Conservar un manifiesto de archivos protegidos de la versión activa y de la fase prioritaria antes y después. La alternativa de ampliar el maestro oficial se descarta porque mezcla poblaciones con contratos y objetivos diferentes.

| Evidencia | Fuente y uso |
| --- | --- |
| C01 | [Catálogo CIMMYT](https://hdl.handle.net/11529/10548986): resolver versión y archivos de bitácora/parcela, siembra/cosecha/rendimiento y glosario; registrar términos vigentes antes de adquirirlos. |
| C02 | [Descriptor científico](https://www.nature.com/articles/s41597-025-06143-w): sustenta la existencia de rendimientos de cebada; advierte ubicaciones truncadas a tres decimales, métodos de medición heterogéneos y sesgo asociado a asistencia técnica. No demuestra compatibilidad con el reto. |
| C03 | `docs/Reto Agrocebada Bases.md`, sección DATASET: admite información pública adicional y reserva las etiquetas ocultas al comité. |
| C04 | Informe priorizado y manifiesto congelado local: controles recuperables y limitación de reutilizar 138 etiquetas. |
| C05 | [API diaria NASA](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) y [fuentes NASA](https://power.larc.nasa.gov/docs/methodology/data/sources/): soporte temporal histórico y malla meteorológica nativa; consultas por celda, sin duplicarlas por parcela. |
| C06 | [Repositorio de los autores](https://github.com/gmonpr/Historical-Agronomic-Dataset/tree/bcc359c2323284def49521dbb5d4fe8538350ae2), revisión consultada el 9 de octubre de 2026: ejemplos de unión y estandarización; no resuelve datum, precisión ni derivación de puntos V6. Lectura del script mediante URL pública tras fallo del visor web. |
| C07 | [Nota institucional e-Agrology](https://www.cimmyt.org/es/noticias/e-agrology-una-herramienta-que-cruza-fronteras/) y [captura BEM/GeoODK](https://www.cimmyt.org/es/noticias/las-tic-y-el-aumento-de-la-produccion-de-maiz-de-manera-sustentable-en-guerrero/), consultadas el 9 de octubre de 2026: documentan captura y georreferenciación, sin certificar metadatos del archivo V6. No justifican extrapolar el datum de otra herramienta al Excel. |

Conservar fecha de consulta y versión resuelta, sin fijar a ciegas la última versión publicada. No descargar los archivos de insumos, labores, irrigación o costos si los tres archivos iniciales bastan. Si falta un campo indispensable, documentar cuál; no incorporar otros archivos o fuentes automáticamente. Las condiciones del catálogo gobiernan adquisición y distribución: almacenamiento local y derivados solo según autorización efectiva.

### 2. Auditoría con criterios cerrados antes de resultados predictivos

Guardar un mapa del diccionario real hacia un esquema canónico: fuente/versión, productor, parcela, bitácora, siembra, rendimiento/producto, estado/municipio, año/ciclo/modalidad, fechas, área, unidad de área y rendimiento, método de medición/humedad si constan, ubicación y su incertidumbre. No usar nombres de columnas adivinados como si fueran observados.

Uniones: comprobar claves únicas y cardinalidades por hoja antes y después de cada cruce. Deduplicar copias del mismo identificador de rendimiento; desacuerdos quedan excluidos. Para varias cosechas del mismo grano y campaña, agregar únicamente si la documentación demuestra producción incremental y área denominadora común: sumar producción y dividir una sola vez por el área correspondiente. No promediar t/ha sin soporte ni sumar rendimientos de tratamientos o subparcelas distintos. Mezclas de cultivos o resiembras sin atribución inequívoca quedan fuera.

Admitir grano de cebada, rendimiento finito no negativo y área finita positiva, unidades convertibles de forma explícita a t/ha y ha, año 2012–2022, primavera–verano, temporal, ubicación utilizable, siembra y cosecha íntegramente entre el 1 de abril y el 31 de octubre de su campaña. Unidades desconocidas, fechas incompletas, producto ambiguo y campañas cruzadas quedan excluidos. Conservar ceros comprobables; no recortar valores por residuos ni ajustar humedad sin información suficiente. Las incógnitas de método/humedad se reportan como heterogeneidad de medición. La modalidad oficial se verifica únicamente en originales; si no consta, la equivalencia con temporal permanece desconocida.

Dos cohortes anidadas: `C-local` = Puebla/Hidalgo/Tlaxcala; `C-mexico` = todo México que cumple las mismas reglas. No se amplían después de observar errores. Reportar las cohortes descartadas de invierno/riego sin entrenarlas en esta fase. Los umbrales siguientes son decisiones experimentales propuestas, no propiedades publicadas del dataset.

Crear un identificador auxiliar con prefijo de fuente y claves originales, y un grupo de dependencia por componente de productor/parcela: todas sus campañas y parcelas relacionadas permanecen juntas. Si falta productor, usar parcela como grupo mínimo y declarar que no se puede controlar dependencia entre parcelas del mismo productor. Si falta parcela recuperable, excluir. Publicar ambos conteos y esta limitación, sin afirmar independencia de productores desconocidos.

### 3. Características comunes limitadas y verificables

Representación única `common-area-nasa-v1`: `log1p(area_ha)`, tres resúmenes por ventana (precipitación acumulada, temperatura media y amplitud diaria media Tmax−Tmin), e indicadores estatales Puebla/Hidalgo/Tlaxcala/otro predefinidos. Total: diez variables continuas y cuatro indicadores; estado sirve como contexto categórico, nunca como código numérico ordenado. Fuente, campaña, claves, fechas de cosecha, manejo, ingresos y datos demográficos no son predictores. No incorporar precipitación o temperatura anual estimada por productores como equivalente de NASA.

Solicitar `T2M`, `T2M_MIN`, `T2M_MAX`, `PRECTOTCORR` en JSON, comunidad AG, tiempo LST, del 1 de abril al 31 de octubre de cada celda/año necesaria. Reutilizar los datos 2025 íntegros ya disponibles cuando su malla, parámetros y unidades son compatibles; mantener sus hashes. Consultas nuevas solo para auxiliares admitidos y años 2012–2022. Almacenar URL, respuesta, versión/metadatos, fecha y hash; máximo 1.000 pares celda/año, solicitudes secuenciales, hasta tres intentos por consulta con espera acotada y caché por clave. Si se excede el límite, detener adquisición con diagnóstico: ampliar presupuesto exige revisión del protocolo previa a entrenar.

Verificar malla de cada parámetro según sus metadatos; la meteorología se documenta como 0,5° latitud × 0,625° longitud. No aplicar la malla de radiación ni una malla 0,5° cuadrada por conveniencia. Para auxiliares aplicar la caja principal de puntos de la decisión 0; admitir solamente si toda la caja resuelve una única celda meteorológica nativa. Contactar un límite de celda también es ambiguo: excluir, sin desempate por centro del punto ni rendimiento. La resolución de celdas y sus límites debe concordar con metadatos/respuestas NASA y conservarse en el contrato. La falta de datum documentado se permite exclusivamente bajo esta revisión asumida; puntos faltantes, incompatibles o que requieran incertidumbre mayor quedan fuera o bloquean según la decisión 0. No exigir vértices que el Excel no contiene ni deducir precisión del número de decimales. La geometría oficial conserva su referencia y política histórica verificadas.

Exigir los 214 días únicos y valores finitos en los cuatro parámetros; Tmin≤Tmax, Tmedia entre −60 y 60 °C, Tmin entre −80 y 60 °C, Tmax entre −60 y 70 °C, precipitación entre 0 y 2.000 mm/día, sin códigos de relleno. No interpolar ni rellenar series climáticas auxiliares. Las 197 entradas oficiales comunes deben ser completas; si faltan, bloquear la comparación principal en lugar de reducir sus 138 etiquetas. Área auxiliar procede de una medición/unidad identificada; no se calcula desde el polígono anonimizado. Identificar diferencias frente al área oficial.

Se descarta el uso compartido de índices ópticos imputados porque la ausencia de toda una rama por fuente confundiría adquisición y rendimiento. Las fechas de cosecha se usan para admisión, sin dar al auxiliar predictores ausentes en las consultas oficiales.

### 4. Exclusión espacial y por dependencia en todos los ajustes

Importar sin cambios `principal-5`, `balanceado-4` y `rotado-45-5` de `registry/schemes.csv` congelado; cada uno tiene 138 asignaciones. El cuarto esquema `intraestado-3` queda como antecedente y no sustituye ninguno de los tres. Validar sus hashes y asignaciones al preparar la fase, sin regenerar grupos.

Para cada ajuste externo e interno, partir de los auxiliares de la cohorte y excluir cualquier grupo cuya caja principal asumida esté a ≤2.000 m de un polígono oficial retenido. Considerar todos los puntos/campañas del grupo, sin seleccionar un representante que oculte proximidad. Calcular un límite inferior conservador de distancia en metros que cubra la caja completa mediante proyección por zona con distorsión acotada o método geodésico; un cálculo incierto en torno al umbral excluye. No basta medir el centro ni muestrear solo esquinas. Para zonas lejanas usar distancia geodésica o partición por zona, no EPSG:32614 indiscriminadamente sobre todo México. Incluir las parcelas externas de validación también al ajustar dentro del entrenamiento externo. Si existiera calibración retenida, aplicar la misma exclusión; esta fase no añade intervalos nuevos. No usar rendimientos retenidos al calcular proximidad. Repetir el cálculo en las políticas de sensibilidad solo para sus conteos, sin cambiar la política principal.

Exigir después de exclusión y muestreo al menos 30 rendimientos, diez grupos de dependencia y dos campañas para que un candidato ampliado sea viable en un ajuste. Si falla en un fold interno, ese candidato completo es inviable, sin promediar solo folds favorables. Si una cohorte no es viable, el procedimiento puede seleccionar el control sin auxiliares. Registrar soporte oficial por estado separado del auxiliar; un estado sostenido solo por donantes se identifica como transferencia. La exclusión limita vecindad bajo el supuesto de ubicación, pero no garantiza separación de parcelas reales sin límites conocidos ni demuestra ausencia de productores compartidos cuya identidad oficial no consta.

### 5. Experimento principal acotado con peso por grupo

Una familia principal: Ridge directo, intercepto sin penalizar, regularización α∈{1,10}; las dos referencias media global/regional se ajustan exclusivamente con etiquetas oficiales. El diseño usa Ridge como prueba interpretable del aporte de datos y separa el modelo fundacional prometedor como diagnóstico opcional; no reabre GPR/GAM ni P06.

Catálogo principal cerrado: dos controles Ridge sin auxiliares + dos cohortes × tres influencias λ∈{0,25; 0,5; 1} × dos α = 14 configuraciones Ridge; más dos referencias = **16 candidatos únicos**, una representación. Si ambas cohortes coinciden tras auditoría, deduplicar por hash antes de entrenar y registrar un catálogo menor, sin sustituirlas por nuevas opciones.

Para n etiquetas oficiales de ajuste, G grupos auxiliares y n_g filas en el grupo g, minimizar:

\[
\frac{1}{n}\sum_{i\in O}(y_i-f_\beta(x_i))^2+
\frac{\lambda}{G}\sum_{g=1}^{G}\frac{1}{n_g}\sum_{j\in g}(y_j-f_\beta(x_j))^2+
\frac{\alpha}{n}\|\beta\|_2^2.
\]

Equivale a pesos oficiales 1 y auxiliares λn/(G n_g) con la penalización Ridge α. Así λ fija masa auxiliar relativa sin permitir que muchos años del mismo productor dominen. Centrado y escala de variables continuas usan esos pesos y solo filas de ajuste; indicadores estatales conservan su definición fija. La alternativa de concatenar filas con peso uniforme se descarta porque cambia automáticamente la influencia al aumentar el tamaño auxiliar.

Seleccionar α del control común por RMSE interno oficial, empate ≤1e−10 a favor de α mayor. Entre ampliados viables, seleccionar menor RMSE interno; empates prefieren λ menor, `C-local`, α mayor. Admitir ampliación solo si mejora ≥2% frente al control común elegido, gana en al menos dos folds internos y no empeora MAE estatal >10% en estados con ≥10 etiquetas internas evaluadas. Si no cumple, usar el control común. No elegir medias como alternativa de este contraste: permanecen como referencias y conservan su propia evaluación. No ensambles ni ajuste de pesos con OOF externas.

| Ejecución | Contenido | Función |
| --- | --- | --- |
| A00 | Recuperar control completo P00-C-activa, ruta oficial, en los tres esquemas y sus 59 consultas | Competitividad frente a la versión vigente; verificar versión y métricas originales |
| A01 | Control Ridge común con α seleccionado internamente, solo 138 etiquetas | Contraste pareado de datos: mismas columnas y algoritmo |
| A02 | Procedimiento común con selección interna entre ampliados y alternativa A01 | Medir aporte efectivo, registrando cuándo no usa donantes |
| A03 | Curva de tamaño auxiliar 25%, 50%, 100% de grupos | Diagnóstico del tamaño, no selector retrospectivo |
| A04 opcional | TabPFN-3 común, sin donantes frente a contexto ampliado fijo | Evaluar si otra familia aprovecha los datos; separado de A02 |

A03 conserva por fold externo la receta A02 seleccionada internamente y aplica orden de grupos por hash SHA256 de clave+semilla 2026, tomando ceil(fracción×G), con todos sus registros. El 100% reutiliza su predicción A02; los pesos se renormalizan manteniendo λ. Si A02 eligió λ=0, la curva se marca no aplicable a ese fold. Fracciones con soporte insuficiente se marcan no viables, no se sustituyen silenciosamente por 100%. No presentan evidencia sobre datos nuevos independientes.

A04 utiliza el checkpoint, entorno y configuración CPU verificados de TabPFN-3 (ocho estimadores, semilla 2026), cuya finalidad profesional experimental no comercial ya confirmó el usuario. Solo dos configuraciones fijas: contexto oficial común y el mismo contexto + hasta 256 auxiliares de `C-local`. Muestreo determinista balanceado por grupo mediante rondas de una observación por grupo, ordenando por hash y preservando claves/campañas; sin duplicaciones para simular pesos. Excluir proximidades antes de muestrear y aplicar los mínimos anteriores. Las observaciones de un grupo nunca se usan como validación auxiliar: las métricas siguen siendo oficiales. No ampliar a `C-mexico` tras ver resultados ni ajustar pesos que el adaptador no soporta. Si checkpoint, licencia, soporte o recursos fallan, A04 se omite con motivo y continúan A00–A03.

### 6. Criterios de lectura congelados y límites

Para declarar **aporte estable de etiquetas en A02**, exigir frente a A01: reducción RMSE ≥2% en principal y al menos dos esquemas, media de tres razones RMSE≤0,98, ninguna razón >1,05 y aumento MAE estatal ≤10% en cada esquema con n≥10. Exigir que A02 haya usado auxiliares en al menos un ajuste externo de cada esquema; de otro modo no afirmar evidencia positiva de ampliación. Publicar frecuencias y soporte, incluidas las predicciones de respaldo.

Cualquier aporte estable se denomina **estabilidad predictiva condicionada a `cimmyt-point-assumption-v2`**. Publicar junto a la conclusión el datum supuesto, semántica/precisión desconocidas y sensibilidad de admisión. No afirmar robustez geográfica, independencia espacial certificada o validación del datum por obtener mejores métricas. Aunque las tres políticas conserven los mismos conjuntos, la incertidumbre documental permanece.

Calcular por separado **competitividad frente a la activa**, aplicando los mismos umbrales contra A00, además del contraste con media regional. Ningún indicador constituye elegibilidad de promoción de esta fase. A04 publica diferencias y los mismos indicadores descriptivos frente a su pareja sin donantes, sin sustituir A02.

Reportar RMSE, MAE, R², sesgo, estado, fold y tercil de área; conteos de parcelas, productores conocidos, campañas y celdas; diferencias por parcela y tasa de respaldo. No sumar 138×3 como etiquetas independientes, ni afirmar significación a partir de errores correlacionados o haber agotado todas las fuentes posibles. No calibrar intervalos con donantes. Las 59 consultas sirven para comprobar contrato, finitud y recuperación, nunca para elegir configuración por sus valores predichos.

### 7. Recursos, registro y recuperación

Adquisición con red y entrenamiento sin red son etapas separadas. Congelar protocolo y manifiestos después de la auditoría y preparación y antes del primer ajuste real; fijar versiones concretas entonces, incluyendo lector XLSX y entorno TabPFN existente. La auditoría tiene su propio registro y estado; añadir `pending_access` en la fase nueva sin alterar el registro histórico. Ningún resultado parcial recibe estado `completed` predictivo. Si ninguna configuración ampliada es viable en ningún ajuste de los tres esquemas, A02/A03 se registran como no viables; los resultados disponibles pertenecen a A01 y no se renombran como un experimento de ampliación completado. Si existen candidatos viables pero la selección los rechaza, A02 sí constituye una comparación realizada, conserva las decisiones internas negativas y sus respaldos A01.

Máximo un trabajador, dos hilos, 4.096 MB de memoria agregada del árbol; 7.200 s por ejecución principal y 1.800 s por configuración opcional. Adquisición: máximo 1.000 consultas y tres intentos por consulta. Un preflight sintético verifica contexto máximo, aislamiento y recursos sin etiquetas oficiales ni búsqueda automática de tamaños que luego cambie el protocolo. Límites superados producen fallo/inviabilidad explícitos y no autorización implícita de cómputo remoto.

Conservar modelos, matrices/contextos auxiliares permitidos, escalas, pesos, claves por ajuste, exclusiones, OOF completas, consultas de 59, métricas y manifiestos. Recuperar en proceso nuevo sin red con tolerancia absoluta 1e−10 y relativa 0 para predicciones guardadas; para una dependencia que no cumpla, registrar el fallo sin relajar la tolerancia de una ejecución ya congelada. Recalcular todas las métricas desde OOF y exigir integridad de archivos protegidos.

## Risks / Trade-offs

- [Pocos registros tras filtros y buffer] → Mantener mínimos y cerrar con conteos negativos; no cambiar ciclo, modalidad o regiones para fabricar viabilidad después de ver errores.
- [Sesgo de asistencia técnica y cambio temporal] → Control común pareado, influencia limitada por fuente/grupo, análisis de sesgo estatal; la ponderación no demuestra corregir todo cambio de dominio.
- [Representación común sin señal espectral] → Comparar también A00; una mejora frente a A01 puede seguir siendo insuficiente para el producto.
- [Modalidad o humedad oficial desconocida] → Declarar transferencia y heterogeneidad; sin equivalencias ni correcciones inventadas.
- [Datum, semántica y precisión de puntos desconocidos] → Supuesto identificado, margen/buffer principal ampliados y sensibilidad previa de admisión; no certificar límites de parcela, datum o separación espacial real. Una futura fuente que contradiga el supuesto exige revisión, no corrección silenciosa.
- [API o condiciones de uso cambiantes] → Manifestar versión, caché y acceso real; un acceso pendiente no cuenta como datos inexistentes ni como experimento ejecutado.
- [Sobreajuste del proceso de investigación sobre 138 etiquetas] → Catálogo pequeño, selección interna, resultados de los tres esquemas y carácter diagnóstico; será necesaria otra campaña etiquetada para validación temporal independiente.

## Migration Plan

Durante apply: preparar fase aislada y controles; auditar acceso y datos; producir cohortes y características; congelar protocolo; ejecutar verificaciones y comparaciones; publicar conclusión y paquete local recuperable. Si el acceso está pendiente, completar herramientas y pruebas independientes y dejar dependientes abiertas. Si la auditoría concluye insuficiencia, cerrar sus resultados y registrar comparaciones como no viables; las tareas de ejecución no se describen como pruebas predictivas realizadas.

Para aplicar esta revisión, conservar las nueve tareas ya completadas, implementar la política de puntos y sensibilidad, reconciliar el informe y estados pendientes de metadatos con sus antecedentes y congelar v2 antes de entrenar. La revisión documental no completa tareas de código ni cambia el cierre de A04: 29 etiquetas locales sigue siendo insuficiente.

No hay migración del dashboard ni activación. Revertir consiste en dejar de utilizar la nueva fase, manteniendo la versión oficial y los experimentos previos intactos. Cualquier incorporación al producto requerirá un cambio posterior con criterios de promoción explícitos.
