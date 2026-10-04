# Proposal

## Why

El reto exige estimar el rendimiento de 59 parcelas y ofrecer una aplicación funcional a partir de solo 138 etiquetas del ciclo abril–octubre de 2025. Las dos investigaciones aportan ideas complementarias, pero necesitamos una metodología reproducible que distinga datos verificados, hipótesis agronómicas y fuentes externas realmente utilizables.

## What Changes

- Construir una base trazable de 197 parcelas, con controles de identificadores, geometrías, unidades, calidad satelital y separación oficial entrenamiento/predicción.
- Incorporar como candidatos los datos públicos ya descargados: NASA POWER diario para abril–octubre de 2025 y DGSIAP municipal 2018–2024. Su admisión al modelo requiere controles de calidad y comparación espacial con la versión que usa únicamente los insumos del reto.
- Mantener un modo completo con los datos del reto cuando una fuente externa falle, resulte inadecuada o no demuestre utilidad. SoilGrids, ERA5-Land y estaciones sin series históricas verificadas no serán dependencias de esta versión.
- Transformar las series en variables compactas por parcela, conservando ramas separadas para Sentinel-2, Planet y VI6T de Landsat.
- Comparar referencias simples, regresión regularizada, SVR, CatBoost y GPR reducido mediante validación espacial anidada; admitir ensambles únicamente con evidencia de mejora.
- Producir las 59 predicciones, métricas fuera de muestra, trazabilidad del modelo y una aplicación Streamlit con mapa, curvas, consulta y ejecución de inferencia por parcela.
- Documentar la contribución de cada familia de datos, las limitaciones de las explicaciones y la cobertura empírica de los intervalos, cuando estos sean utilizables.
- El producto inicial estima retrospectivamente el ciclo 2025 usando observaciones hasta el 31 de octubre; un pronóstico anticipado o para años futuros queda fuera de alcance.

## Capabilities

### New Capabilities

- `data-provenance`: inventario, adquisición, calidad y admisión de datos con alternativa basada en los insumos oficiales.
- `parcel-features`: construcción reproducible de variables temporales, ambientales e históricas por parcela.
- `yield-model`: evaluación espacial, selección del modelo, inferencia y exportación del conjunto oficial.
- `parcel-dashboard`: consulta geográfica, visualización y ejecución interactiva del modelo con procedencia y limitaciones visibles.

### Modified Capabilities

Ninguna; no existen especificaciones previas.

## Impact

Se implementará Python en la raíz del proyecto, preservando el repositorio anidado `Reto-Cebada` como fuente. Se prevén pandas, NumPy, scikit-learn, GeoPandas, rasterio, Streamlit y CatBoost; el entorno, dependencias, código y despliegue se crearán en la fase de implementación. Los datos externos, manifiestos y comprobaciones preliminares se conservan en `evidence/` de este cambio; no hay entrenamiento ni aplicación implementados en esta propuesta. El desarrollo inicial será local y la aplicación no necesitará consultar servicios externos para operar con una versión validada de datos.
