# Consultar AgroCebada

Abrir la [interfaz oficial de Cloudflare](https://agrocebada-2026.leonforce033.workers.dev/). Para abrirla localmente, desde la raíz:

```sh
npm --prefix frontend ci
npm run dashboard
```

Usar la dirección que indica la terminal. No se necesita iniciar Python para consultar los resultados ya exportados. Los fondos Satélite y Relieve requieren internet; las tipografías, contornos, curvas y resultados están incluidos en la aplicación.

1. En **Explorar parcelas**, buscar por identificador (`AGC_071` o `71`), municipio o estado. También se puede filtrar por estado y seleccionar un contorno en el mapa.
2. La selección acerca el mapa y abre la ficha con superficie, rendimiento, producción e intervalo. Los valores proceden de la exportación verificada del modelo E12. El rendimiento observado solo aparece cuando existe una etiqueta conocida.
3. Debajo de la ficha, consultar la evolución del cultivo y cambiar entre Sentinel-2 y Planet. La tabla comparte el sensor seleccionado y permite revisar los valores y el método de la curva. La vista actual no reproduce los videos conservados en el archivo de medios.
4. **Modelo y validación** presenta MAE, RMSE, R² y resultados por estado sobre 138 predicciones fuera de pliegue. E12 se evalúa con cinco grupos estratificados por estado; el test oculto carece de etiquetas disponibles.
5. **Fuentes y metodología** explica la procedencia y los límites. Sus enlaces permiten descargar las 59 predicciones oficiales, con y sin intervalos, independientemente de los filtros del mapa.
6. Cerrar la ficha o pulsar **Ver territorio** devuelve el encuadre general. La URL conserva la selección y permite usar atrás y adelante.

La preferencia de movimiento reducido desactiva las animaciones principales. Las gráficas incluyen tablas y la búsqueda permite seleccionar sin depender de los puntos del mapa.

Los resultados son retrospectivos de 2025. No son pronósticos anteriores a cosecha ni explicaciones causales del manejo. El ensamble E12 no incorpora contribuciones por variable que reproduzcan exactamente sus estimaciones. La [guía de reproducción](local-reproduction.md) documenta la verificación científica y la [guía de despliegue](deployment-cloudflare.md) explica cómo actualizar la publicación.
