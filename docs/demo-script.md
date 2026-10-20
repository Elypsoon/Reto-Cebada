# Demo de hasta cinco minutos

Duración objetivo: 4 minutos 40 segundos. Abrir la [interfaz oficial](https://agrocebada-2026.leonforce033.workers.dev/) y comprobar que carga el mapa antes de comenzar. Los resultados publicados ya están exportados; no se entrena durante la demo.

| Tiempo | Acción y mensaje |
|---|---|
| 0:00–0:35 | Presentar el problema: estimar t/ha por parcela en tres estados. Aclarar que E12 utiliza señales del ciclo completo de 2025 y que la consulta es retrospectiva. |
| 0:35–1:15 | Mostrar las 197 parcelas, filtrar un estado y buscar `71`. Seleccionar AGC_071 y mostrar su contorno y ficha. |
| 1:15–2:00 | Explicar rendimiento, intervalo, superficie y producción = rendimiento × superficie. Diferenciar valor observado de etiqueta oculta. La web lee estimaciones verificadas del modelo guardado. |
| 2:00–2:40 | Mostrar la evolución del cultivo, cambiar sensor y revisar la tabla de valores. Una curva reconstruida no identifica por sí sola la floración exacta. |
| 2:40–3:35 | Abrir Modelo y validación: MAE 0.340 t/ha, RMSE 0.481 t/ha y R² 0.678 sobre 138 predicciones fuera de pliegue, con cinco grupos estratificados por estado. Distinguir esta validación del test oculto. |
| 3:35–4:15 | Abrir Fuentes y metodología. Explicar procedencia y límites y descargar las 59 predicciones oficiales. |
| 4:15–4:40 | Mostrar la ruta de auditoría del README: código, contratos, hashes, datos y pruebas. Cerrar con límites: una campaña, pocas etiquetas, sin validación futura ni uso directo para aprobar crédito. |

Consultar [app-guide.md](app-guide.md) para el recorrido y [model-update-e12.md](model-update-e12.md) para la trazabilidad del modelo.
