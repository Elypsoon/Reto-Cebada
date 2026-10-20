# AgroCebada · Dashboard React

Interfaz de consulta de las 197 parcelas del reto: mapa geográfico, búsqueda y filtros, fichas de rendimiento e intervalos, curvas NDVI, validación del modelo y descargas CSV.

**Versión publicada:** [Explorar parcelas](https://agrocebada-2026.leonforce033.workers.dev/).

## Ejecutar localmente

Se necesita Node.js **22.12 o posterior** y npm. Desde la raíz del repositorio:

```sh
npm --prefix frontend ci
npm run dashboard
```

Abrir la dirección que muestra la terminal, normalmente `http://127.0.0.1:5173`. También se puede trabajar desde esta carpeta con `npm ci` y `npm run dev`.

La interfaz consulta archivos estáticos incluidos en `public/`; no necesita un servidor Python, claves API ni volver a entrenar el modelo. Los fondos cartográficos Satélite y Relieve requieren internet.

## Compilar y previsualizar

```sh
npm run dashboard:build
npm --prefix frontend run preview
```

La compilación ejecuta la detección de medios, la comprobación TypeScript y Vite. El resultado está en `frontend/dist/` y puede alojarse como un sitio estático en la raíz de un dominio. Las rutas de datos y recursos empiezan por `/`; para servir bajo un subdirectorio hay que adaptar esas rutas.

## Datos incluidos y procedencia

La exportación conserva el **Ensamble Maestro Integral E12** del commit [`32a6d21`](https://github.com/Elypsoon/Reto-Cebada/commit/32a6d2116e480c9388b9024faa300d1a48ee075d): MAE **0.339942 t/ha**, RMSE **0.481150 t/ha** y R² **0.678118**, calculados sobre 138 predicciones fuera de pliegue con cinco grupos estratificados por estado. Es una estimación retrospectiva de la campaña 2025 con señales del ciclo completo; las curvas visibles corresponden a abril–octubre.

- `public/data/parcels.json`: 197 fichas con estimaciones e intervalos.
- `public/data/parcels.geojson`: los 197 contornos originales reproyectados a WGS84, sin simplificación.
- `public/data/curves/`: una curva por parcela, con Sentinel-2 y Planet.
- `public/data/model.json`: identidad, métricas, resultados por estado, 138 puntos de validación, alcance y hashes de los artefactos utilizados en la exportación.
- `public/data/map-provenance.json`: procedencia, hash del GeoParquet original, CRS y operación de exportación.
- `public/downloads/`: las 59 predicciones oficiales, con y sin intervalos.

Los datos son una instantánea verificada procedente del proyecto del dashboard. Cambiar los modelos Python del repositorio no actualiza automáticamente estos archivos. Al actualizar la exportación deben mantenerse sincronizados fichas, curvas, geometrías, métricas, intervalos, CSV y hashes; no modificar las cifras de forma manual. Los hashes del modelo y contrato identifican los artefactos adaptados para el dashboard y pueden diferir de los del entorno Python original.

Antes de entregar esta rama se verificó la igualdad de estimaciones, intervalos, descargas, métricas y hashes contra el predictor guardado utilizado en la exportación, además de la igualdad geométrica de los 197 contornos. La rama parte de `cambios-experimentos-2026-10-17` (`2e078dc`) y añade la interfaz sin sustituir el código ni los artefactos científicos existentes.

## Interfaz y accesibilidad

El mapa usa MapLibre GL JS con Esri World Imagery y OpenTopoMap, con sus atribuciones visibles. Buscar por ID completo o numérico, municipio o estado; también se puede seleccionar el polígono o su marcador. La ficha se abre junto al mapa y se apila en pantallas pequeñas. Sensor, curva y tabla de valores mantienen la misma selección.

La navegación conserva la parcela en el fragmento de URL y admite atrás/adelante. Hay controles de zoom, selección mediante búsqueda y teclado, tablas para las gráficas y compatibilidad con movimiento reducido. Los valores observados se distinguen de las etiquetas ocultas. El modelo no dispone de contribuciones por variable que reproduzcan el ensamble; la interfaz explica ese límite.

## Recursos audiovisuales

Se incluyen los 16 videos originales y su asignación a las 197 parcelas en `public/media/parcel-videos/`. La vista inmersiva actual no reproduce videos; los archivos se conservan para reutilizarlos. `scripts/sync-media.mjs` detecta un MP4 o WebM por familia y genera `files.json` al iniciar o compilar, conservando los nombres originales. Más detalles en [la guía de medios](public/media/README.md).

## Despliegue en Cloudflare

`wrangler.jsonc` configura Workers Static Assets sobre `dist/`, con el nombre de servicio `agrocebada-2026`. Para publicar, autenticar Wrangler desde `frontend/`, comprobar la cuenta y el nombre de servicio deseados, y ejecutar desde la raíz:

```sh
npm run dashboard:deploy
```

La cuenta se selecciona mediante la sesión de Wrangler; no se incluyen credenciales ni una cuenta fijada. Para validar sin publicar, compilar y ejecutar `npm --prefix frontend run deploy:check`. No hay despliegue automático desde GitHub.

`public/_headers` configura la caché y `Content-Type: application/geo+json` para los contornos; conservarlo o reproducir esos encabezados al usar otro proveedor. La navegación usa fragmentos de URL y los archivos de datos ausentes deben devolver 404.
