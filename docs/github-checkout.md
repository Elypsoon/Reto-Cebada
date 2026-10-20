# Revisar un checkout limpio

La rama contiene la interfaz oficial, los originales en `DataSet/`, las investigaciones del equipo y los artefactos preparados. No se necesita un repositorio anidado.

1. Instalar Python 3.12 y el entorno de `requirements.txt` según [local-reproduction.md](local-reproduction.md).
2. Ejecutar `python -m agrocebada.cli verify` y las pruebas indicadas en el README.
3. Instalar el frontend con `npm --prefix frontend ci` y compilar con `npm run dashboard:build`.
4. Ejecutar `npm run dashboard` para inspeccionar la interfaz. Para publicar, seguir [deployment-cloudflare.md](deployment-cloudflare.md).

Las guías de uso están en [app-guide.md](app-guide.md). El informe del equipo se conserva en `output/pdf/Reporte_AgroCebada_2026.pdf`, y la revisión documental y sus comprobaciones, en `output/audit/`. El contexto científico previo está en [project-background.md](project-background.md).
