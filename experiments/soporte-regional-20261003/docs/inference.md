# Inferencia y explicaciones

`Predictor` es el único servicio de cálculo utilizado por consola y Streamlit. Carga el pipeline guardado; no entrena, no solicita imágenes ni consulta APIs. Acepta identificadores únicos de las 197 parcelas disponibles. No admite cualquier polígono nuevo sin un proceso compatible de preparación y validación.

Hay dos artefactos independientes: `model_selected.joblib`, resultado del procedimiento de selección interno, y `model_official.joblib`, ajustado únicamente con datos del reto. Los contratos JSON contienen corte 2025-10-31, semilla, configuración temporal, columnas y orden, fuentes requeridas, hashes de tablas/datos/modelo/código y versiones de dependencias. Cambios incompatibles se rechazan con un mensaje; no se sustituye silenciosamente el modelo seleccionado por el oficial. Restaurar una versión implica restaurar su contrato, tablas y código completos.

La descarga usa exactamente los 59 identificadores PREDICCION, ordenados, con dos columnas: `ID_POLIGONO` y `RENDIMIENTO_T_HA`. Se conserva precisión completa. No se aplican límites artificiales del entrenamiento, Tlaxcala o SIAP; valores no finitos o negativos bloquean el cálculo y la exportación. La ficha también entrega superficie y producción total: toneladas = t/ha × ha. El rendimiento observado se distingue del estimado. Predicciones sobre parcelas de entrenamiento sirven para consulta, no como métricas independientes.

Verificar reproducibilidad y métricas guardadas:

```powershell
.\.venv\Scripts\python.exe -m agrocebada.cli verify
```

La verificación reproduce las 59 salidas con tolerancia absoluta 1e-10, comprueba identificadores y recalcula RMSE/MAE/R² desde las 138 predicciones OOF. También exporta `predictions_official_only_59.csv`. El test oculto carece de etiquetas locales: su puntuación no se afirma.

Intervalos nominales 90% se calibran con un grupo separado de al menos 25 etiquetas, repitiendo la selección dentro del resto. Solo se presentan si la cobertura espacial OOF supera 85% y existe calibración final compatible. El estimador calibrado usa menos etiquetas y puede tener un centro distinto del estimador principal. La dependencia espacial y falta de años nuevos impiden prometer cobertura por parcela, estado o campaña futura. GPR sin calibración no constituye un intervalo acreditado.

Para modelos lineales, la explicación es coeficiente por entrada escalada más intercepto. CatBoost usa contribuciones SHAP del modelo guardado, comprobando que contribuciones más base reproducen su salida. En ensambles se ponderan efectos por los pesos del modelo. SVR/GPR muestran sensibilidad al sustituir una variable por su mediana de entrenamiento: esos efectos no son aditivos y no se presentan como SHAP exacto. Contribución predictiva no prueba causalidad, respuesta a una intervención ni garantía crediticia.

Las medias global y regional pueden ser seleccionadas dentro del entrenamiento. La media regional se representa mediante el estado oficial, con media global como base y diferencia regional como contribución; un estado ausente en train utiliza la media global. Los indicadores de estado no incluyen rendimiento de validación. Su contrato registra la familia y las columnas, además del hash de la tabla de parcelas de la que se deriva el estado.

Solo se cargan artefactos locales del paquete del proyecto. La versión corta visible corresponde al hash del modelo; la trazabilidad completa está en el contrato. `integration-check.json` registra la comprobación y las fuentes realmente elegidas para el rendimiento principal.
