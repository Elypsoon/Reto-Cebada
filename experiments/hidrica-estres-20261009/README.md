# Evaluación de disponibilidad hídrica y estrés agroclimático

Fase aislada del cambio `disponibilidad-hidrica-y-estres-agroclimatico`. El protocolo, las fuentes y el catálogo están congelados en `registry/frozen-protocol.json`. Esta fase conserva 197 parcelas, 138 etiquetas de desarrollo y 59 consultas, con corte 2025-10-31. Los resultados se publican incrementalmente en [el informe](docs/results.md).

Los bloques G (retención SoilGrids) y S (estrés con NDWI vegetal) quedaron no viables bajo las reglas previas. La auditoría de suelo conserva un recorte WCS a 250 m, con CRS y máscara NoData no comprobados dentro del archivo, y la discrepancia de unidades de la descripción del servicio. La ficha ISO confirma la naturaleza de retención a 33 kPa, pero no basta para validar el conjunto de capas requerido. El diccionario NDWI no confirma bandas ni fórmula. Estas decisiones no prueban inutilidad científica del suelo o del estrés; identifican las comparaciones que no cuentan con entradas admisibles.

Las funciones de extracción, capacidad por estrato, envolventes, soporte semanal e interacciones se implementaron y verificaron con datos sintéticos. En la evaluación real permanecen W01-O, W01-E, W04 y W05, además del control recuperado W00. No se inventan metadatos de variedad, fecha de siembra, raíces o heladas locales.

## Recuperación y verificación

Usar el Python fijado del proyecto, con `PYTHONDONTWRITEBYTECODE=1`, `PROJ_NETWORK=OFF` y `PYTHONPATH` apuntando a `src` de esta fase. Las dependencias efectivas se registran en `registry/preparation-receipt.json`; `requirements.lock` conserva la versión exacta de origen. No instalar dependencias ni modificar los entornos históricos para recuperar un paquete.

Desde la raíz del proyecto, en PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PROJ_NETWORK='OFF'
$env:PYTHONPATH=(Join-Path (Get-Location) 'experiments/hidrica-estres-20261009/src')
.venv/Scripts/python.exe experiments/hidrica-estres-20261009/scripts/offline_worker.py module hydric.run verify W01-O
.venv/Scripts/python.exe experiments/hidrica-estres-20261009/scripts/offline_worker.py module hydric.run verify W01-E
.venv/Scripts/python.exe experiments/hidrica-estres-20261009/scripts/offline_worker.py module hydric.run verify W04
.venv/Scripts/python.exe experiments/hidrica-estres-20261009/scripts/offline_worker.py module hydric.run verify W05
```

Cada ejecución completada conserva modelo, contrato, selección interna, tres vectores OOF, métricas, 59 consultas y paquete de recuperación. La tolerancia es absoluta 1e-10, relativa cero. La recuperación comprueba consultas individuales frente a lotes, hashes, columnas y métricas recalculadas. Los procesos bloquean conexiones IP; los modelos operan con archivos locales.

Los identificadores cerrados no se reutilizan. No ejecutar preparación, adquisición, congelación ni entrenamiento sobre estas rutas para sobrescribirlos. Una nueva fuente o corrección del protocolo requiere otra ejecución y su planificación correspondiente. Los controles históricos usan su código original copiado y permanecen independientes del módulo `hydric`.

## Recibos de evidencia

- `registry/copy-origins.json`, `population-check.json` y `preparation-receipt.json`: aislamiento, identidad y versiones.
- `registry/spectral-audit.json`, `soil-acquisition.json`, `soil-admission.json` y `agronomic-metadata-audit.json`: disponibilidad comprobada y exclusiones.
- `registry/catalog.json`: ocho subconjuntos originales y deduplicación previa, 33 candidatos comunes efectivos en total por los bloques del catálogo; no es el número total de ajustes de validación.
- `registry/resource-preflight.json` y `implementation-tests-final.xml`: recuperación sintética, límites y pruebas.
- `runs/<id>/fresh-process-check.json`, `recovery-package.json` y `resources-*.json`: verificación en proceso nuevo y recursos reales.
- `registry/W05-eligibility.json`, `summary.json`, `paired-comparisons.json` y `final-integrity.json`: decisiones y cierre, cuando las ejecuciones correspondientes estén completadas.

La investigación reutiliza las mismas etiquetas de una sola campaña. No valida otra campaña, causalidad agronómica, eventos locales ni tendencias del cambio climático. No hay intervalos nuevos para W05. La elegibilidad, activación, despliegue y envío se registran por separado; la versión activa se conserva intacta.
