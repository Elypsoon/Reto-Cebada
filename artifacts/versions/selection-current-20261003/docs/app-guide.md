# Consulta local de AgroCebada

Abra una terminal en la raíz del proyecto y ejecute:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra `http://127.0.0.1:8501`. La aplicación escucha únicamente en la computadora local. Con los artefactos preparados, la consulta e inferencia funcionan sin conexión: no requieren servicios satelitales, API climática, mapas externos ni reentrenamiento.

1. En «Consultar parcelas», filtre estado, municipio o conjunto. Busque por identificador o elija un punto del mapa y pulse «Abrir parcela elegida en el mapa».
2. La ficha muestra superficie y, cuando está disponible, rendimiento observado. Pulse «Calcular rendimiento estimado» para ejecutar el modelo guardado. Consulte rendimiento t/ha, producción total t y versión/corte. Descargue la ficha si la necesita.
3. Cambie sensor y umbral de nube para revisar observaciones originales, utilizables y reconstrucción. Las lagunas impiden presentar fases válidas. VI6T se muestra como índice; el pico aproximado no identifica floración exacta. Las coberturas limitadas de topografía se avisan por parcela.
4. «Validación» presenta errores espaciales globales y por estado, referencias, familias de modelos e información sobre intervalos. Las 59 etiquetas ocultas no están disponibles para evaluación local.
5. «Fuentes» muestra procedencia y admisión de los candidatos externos en el ajuste final. El selector de modelo permite abrir expresamente el artefacto oficial independiente.
6. «Descargar las 59 predicciones» siempre entrega el conjunto oficial completo, incluso si la consulta está filtrada. Descargar una ficha tiene un alcance distinto.

Si aparece «No se pudo cargar esta versión», conserve el mensaje y restaure código, dependencias, tablas y modelo del mismo paquete. No cambie columnas ni elimine una fuente requerida para forzar la carga. `python -m agrocebada.cli verify` diagnostica compatibilidad y reproducción. Para regenerar desde los originales, siga README; no mezcle una preparación nueva con un modelo anterior.

Los resultados son estimaciones retrospectivas de 2025. No se presentan como pronóstico anterior a cosecha, asesoramiento causal de manejo ni dictamen de crédito. Una consulta vacía pide ampliar filtros; no crea parcelas o predicciones ficticias.
