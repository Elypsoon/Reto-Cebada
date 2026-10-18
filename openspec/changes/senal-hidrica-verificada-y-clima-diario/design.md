# Design

## Context

Véase `proposal.md`, sección Why. La preparación operativa de `src/agrocebada/cli.py` escribe en `data/processed`; la selección de `modeling.py` admite exclusivamente los grupos NASA y SIAP. El contrato activo selecciona GPR, configuración `whittaker_40_10`, parámetro 5 y NASA; su hash coincide con el control conservado en la fase hídrica. La receta `hydric` utiliza otra selección, imputación y familias: sus resultados no son una ablación exacta de la activa.

La fase `experiments/hidrica-estres-20261009/` está congelada. Su `StressFeatures` exige dos fechas por semana, al menos cuatro semanas válidas y 50% de soporte por ventana. La exploración, sin rendimientos, encontró 79/0/2 parcelas con soporte en abril–mayo/junio–julio/agosto–octubre. La alternativa de 14 días y mínimo de dos intervalos válidos alcanzó 197/161/175 y 144 parcelas en las tres ventanas; cambió duración y mínimo, por lo que no demuestra equivalencia ni valida la semántica del NDWI. Hay que reproducir el diagnóstico con las entradas efectivas nuevas.

Fuentes de orientación: [investigación local](../../../docs/investigacion-variables-cebada-2026-10-12.md), [Sentinel-2 L2A](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html), [catálogo STAC vigente](https://documentation.dataspace.copernicus.eu/APIs/STAC.html), [CHIRPS v3](https://www.chc.ucsb.edu/data/chirps3) y [ERA5-Land](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview). La documentación identifica rutas, no acredita descarga ni cobertura parcelaria. Las reglas relevantes ya existen en las cuatro capacidades; los deltas amplían adquisición, calendario y comparabilidad sin reabrir W05.

## Goals / Non-Goals

**Goals:** construir una fase recuperable con entradas públicas auditadas, decisiones de viabilidad sin etiquetas, catálogo reducido y controles que permitan separar cambio de método y aporte de datos. La unidad final sigue siendo parcela y el rendimiento t/ha.

**Non-Goals:** ejecutar preparación sobre la activa, cambiar los modelos desplegados, revisar resultados de fases cerradas, crear cuentas, pagar servicios, reconstruir fechas de siembra a partir de rendimientos, implementar dashboard o utilizar suelo/térmico en esta fase. Los registros de productores serán opcionales y descriptivos; variables por etapas agronómicas requerirán otro protocolo. No se promete mejorar el RMSE ni identificar mecanismos fisiológicos.

## Decisions

### 1. Fase aislada y versiones de control

Crear `experiments/senal-clima-20261013/` durante apply, con `src`, `scripts`, `tests`, `data`, `registry`, `controls`, `runs` y `docs`. Copiar solo código y datos necesarios, con hashes de origen y dependencias efectivas fijadas. No importar módulos históricos de forma que escriban allí. Registrar un inventario inicial de archivos protegidos: código/datos/modelos operativos, fases experimentales cerradas y entradas oficiales. Los artefactos de planificación nuevos quedan fuera de ese inventario de ejecución.

Recuperar F00-ACT como referencia histórica con su propio código y política originales; exigir reproducción de OOF principal/balanceado/rotado y 59 consultas a tolerancia absoluta 1e-10, relativa cero. La búsqueda histórica se conserva exclusivamente como recuperación de control. Crear F00, control acotado de esta fase, para las comparaciones nuevas. El informe mostrará F00−F00-ACT y cada variante−F00; solo el segundo contraste identifica la adición de un bloque bajo el nuevo procedimiento.

Alternativa descartada: ampliar la preparación operativa directamente. Sobrescribiría contratos y confundiría una nueva fase con la activa.

### 2. Adquisición pública limitada y recuperable

Cada adquisición tendrá manifiesto con consulta, proveedor/producto, versión, fechas de cobertura/publicación/descarga, calendario horario, condiciones de uso, bytes, estado HTTP, hash y motivo. Descarga temporal seguida de validación y publicación local atómica; respuestas HTML, rásteres sin georreferencia y archivos incompletos no se admiten.

Antes de la primera descarga fijar límites de 4 GiB y 45 minutos para adquisición total, máximo tres intentos por solicitud con espera progresiva y recortes al área necesaria. Priorizar catálogo y una muestra de integridad antes de descargar una serie. Los originales incompletos se conservan como evidencia separada y nunca como entradas predictivas. Registrar consumo y límites reales. Al agotarlos, resolver el bloque como no viable y continuar independientemente; no ampliar presupuesto ni cambiar productos tras conocer errores. Las credenciales ya configuradas pueden utilizarse sin registrarlas; nunca se imprimen ni se guardan en manifiestos.

Estos límites son un presupuesto propuesto, no una estimación de descarga exitosa. No adquirir mosaicos nacionales ni instalar entornos completos para un proveedor fallido. La inferencia no tendrá código de consulta remoto.

### 3. Señal vegetal con identidad explícita

Orden previo al entrenamiento: (a) comprobar si existe evidencia original identificable de fórmula/bandas/procesamiento del NDWI suministrado; (b) si no existe, intentar Sentinel-2 L2A de abril–octubre de 2025 para los polígonos oficiales mediante el catálogo STAC vigente. Una referencia genérica no identifica la fórmula de la columna entregada.

La extracción nueva se denominará `ndmi_b8a_b11`: `(rho_B8A-rho_B11)/(rho_B8A+rho_B11)` a 20 m. Requerir reflectancia de superficie con factores/offsets y baseline de procesamiento comprobados, denominador válido y máscara SCL que excluya nubes, sombras, nieve, saturación, píxeles defectuosos y NoData. Extraer sobre intersección de superficie parcelaria, conservando porcentaje válido y número efectivo de píxeles; exigir al menos 80% de superficie válida por adquisición. No completar bandas por remuestreo que fabrique detalle.

Deduplicar por adquisición y fecha; si coinciden productos, usar preferencia determinista por calidad/baseline documentada antes de los resultados. La nueva serie no reemplaza ni cambia la identidad de las variables históricas del control. Solo una definición vegetal y orientación comprobadas habilitan H y las interacciones. El modo de acceso real y su cobertura se resuelven en la auditoría; una cuenta ausente no convierte la fuente en disponible.

### 4. Clima diario y alternativas con roles separados

El bloque D exige CHIRPS v3 **final**, variante diaria basada en satélite (`sat`), comprobada en documentación y archivos, y NASA diario local verificado. CHIRPS aporta lluvia; NASA aporta temperatura/VPD regionales. Registrar explícitamente la desagregación pentadal, escalas nativas y día de cada proveedor. Si `sat` no está disponible o no es íntegro, D queda no viable en este protocolo; no cambiar a `rnl`, versión 2 o precipitación NASA para completar el bloque.

NASA sirve también para las coexposiciones de los intervalos observados de H; no se inventa temperatura local desde su celda. Conservar conversión comprobada de Tmin/Tmax/punto de rocío a VPD y rango físico. No presentar cero días regionales bajo cero como ausencia de heladas parcelarias.

Auditar estaciones SMN por coordenadas, altitud, variable, método, fecha y lagunas de 2025. ERA5-Land se consulta solo con acceso ya disponible. Ambas alternativas producen un informe de contraste/cobertura y, cuando se recuperen, datos auxiliares locales; no sustituyen los predictores primarios de D ni agregan otra variante de entrenamiento en esta fase. Esto acota la selección de proveedor y evita elegirlo por el error. Nuevas fuentes locales favorables requieren otro catálogo antes de evaluarlas.

Exigir al menos 95% de días válidos en cada ventana y al menos 95% de soporte espacial por parcela para CHIRPS. Valores diarios faltantes no son cero; las rachas se calculan únicamente en segmentos diarios contiguos válidos. D será viable si al menos 90% de las 197 parcelas cumple las tres ventanas; conservar todas las filas y sus faltantes. Las estaciones conservan su propia ventana diaria: alinear fechas no demuestra coincidencia exacta de hora con CHIRPS o NASA.

### 5. Calendario y calidad decididos antes de ajustar

Usar intervalos consecutivos de 14 días desde 2025-04-01, con último intervalo truncado al 2025-10-31; la ventana abril–mayo/junio–julio/agosto–octubre se asigna por punto medio real. El diagnóstico de siete días se conserva, pero no es otra configuración elegible. No probar duraciones alternativas con etiquetas.

Un intervalo vegetal requiere dos fechas únicas que superen la máscara espacial. Una ventana requiere al menos dos intervalos válidos y 50% de sus intervalos; H requiere que al menos 70% de las 197 parcelas cumpla las tres ventanas. Si no alcanza el mínimo, H y las comparaciones que lo requieren quedan no viables; no bajar el umbral después de ajustar. Estos valores propuestos se congelan y su cumplimiento se publica sin seleccionar parcelas por rendimiento.

Clima se agrega en esos mismos intervalos. I exige pares vegetal/clima con soporte completo según la misma regla y no interpola sobre lagunas. Registrar soportes en tablas independientes. Los indicadores de calidad de la señal admitida serán covariables comunes de F00 y sus variantes, fijadas antes del catálogo, para separar amplitud espectral y disponibilidad observacional. La diferencia de F00 frente a la activa incluye ese cambio de calidad y metodología y se publica como tal.

### 6. Variables acotadas y efectos principales coherentes

Mantener las tablas históricas de base, ventanas y calidad originales. Los bloques nuevos agregan:

| Perfil | Variables nuevas | Definición |
| --- | --- | --- |
| D | Nueve: tres acumulados de lluvia, tres máximas rachas estimadas y tres percentiles 95 de Tmax regional | Una variable por ventana; racha con lluvia estimada <1 mm/día solo en segmentos válidos; percentil como descriptor observado, no umbral de daño |
| H | Tres medias de señal vegetal | Mediana por intervalo y media ponderada por duración de intervalos válidos, con soporte explícito |
| M | D+H y seis efectos principales coincidentes | Medias de VPD y Tmedia NASA por ventana usando exactamente los intervalos que soportan la señal |
| I | M y nueve indicadores | Dos productos estandarizados por ventana (VPD×señal y Tmedia×señal), y una fracción de coexposición VPD alto/señal baja por ventana |

El umbral de 1 mm define únicamente un descriptor de lluvia estimada. Las escalas y umbrales relativos de I se ajustan dentro de cada entrenamiento interno/externo: VPD alto = quantil 0.75 sobre pares celda/intervalo únicos del entrenamiento; señal baja = quantil 0.25 con peso total igual por parcela. La fracción conjunta usa solo pares válidos. Se conserva soporte y se devuelve faltante ante varianza nula o datos insuficientes. M usa los mismos efectos y pares que I, por lo que F04−F03 aísla la interacción.

Si D no es viable, M/I no se ejecutan en este protocolo, aunque NASA exista. H puede evaluarse independientemente. Los metadatos opcionales no cambian estas ventanas ni habilitan variables agronómicas nuevas.

### 7. Registro opcional de productores

Admitir archivo local opcional con ID_POLIGONO, campaña, campo, valor, unidad cuando aplique, fecha del evento y procedencia. Validar siembra, variedad y riego sin inferir ausentes, rechazar IDs ajenos y uniones multiplicadas, y publicar conflictos sin elegir según etiquetas. Conservar normalización y original. La ausencia produce un registro explícito vacío; no bloquea ninguna ejecución pública.

El registro en esta fase es descriptivo y permite preparar futuras ventanas agronómicas. La información nueva no modifica el catálogo congelado. Alternativa descartada: inferir variedad o siembra por ubicación o verdor como si estuvieran observadas.

### 8. Catálogo y controles pareados

La familia GPR conserva el pipeline original de selección/imputación/escalado y parámetros 1/5; la segunda familia es ElasticNet con parámetros 0.05/0.2 del proyecto. Representaciones: `monthly_40_10` y `whittaker_40_10`, incluyendo la representación activa. Misma búsqueda para todas las parejas. Las fuentes de base tienen dos opciones, oficial sola u oficial+NASA, con admisión NASA decidida internamente; SIAP no entra al catálogo nuevo porque no está admitida en la activa y evaluarla ampliaría otra hipótesis. F00-ACT conserva su política histórica completa, incluido el diagnóstico SIAP, como control recuperado. No copiar la selección final ajustada sobre todas las etiquetas como si fuera selección independiente de cada fold.

F00 utiliza perfil vacío y calidad compartida. F01 añade D; F02 añade H; F03 usa M; F04 usa I. F05 selecciona internamente entre los perfiles viables vacío/D/H/M/I con esas mismas familias y parámetros; los perfiles ausentes se excluyen únicamente por reglas de viabilidad sin etiquetas. Las medias global y regional son referencias. Hay como máximo 82 candidatos únicos para el combinado (cinco perfiles × ocho configuraciones × dos opciones de fuentes de base + dos referencias), dentro del límite de 160 de la capacidad vigente. La información NASA indispensable para definir D/M/I conserva su rol declarado aunque se excluyan sus columnas históricas de base. Contar también los ajustes reales; candidatos únicos no equivalen a número de entrenamientos.

La alternativa de usar solo la configuración ganadora de toda la campaña para cada validación se descarta: reutilizaría decisiones elegidas con las etiquetas externas. La búsqueda acotada puede empeorar frente a la histórica; F00 hace visible ese efecto. Compartir representaciones, familias, datos y reglas entre F00 y variantes permite medir el aporte incremental aunque F00 no reproduzca el error de la activa.

Particiones principal-5, balanceado-4 y rotado-45-5 se copian verificadas por ID; 138 etiquetas y 59 consultas no cambian. Toda normalización, imputación, selección y admisión usa entrenamiento de cada nivel. Los resultados externos no eligen calendario, fuente, perfil final ni pesos.

### 9. Ejecución, recuperación y elegibilidad

Antes del primer ajuste congelar código/dependencias, fuentes y hashes, soporte, variables, catálogo, semillas, particiones, presupuesto y criterios. La auditoría no recibe rendimientos; los metadatos oficiales de identidad y geometría sí. Las pruebas sintéticas y una recuperación mínima preceden a la congelación, sin producir métricas predictivas reales.

Ejecutar F00-ACT/F00 y las variantes viables; registrar no viables con motivo. F05 es el único elegible. Aplicar todos los criterios del delta `yield-model`: reducción de 2%, razones y protección estatal frente a regional y activa, tres esquemas completos, controles y recuperación. Además exigir al menos un bloque nuevo efectivamente utilizado en el modelo final; volver al respaldo no es una mejora temporal.

Limitar cada ejecución principal a seis horas y 6 GiB de memoria medida; un preflight registrará memoria, ajustes previstos y condiciones de interrupción antes de entrenar. Conservar parciales y estado incompleto si se excede un límite, sin omitir folds para cerrar. Reanudar solo con las mismas versiones/configuración y paquetes íntegros; nunca sobrescribir una ejecución completada.

Cada ejecución completada tendrá modelos/contratos, OOF por esquema, métricas globales/estatales, diferencias pareadas, selección interna, fuentes disponibles/usadas, 59 consultas y verificación en proceso nuevo con red bloqueada. Los controles históricos se recuperan a 1e-10 y las métricas nuevas se recalculan con la misma tolerancia. Activación, despliegue y envío quedan falsos. La reutilización de 2025 es evidencia de desarrollo, sin intervalos nuevos ni prueba de otra campaña.

## Risks / Trade-offs

- [Catálogo público accesible pero bandas inaccesibles o excesivas] → muestra de integridad, recorte y límites previos; H no viable sin bloquear D.
- [Más soporte por intervalos largos oculta eventos breves] → publicar duración y cobertura; no afirmar semanas exactas de pérdida ni comparar cobertura como prueba fisiológica.
- [Cambio de método o calidad parece mejora de datos] → publicar F00−activa y comparar cada perfil con su pareja equivalente.
- [Series regionales compartidas dominan el contraste] → conservar identidad de celda, umbrales sin duplicación climática y resultados separados por esquema/estado.
- [Fuente diaria desagregada o revisada retrospectivamente] → declarar método y fecha de disponibilidad; no interpretar rachas como observaciones locales ni validar un pronóstico histórico.
- [Muestra pequeña y búsqueda repetida] → catálogo acotado, decisión interna, resultado negativo recuperable y advertencia de campaña única.
- [Metadatos opcionales modifican una ejecución cerrada] → registro descriptivo separado y protocolo nuevo para cualquier evaluación predictiva futura.

## Migration Plan

Apply creará únicamente la fase experimental y sus recibos. La aplicación y sus tablas continuarán usando sus contratos actuales. No hay migración de producción en este cambio. Un fallo se conserva con su evidencia y no requiere restaurar la activa porque no se modifica; discrepancias de hashes bloquean el cierre y se investigan sin reescribir expectativas.

Al terminar se presentarán resultados, fuentes admitidas/excluidas y elegibilidad. Activar un candidato, ampliar el presupuesto/proveedor o incorporar variables agronómicas requiere una decisión posterior y otro alcance registrado. La sincronización de especificaciones y archivo se realizan mediante el flujo OpenSpec posterior.
