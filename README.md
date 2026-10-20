# AgroCebada 2026

**Interfaz oficial:** [AgroCebada · Explorar parcelas](https://agrocebada-2026.leonforce033.workers.dev/), publicada en Cloudflare Workers Static Assets. Código de la interfaz en [`frontend/`](frontend/README.md), con React, TypeScript y Vite.

Estimación retrospectiva del rendimiento de 197 parcelas de cebada de Hidalgo, Tlaxcala y Puebla, campaña 2025. Incluye modelos guardados, 138 predicciones de validación fuera de pliegue y las 59 predicciones oficiales descargables. La web consulta una exportación estática verificada del modelo; no reentrena ni ejecuta Python en Cloudflare.

## Abrir la interfaz localmente

Con Node.js 24 y npm, desde la raíz:

```sh
npm --prefix frontend ci
npm run dashboard
```

Abrir la dirección local indicada en la terminal. Para compilar: `npm run dashboard:build`. La salida es `frontend/dist/`. Consultar la [guía de uso](docs/app-guide.md) y la [guía de despliegue en Cloudflare](docs/deployment-cloudflare.md).

## Verificar el modelo y los datos

Con Python 3.12 y un entorno virtual activo:

```sh
python -m pip install -r requirements.txt
python -m agrocebada.cli verify
python -m pytest -q tests experiments/estratificacion-pyr-20261018/tests experiments/fisiologia-siniestros-20261018/tests
```

Si cambian los artefactos científicos, regenerar los datos de la web antes de compilar:

```sh
python scripts/export_react_dashboard.py
npm run dashboard:build
```

La comprobación **Cloud readiness** de GitHub Actions verifica los modelos y las pruebas en Ubuntu/Python 3.12, y compila el frontend oficial. No publica automáticamente.

## Modelo y límites

El **Ensamble Maestro Integral E12**, procedente del commit `32a6d2116e480c9388b9024faa300d1a48ee075d` del proyecto original, tiene **MAE 0.339942 t/ha**, **RMSE 0.481150 t/ha** y **R² 0.678118** sobre 138 parcelas, con cinco grupos estratificados por estado. Consulta estimaciones precalculadas para las parcelas oficiales e intervalos adaptativos por estado. Se conserva el modelo independiente «Solo datos del reto» para verificación por consola.

E12 utiliza señales del ciclo completo de 2025: sus resultados son retrospectivos. No validan campañas futuras, predicción anterior a cosecha ni decisiones crediticias. Las etiquetas del test oculto no se conocen. La interfaz distingue los esquemas de validación y no atribuye al ensamble explicaciones de su modelo base. Detalles en [la actualización E12](docs/model-update-e12.md).

## Ruta de auditoría

| Ruta | Contenido |
|---|---|
| `frontend/` | Interfaz oficial, datos exportados, contornos, descargas y medios publicados |
| `src/agrocebada/` | Preparación, variables, entrenamiento, inferencia y verificación |
| `tests/` | Pruebas científicas, de exportación y de geometría |
| `data/processed/`, `data/external/` | Datos procesados y fuentes externas verificadas |
| `artifacts/` | Modelos, contratos con hashes, predicciones y resultados de validación |
| `experiments/` | Investigaciones del equipo, con código, pruebas y resultados E01–E12 |
| `openspec/` | Especificaciones y evidencia de decisiones |
| `docs/`, `output/pdf/` | Documentación, procedencia, informe del equipo y auditoría |

Las versiones de las bibliotecas del modelo y los hashes de código, datos y modelos se verifican exactamente; se permiten parches dentro de Python 3.12. Streamlit permanece en las dependencias únicamente porque los contratos guardados verifican su versión. Su aplicación, configuración, estilos y pruebas de interfaz se retiraron. Véase [el registro de limpieza](docs/repository-cleanup.md).

Los originales se conservan en `DataSet/`, la única ruta usada para reproducir la preparación. La consulta y las pruebas con artefactos preparados no requieren volver a procesarlos. Consultar [reproducción local](docs/local-reproduction.md). El contexto científico del README anterior está en [docs/project-background.md](docs/project-background.md); el informe del equipo está en `output/pdf/Reporte_AgroCebada_2026.pdf` y la revisión documental en `output/audit/`.

Integrantes: Leonardo Alvarez Gonzalez, Ángel de Jesús Elvis Gutiérrez Pacheco y Diego Cannata Cárdenas. Aportaciones en `docs/team-contributions.json`.
