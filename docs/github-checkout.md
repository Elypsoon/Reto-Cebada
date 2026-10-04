# Preparar el checkout de GitHub

Esta rama incorpora la solución y la fase experimental completa. Conserva la investigación y `DataSet/` existentes. No activa un modelo nuevo ni representa una evaluación del organizador.

## Registros completos y vistas para GitHub

Los JSON de más de 2 MiB se distribuyen como vistas resumidas junto a un `.json.gz` que conserva exactamente todos sus bytes. `github-transport.json` contiene hashes y tamaños. Antes de verificar registros, manifiestos o paquetes, restaure los originales:

```powershell
python scripts/restore_github_evidence.py --check
python scripts/restore_github_evidence.py
```

La restauración verifica cada SHA-256, conserva el gzip y rechaza sobrescribir archivos modificados. Materializa los registros íntegros sobre las vistas resumidas, por lo que esos archivos aparecerán modificados en Git después de restaurar. No cambia ninguna métrica, contrato ni hash original.

## Entorno e inferencia

Python 3.12 y las versiones de `requirements.lock`:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe -m pip install --no-deps -e .
.venv\Scripts\python.exe scripts/configure_checkout.py
.venv\Scripts\python.exe -m agrocebada.cli verify
.venv\Scripts\python.exe -m streamlit run app.py
```

En Linux/macOS utilice `python3.12` y `.venv/bin/python`. `configure_checkout.py` crea una vista local de `DataSet/` en la ruta histórica esperada por el código: una junction en Windows o un enlace simbólico en Linux/macOS. No copia ni modifica los originales. También adapta solo las rutas de ejecución de las dos fases al nuevo checkout, guardando los metadatos originales como `workspace.origin.json` y el registro de traslado en `checkout-relocation.json`. Los cambios de configuración son locales y no implican reentrenamiento ni alteración de código, datos o modelos.

Las dependencias y los archivos de código se conservan por versión; `.gitattributes` evita conversiones de finales de línea que invalidarían sus hashes al clonar en Windows. Los entornos instalados, temporales y cachés no se distribuyen.

## Consultar los experimentos

- [Informe de E00–E08](../experiments/soporte-regional-20261003/docs/phase-results.md).
- [Historial incremental](../experiments/soporte-regional-20261003/docs/experiment-history.md).
- [Paquetes de recuperación](../experiments/soporte-regional-20261003/packages/README.md).
- [Cambio archivado y sincronizado](../openspec/changes/archive/2026-10-03-experimentos-trazables-con-soporte-regional/evidence.md).

E08 no es elegible por protección de Puebla en el esquema rotado. Los intervalos experimentales están desactivados por cobertura inferior al mínimo. Se conservan los intentos fallidos y las 68 pruebas de la fase; etiquetas de otra campaña y manejo verificable siguen pendientes.

TabPFN-2.5 utiliza un entorno separado y sus condiciones de uso están en `LICENSE` y `NOTICE` junto a cada checkpoint. Los derechos son otorgados directamente por Prior Labs GmbH para uso no comercial. Los pesos, contextos, parámetros y hashes se distribuyen para investigación y reproducción, sin despliegue de producción. Para volver a ejecutar el adaptador, instale su `optional/tabpfn-2.5/requirements.lock` en su propio entorno compatible; el entorno instalado de la ejecución original se excluyó de Git.
