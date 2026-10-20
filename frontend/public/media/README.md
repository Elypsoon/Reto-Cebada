# Recursos del dashboard

`map/soil-background.png` es una imagen conceptual de suelo. Los contornos geográficos de las parcelas se encuentran en `../data/parcels.geojson`.

## Archivo de videos

Se conservan los 16 videos originales aportados para el dashboard, uno por carpeta en `parcel-videos/`. Cada nombre de carpeta identifica la familia y la parcela utilizada como referencia. `assignment.json` contiene la asignación completa de las 197 parcelas a esas familias.

La vista inmersiva actual presenta el mapa y las fichas sin reproducir videos. Los clips se incluyen para mantener disponibles los recursos del proyecto.

Para sustituir un clip, colocar un solo archivo MP4 o WebM en su carpeta. Puede conservar su nombre original. Desde la raíz del repositorio, ejecutar:

```sh
npm --prefix frontend run media:sync
```

La herramienta actualiza `files.json`, conserva los nombres y rechaza carpetas con más de un clip para evitar asignaciones ambiguas. También se ejecuta al iniciar o compilar la interfaz. Los 16 videos incluidos utilizan MP4/H.264.
