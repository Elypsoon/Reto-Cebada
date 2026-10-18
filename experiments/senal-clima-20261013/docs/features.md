# Variables y soporte

Todas las tablas predictivas conservan los 197 IDs oficiales. Abril–octubre de 2025 se divide en 16 intervalos consecutivos de 14 días; el último dura cuatro días. El punto medio real asigna abril–mayo, junio–julio o agosto–octubre. El diagnóstico semanal se conserva exclusivamente como diagnóstico temporal.

| Bloque | Variables por ventana | Unidades y soporte |
| --- | --- | --- |
| D | Lluvia acumulada, máxima racha estimada con lluvia <1 mm/día, percentil 95 de Tmax | mm, días y °C. CHIRPS v3 final diario sat y NASA local; 95% de días válidos y 95% de superficie CHIRPS. Las rachas se interrumpen ante un faltante. |
| H | Señal mediana por intervalo, promediada con peso por duración | Índice adimensional `ndmi_b8a_b11`. Dos fechas únicas por intervalo, 80% de superficie válida por adquisición y al menos dos intervalos/50% por ventana. |
| M | D+H, media de VPD y Tmedia sobre los mismos intervalos válidos de H | kPa y °C regionales. No se extrapolan pares a intervalos sin señal. |
| I | M más VPD×señal, Tmedia×señal y fracción conjunta VPD alto/señal baja | Escalado y cuantiles ajustados solo en cada entrenamiento. VPD usa celdas/intervalos únicos; la señal asigna igual peso total por parcela. Varianza nula produce faltante. |

D necesita al menos 90% de parcelas con sus tres ventanas completas; H, 70%. M/I exigen D y H viables y 70% de parcelas con efectos principales y pares completos. Son umbrales de calidad predeclarados, no umbrales de daño agronómico. No se bajan tras evaluar resultados. H puede ser viable sin D; M/I no.

`Q_signal_support_*`, `Q_signal_dates_*` y `Q_signal_area_*` describen proporción de intervalos, fechas válidas y superficie media. Solo si H es admitido se incorporan como covariables comunes de F00 y sus variantes. Un faltante no representa ausencia de estrés.

`prepare_features.py` construye las tablas y `registry/viability.json` leyendo identidad/geometría y entradas públicas locales; no lee rendimientos. Rechaza auditorías abiertas, fuentes no comprobadas y archivos alterados. CHIRPS diario sat desagrega acumulados pentadales mediante IMERG Late V07: sus rachas son estimaciones regionales, no observaciones meteorológicas de la parcela. NASA también conserva su escala regional. Estos indicadores no demuestran cierre estomático, retención del suelo ni semanas exactas de pérdida de producción.

Estado actual: la lógica está implementada y probada con datos inventados; las tablas nuevas reales y su viabilidad esperan las autorizaciones/auditorías de adquisición. El NDWI original carece de fórmula/bandas comprobadas y no habilita H/I.
