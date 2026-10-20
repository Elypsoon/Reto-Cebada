# Entrega de la interfaz oficial y limpieza

La interfaz oficial está en `frontend/` y se publica en [Cloudflare](https://agrocebada-2026.leonforce033.workers.dev/). Esta rama integra la limpieza y la auditoría sobre la rama de experimentos que contiene E12.

## Estructura para revisión

- Una única carpeta por función: `src/`, `tests/`, `frontend/`, `experiments/`, `docs/` y `output/`.
- `DataSet/` es la ubicación canónica de los originales. La reproducción no requiere clonar este repositorio dentro de sí mismo ni crear `Reto-Cebada/DataSet`.
- `output/pdf/Reporte_AgroCebada_2026.pdf` conserva el informe del equipo.
- `output/audit/` incorpora seis documentos de auditoría y comprobaciones. Son material de revisión, no sustituyen la evaluación oficial.
- El contexto científico del README anterior se conserva en [project-background.md](project-background.md).

## Limpieza aplicada

Se retiran la aplicación, la configuración y las pruebas de Streamlit; las dos copias de la guía local; y cinco auxiliares ligados a cambios archivados o a manifiestos que ya no forman parte del arranque. Las instrucciones vigentes están en el README, [app-guide.md](app-guide.md), [local-reproduction.md](local-reproduction.md) y [deployment-cloudflare.md](deployment-cloudflare.md).

Se conservan todas las investigaciones y los datos originales del colega. No se reintroducen los dos PDF retirados en el commit de limpieza `0529caf`. Los entornos, cachés, grabaciones locales y copias anidadas quedan fuera de los nuevos archivos.

## Compatibilidad y trazabilidad

El código de inferencia y los contratos incorporan los ajustes de portabilidad usados por la interfaz oficial. La ruta de originales se unifica en `DataSet/`. Se actualizan únicamente los metadatos de código y los hashes de los dos modelos serializados; no se ajusta ningún estimador. La igualdad exacta de las estimaciones e intervalos de las 197 parcelas en ambas rutas se registra en `artifacts/cloudflare-delivery-compatibility.json`.

La exportación del frontend se regenera desde estos contratos para que los hashes publicados en los datos correspondan a los artefactos de esta rama. Los CSV de las 59 predicciones mantienen sus bytes originales. El exportador lee el catálogo único de asignación de videos en `frontend/public/media/parcel-videos/assignment.json`.

Streamlit permanece fijado en las dependencias porque los contratos históricos verifican su versión. No se inicia una aplicación Streamlit.

## Verificación

Consultar el pull request para los resultados de verificación de ambos modelos, pruebas del proyecto y de las dos investigaciones de octubre, exportación de las 197 parcelas y compilación de la interfaz.
