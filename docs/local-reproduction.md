# Reproducción local

La interfaz oficial es la de Cloudflare; las instrucciones de consulta están en [app-guide.md](app-guide.md). Esta guía documenta el entorno científico y los originales necesarios para reconstruir datos.

## Verificar los artefactos entregados

Python 3.12. Desde la raíz, en Windows:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m agrocebada.cli verify
.venv/Scripts/python.exe -m pytest -q tests experiments/estratificacion-pyr-20261018/tests experiments/fisiologia-siniestros-20261018/tests
```

En Linux/macOS, utilizar `python3.12` y `.venv/bin/python`. La instalación editable mantiene las rutas de los recursos junto al código. Las versiones exactas están en `requirements.lock`; Streamlit se conserva para verificar contratos existentes, aunque su interfaz se retiró.

Este recorrido no necesita los datos originales ni el checkout de origen. Comprueba los modelos guardados y las descargas E12. Para exportar la interfaz desde esos artefactos:

```powershell
.venv/Scripts/python.exe scripts/export_react_dashboard.py
npm --prefix frontend ci
npm run dashboard:build
```

## Preparar desde originales

Los originales están en `DataSet/`, con `Data/`, geometrías, clima y topografía. Tanto el código base como las investigaciones usan esa ruta en la raíz. No se requieren junctions ni una copia anidada del repositorio.

La evidencia externa archivada bajo `openspec/changes/archive/2026-10-03-prediccion-cebada-con-datos-verificados/evidence/` también es una entrada de preparación: se conserva aunque algunos archivos coincidan con `data/external/`, porque el código verifica sus hashes antes de promoverlos.

Los siguientes comandos regeneran tablas y modelos base y sobrescriben artefactos. Ejecutarlos en una copia de trabajo independiente si se quiere conservar la entrega E12:

```powershell
.venv/Scripts/python.exe -m agrocebada.cli prepare
.venv/Scripts/python.exe scripts/check_preparation.py
.venv/Scripts/python.exe -m agrocebada.cli train
.venv/Scripts/python.exe -m agrocebada.cli verify
```

`prepare --official-only` y `train --official-only` permiten reproducir exclusivamente con datos del reto. El entrenamiento base no reconstruye por sí solo el ensamble E12: consultar su [procedencia](model-update-e12.md) y el [README de la fase fisiológica](../experiments/fisiologia-siniestros-20261018/README.md). Los scripts históricos de importación requieren el Git de origen y sus snapshots locales; no son parte del arranque o la verificación habitual.

## Documentos y evidencia

`artifacts/predictions_59.csv` contiene los 59 identificadores y rendimientos oficiales; `oof.csv`, las 138 estimaciones de validación; `validation.json`, las métricas; y `contract_*.json`, las versiones y hashes. El informe del equipo está en `output/pdf/Reporte_AgroCebada_2026.pdf`; los documentos de auditoría y comprobaciones están en `output/audit/`.

Los archivos de compatibilidad registran migraciones históricas sin reentrenamiento. Los snapshots locales de `artifacts/versions/` y los paquetes antiguos no forman parte de la entrega actual. Las comprobaciones históricas pueden describir versiones anteriores de la interfaz; la guía vigente es [deployment-cloudflare.md](deployment-cloudflare.md).
