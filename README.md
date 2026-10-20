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

### Inferencia programática y comandos de consola (CLI)

Para consultar predicciones interactivamente en Python:

```python
from agrocebada.inference import Predictor

# Cargar el predictor oficial seleccionado (Ensamble Maestro E12)
predictor = Predictor("selected")

# Estimar rendimiento (t/ha), producción (t) e intervalos de calibración al 90%
resultado = predictor.predict(["AGC_003", "AGC_011", "AGC_025"])
print(resultado[["ID_POLIGONO", "RENDIMIENTO_T_HA", "INTERVAL_LOW", "INTERVAL_HIGH"]])
```

Comandos disponibles en la herramienta de línea de órdenes (`agrocebada.cli`):
- `python -m agrocebada.cli verify`: Comprueba contratos criptográficos (SHA-256), reproduce exactamente las 59 predicciones oficiales y verifica métricas fuera de pliegue.
- `python -m agrocebada.cli audit`: Audita identificadores, CRS, geometrías y tablas maestras originales en `DataSet/`.
- `python -m agrocebada.cli prepare`: Procesa y sincroniza series temporales de Sentinel-2, PlanetScope y clima diario.
- `python -m agrocebada.cli train`: Ejecuta la búsqueda de modelos, evaluación por bloques espaciales y políticas de selección.

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

## Integrantes y aportaciones

- **Ángel de Jesús Elvis Gutiérrez Pacheco** (*Modelado, Experimentación y Estrategia Analítica*): Diseño y formulación de la arquitectura predictiva; concepción, ejecución y registro de las fases experimentales; análisis de métricas de desempeño y definición de la representación espacial y matemática de la información. Líder y organizador del proyecto.
- **Leonardo Álvarez González** (*Desarrollo Web, Diseño UI/UX y Producción Audiovisual*): Diseño de la interfaz de usuario (UI/UX) y desarrollo de la aplicación web; estructuración visual de los componentes de consulta interactiva y guionización, grabación y edición del video demostrativo del proyecto.
- **Ángel Gabriel Aguilar Saldívar** (*Estadística de Datos y Validación Matemática*): Modelado estadístico y análisis de dispersión; formulación, revisión y auditoría rigurosa de las ecuaciones matemáticas y funciones de pérdida (Huber, Kriging y calibración de intervalos) en el código y en el reporte técnico.
- **Iván Pérez Sánchez** (*Auditoría Técnica, Investigación y Fuentes Externas*): Revisión técnica y auditoría de consistencia del reporte; investigación agronómica y bibliográfica para la selección de variables biofísicas; búsqueda, control de calidad e integración de fuentes de datos satelitales y climáticos externos.
- **Diego Cannata Cárdenas** (*Auditoría de Dashboard y Aseguramiento de Calidad de Datos*): Aseguramiento de calidad (QA) y auditoría de la plataforma interactiva; verificación de la fidelidad e integridad en la representación de polígonos, métricas y series temporales; validación del módulo de análisis y presentación de datos.

Detalles y metadatos complementarios en [`docs/team-contributions.json`](docs/team-contributions.json).
