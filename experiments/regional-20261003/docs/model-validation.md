# Fase de selección robusta con corrección regional

Promoción rechazada: se conserva la versión vigente íntegra. Ejecución regional-20261003; semilla 2026; corte 2025-10-31. El nuevo RMSE principal es 0.749458 t/ha frente a 0.764053 previo y 0.743976 de la media regional. Cambio frente a la selección previa: 1.91% de reducción. La comparación histórica usa los mismos identificadores, etiquetas y folds; las otras particiones tienen sus propias referencias.

## Protocolo y límites

Política y particiones congeladas antes de entrenar. Hash de política: 71353aead0fc1dd2a87e01444fb34f349ad4f9736d0e65afcd68fa638c94c099. Hay 26 candidatos oficiales: ocho directos, dieciséis correcciones regionales con intensidad 0.5/1 y dos medias. Solo GPR y CatBoost, representaciones monthly_20_10 y whittaker_20_10. Cuatro promedios uniformes; no se optimizan pesos continuos. Seis ablaciones externas sobre los dos ganadores oficiales: NASA, DGSIAP y ambas. Cada opción se compara con su pareja sin fuentes y con la referencia. La admisión interna requiere reducción RMSE ≥2%, mejora en dos folds y deterioro MAE regional ≤10% para n≥10.

Las tres evaluaciones reutilizan las mismas 138 etiquetas. No son 414 observaciones independientes, un test nuevo, validación temporal ni evaluación oficial. La grilla no se amplió después de observar resultados. Los diagnósticos de GPR y CatBoost no sustituyen retrospectivamente la selección.

## Comparación por esquema

| esquema | RMSE selección | RMSE oficial | RMSE regional | razón selección/regional |
| --- | --- | --- | --- | --- |
| principal-5 | 0.7495 | 0.7563 | 0.7440 | 1.0074 |
| balanceado-4 | 0.7694 | 0.7644 | 0.7442 | 1.0340 |
| rotado-45-5 | 0.7492 | 0.7492 | 0.9119 | 0.8215 |

## Decisión de promoción

| condición | cumple |
| --- | --- |
| three_valid_schemes | True |
| principal_gain_2pct | False |
| at_least_two_gains | False |
| mean_ratio_098 | True |
| none_above_105 | True |
| regional_protection | False |
| verification | True |

Razón media de RMSE: 0.954283. La ruta oficial también fue contrastada: promoción rechazada. Requisitos: principal ≤0.98, dos de tres razones ≤0.98, media ≤0.98, ninguna >1.05, protección regional y verificaciones completas. Los motivos individuales permanecen en promotion.json y promotion-official.json.

## Resultados por estado

| esquema | estado | n | MAE selección | MAE regional | razón MAE | RMSE selección |
| --- | --- | --- | --- | --- | --- | --- |
| principal-5 | Hidalgo | 36 | 0.8171 | 0.9351 | 0.8738 | 0.9118 |
| principal-5 | Puebla | 71 | 0.4371 | 0.4149 | 1.0535 | 0.6192 |
| principal-5 | Tlaxcala | 31 | 0.7056 | 0.5000 | 1.4113 | 0.8105 |
| balanceado-4 | Hidalgo | 36 | 0.8863 | 0.9351 | 0.9478 | 0.9791 |
| balanceado-4 | Puebla | 71 | 0.4152 | 0.4157 | 0.9987 | 0.6149 |
| balanceado-4 | Tlaxcala | 31 | 0.7049 | 0.5000 | 1.4098 | 0.8100 |
| rotado-45-5 | Hidalgo | 36 | 0.7209 | 0.8812 | 0.8180 | 0.8306 |
| rotado-45-5 | Puebla | 71 | 0.4100 | 0.3779 | 1.0850 | 0.5908 |
| rotado-45-5 | Tlaxcala | 31 | 0.8595 | 1.2742 | 0.6746 | 0.9475 |

Las métricas por tercil de área y por fold, predicciones pareadas, frecuencias de selección/admisión y variables elegidas se conservan por esquema. El dataset evaluado mantiene 197 identificadores, 138 etiquetas y 59 casos ocultos; hash de datos dd53624fd4069eab5193c031fc1bc2f5c11549218c597d5b197f71d7f659da4e.

## Diagnóstico y originales

Hidalgo aportaba 54.2% del error cuadrático previo y aporta 38.6% del nuevo esquema principal. Se revisaron 10 casos de mayor error contra CSV y geometría originales. No se demostraron discrepancias de rendimiento, superficie, estado o municipio; no se corrigieron ni retiraron etiquetas por residuo elevado. Se verificaron 176 hashes de originales. Las uniones parcelarias, calidad utilizable por sensor, faltantes y cobertura de rásteres están en diagnostic-*. Municipios con n<10 se marcan como muestra pequeña: su error es descriptivo.

## Intervalos y sensibilidad

| esquema | estado | n | valid_n | coverage | mean_width |
| --- | --- | --- | --- | --- | --- |
| principal-5 | global | 138 | 138 | 0.8768 | 2.8674 |
| principal-5 | Hidalgo | 36 | 36 | 0.6944 | 2.9426 |
| principal-5 | Puebla | 71 | 71 | 0.9155 | 2.1928 |
| principal-5 | Tlaxcala | 31 | 31 | 1.0000 | 4.3251 |
| balanceado-4 | global | 138 | 138 | 0.8623 | 2.8977 |
| balanceado-4 | Hidalgo | 36 | 36 | 0.6944 | 2.9171 |
| balanceado-4 | Puebla | 71 | 71 | 0.8873 | 2.2658 |
| balanceado-4 | Tlaxcala | 31 | 31 | 1.0000 | 4.3224 |
| rotado-45-5 | global | 138 | 138 | 0.8986 | 2.8515 |
| rotado-45-5 | Hidalgo | 36 | 36 | 0.9167 | 3.0755 |
| rotado-45-5 | Puebla | 71 | 71 | 0.9718 | 2.9584 |
| rotado-45-5 | Tlaxcala | 31 | 31 | 0.7097 | 2.3465 |

Nominal 90%, mínimo de calibración 25. Intervalos de la ruta enriquecida disponibles según cobertura principal ≥85% y modelo final compatible. El centro procede de un ajuste separado; las etiquetas de calibración no entran en selección. La cobertura global no garantiza cobertura regional: Hidalgo principal alcanza 69.4%.

Leave-one-state-out y buffer de 1 km evaluaron la ruta oficial congelada. El buffer usa distancia entre polígonos en UTM, excluyendo físicamente vecinos a menos de 1 km. Escenarios evaluados: 6; inviables: 2, con razón, conjuntos y tamaños registrados en stress.json. No se retiraron escenarios para mejorar la decisión principal.

## Modelos finales y reproducción

El ajuste experimental final usa gpr direct; pesos [1.0]; fuentes del rendimiento: nasa. Cada componente conserva medias, escala, columnas, intensidad, fuentes y hashes. Referencia más corrección ponderada reproduce la predicción; GPR muestra sensibilidades individuales no aditivas. Se mantienen modelos oficial/enriquecido separados y 59 predicciones por ruta sin cotas artificiales. Producción = rendimiento por superficie.

## Siguiente evidencia necesaria

1. Rendimientos parcelarios de una nueva campaña, medidos y con unidades/área verificadas. Confirmar generalización temporal en etiquetas no utilizadas para desarrollar la política. Disponibilidad: pendiente de obtención y verificación.
2. Fechas de siembra/cosecha, variedad, riego, fertilización y manejo por parcela. Explicar variación parcelaria y alinear ventanas fenológicas. Disponibilidad: pendiente de obtención y verificación.
3. Protocolo de medición, humedad/calidad de cosecha y fuente del rendimiento. Resolver cuantización y discrepancias con evidencia primaria. Disponibilidad: pendiente de obtención y verificación.
4. Más etiquetas verificadas de Hidalgo y municipios con pocos casos. Evaluar cobertura y errores regionales con mayor soporte. Disponibilidad: pendiente de obtención y verificación.

No se ha desplegado ni enviado la versión experimental al organizador. La restauración usa el paquete completo de la versión anterior, no la modificación de hashes de contratos incompatibles.
