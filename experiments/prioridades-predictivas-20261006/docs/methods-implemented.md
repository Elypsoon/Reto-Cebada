# Métodos contrastados

Las ecuaciones siguientes documentan decisiones implementadas del proyecto. Los papers motivan hipótesis; sus resultados no se atribuyen a estas parcelas. Todas las transformaciones aprendidas utilizan únicamente el entrenamiento correspondiente.

## Selección de variables

P01 compara ranking marginal con una lista agronómica fija de 16 variables y con todas las columnas numéricas elegibles. Disponibilidad mínima 50%; imputación mediante mediana de train y exclusión de constantes. La variante sin ranking conserva relaciones no lineales aunque su correlación marginal sea pequeña. Se publican dimensiones y columnas efectivas en los contratos por partición.

## Calendario y tiempo térmico

Para temperaturas diarias NASA verificadas, con base 0 °C y tope 26 °C:

\[
g_d=\frac{\operatorname{clip}(T_{\min,d},0,26)+\operatorname{clip}(T_{\max,d},0,26)}{2},\quad
G(t)=\sum_{d=2025\text{-}04\text{-}01}^{t}g_d.
\]

El eje térmico es G(t)−G(2025-04-01); el calendario usa días desde esa fecha. Los dos controles contienen las mismas covariables, calidad y total GDD. NASA aporta celdas regionales compartidas, no 197 estaciones independientes. No se infieren siembra o antesis.

Los segmentos conservan lagunas mayores que 21 días sin integrarlas. Los tiempos térmicos repetidos se agregan dentro del segmento, sin incrementos artificiales. Las integrales emplean índice×día o índice×grado-día y se normalizan por su eje respaldado. Esta comparación es enriquecida; P06 permanece exclusivamente oficial.

## Proyección funcional

Para cada parcela y rama espectral, se estiman seis coeficientes de B-splines cúbicos sobre fechas realmente observadas:

\[
\widehat c=\arg\min_c\sum_{j\in\mathcal O} w_j[z_j-B(t_j)c]^2+10\lVert D^2c\rVert^2.
\]

Los nudos interiores son 1/3 y 2/3 del calendario de la campaña. La ponderación deriva de nubosidad; fechas sin observación tienen peso cero. Se requiere un mínimo de ocho observaciones y soporte en dos tercios calendario. Los coeficientes son una proyección latente y no reconstruyen curvas fuera de segmentos.

La PCA compartida se aprende con coeficientes válidos de train, al menos 20 parcelas y 50% de disponibilidad por rama. El signo se fija mediante el coeficiente de mayor magnitud. P05 compara dos/tres componentes por rama; P06 fija dos. Los objetos ajustados transforman consultas nuevas sin actualizar la base.

## Modelos jerárquicos

Ridge/GAM ajustan el rendimiento normalizado de train como suma de efecto parcelario y estatal:

\[
\widehat y_i=\mu_{\mathrm{train}}+\sigma_{\mathrm{train}}[f(X_i)+u_{s(i)}],\qquad
\sum_s n_su_s=0.
\]

El ajuste penaliza los coeficientes de f y los efectos u por separado. Penalización estatal infinita elimina u. GAM utiliza bases spline con nudos aprendidos en train y términos centrados. Un estado sin etiquetas recibe exactamente la media global de train, sin efecto estatal ni corrección parcelaria para ese estado: es una regla expresa del diseño, que puede limitar transferencia.

El GPR jerárquico añade covarianza estatal al kernel parcelario:

\[
K_{ij}=k_{\mathrm{Mat\acute ern},\nu=2.5,\ell}(X_i,X_j)
+\tau^2\mathbf1[s(i)=s(j)]+0.15\mathbf1[i=j].
\]

Se contrastan tau²=0/0.25/1 y longitudes 1/5. Los contratos conservan normalización, soporte estatal y descomposición de la predicción en t/ha. El estado ausente sigue la misma regla de media global.

## EBM y modelos fundacionales

EBM compara términos aditivos con dos interacciones fijas: EVI medio×precipitación media y MSAVI tardío×temperatura media tardía. Usa resolución 8/16, ocho bolsas internas, 1000 rondas y early stopping desactivado. Las bolsas utilizan únicamente train.

TabICLv2 y TabPFN-3 se evalúan por separado sobre monthly/whittaker, con checkpoint explícito, ocho estimadores y semilla 2026. Sus preprocesadores usan contexto de train. La recuperación conserva pesos, dependencias y contexto; ninguna configuración opcional entra a P06.

## Selección y lectura de resultados

Cada selección interna vuelve a ajustar bases, imputación, nudos y efectos. Una alternativa requiere reducción RMSE de al menos 2%, mejora en dos folds y protección de MAE estatal. Un fold fallido invalida ese candidato; no se elimina del promedio. Los ensambles son uniformes y predeclarados.

Las predicciones externas se comparan sobre las mismas 138 etiquetas en tres esquemas espaciales. P06 tiene además exigencias frente al control activo oficial y protección regional. Calibración independiente, mínimo 25 etiquetas, nominal 90% y cobertura principal mínima 85% determinan la disponibilidad de intervalos, separadamente de la elegibilidad puntual.

Los contrastes de configuraciones fijas y sus mínimos observados son diagnósticos. No reconfiguran P06 ni convierten estas etiquetas reutilizadas en un test de otra campaña. Véanse evidence-and-coverage.md, mechanism-comparisons.md y priority-results.md para fuentes y resultados.
