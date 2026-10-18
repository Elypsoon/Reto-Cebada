# Fase de prioridades predictivas

Implementación y evaluación completadas del cambio `evaluacion-predictiva-prioritaria-con-evidencia`.

La fase conserva 197 parcelas, 138 etiquetas de desarrollo y 59 consultas, con corte 2025-10-31. Las 12 ejecuciones P00–P08 terminaron y reprodujeron métricas e inferencia sin red. P06 no cumple los criterios de sustitución. TabPFN-3 mensual mejora frente a la activa en los tres esquemas, como diagnóstico sobre estas mismas etiquetas. La decisión y sus límites se explican en [conclusiones](docs/conclusions.md); el detalle está en [resultados](docs/priority-results.md) y [evidencia y cobertura](docs/evidence-and-coverage.md).

## Preparación completada

- Copias verificadas de código y tablas de soporte regional, con una versión inicial inmutable y manifiestos de procedencia.
- Controles C-activa y C-soporte reproducidos con código original e importaciones/destinos aislados.
- Los cuatro esquemas espaciales originales, revisión 2, importados por ID sin regenerar particiones.
- Evidencia L01–L08 y matriz P00–P08, con métricas verificadas y alternativas secundarias diferidas explícitas.
- Selectores de ranking, lista agronómica y todas las variables elegibles.
- Cinco ramas espectrales, covariables/calidad compartidas, calendario y eje térmico NASA auditado.
- Proyección individual B-spline y PCA de coeficientes ajustable exclusivamente por entrenamiento.
- Ridge/GPR jerárquicos, GAM directo/jerárquico y EBM 0.7.8 con configuración acotada.

## Corrección autorizada y protocolo

El usuario autorizó corregir el conteo conservando todas las recetas: máximos 78/14/42/36/51/30. No se añadieron modelos ni parámetros. La revisión está en `docs/candidate-budget-review.md`.

La fuente de progreso es `openspec/changes/evaluacion-predictiva-prioritaria-con-evidencia/tasks.md` en el proyecto. `registry/frozen-priority.json` identifica la versión inmutable y los protocolos registrados antes del primer resultado externo. No se amplía el catálogo con ganadores externos.

TabICLv2 y TabPFN-3 usan checkpoints oficiales explícitos, ocho estimadores y entornos CPU independientes. Ambos pasaron recuperación sintética en proceso nuevo a tolerancia 1e-10/rtol=0. Se conservan los intentos previos fallidos. Se desactiva MKLDNN y se fijan las semillas/configuración numérica CPU antes de congelar; la caché de skrub permanece dentro de la fase. El contexto profesional experimental no comercial de TabPFN-3 fue confirmado por el usuario.

Cada ejecución mantiene un único proceso de entrenamiento, dos hilos por biblioteca y un supervisor que suma memoria del proceso y sus descendientes: 4 GiB, 120 minutos por bloque obligatorio y 30 minutos por configuración opcional, incluida recuperación. Los procesos bloquean conexiones IP antes de cargar estimadores. Un límite interrumpe la ejecución y no convierte predicciones parciales en resultados verificados.

## Recibos

- `registry/preparation-receipt.json`, `copy-origins.json` y `source-integrity.json`: preparación y fuentes protegidas.
- `registry/control-resolution.json`: rutas e identidad de cada control, sin métricas nuevas.
- `registry/scheme-validation.json`: IDs, corte, tamaños y hash original de particiones.
- `registry/evidence.json`: fuentes, alcance de lectura, hipótesis y controles.
- `registry/curve-preparation.json`, `functional-preparation.json`: soporte, sin base compartida global ni etiquetas externas.
- `registry/implementation-tests.xml`: 47 pruebas sintéticas e integración de los componentes.
- `registry/intermediate-integrity.json`: verificación intermedia de fuentes protegidas; no sustituye la recuperación final de las 59 predicciones.
- `registry/package-verification.json`: 12 paquetes, sus manifiestos y las versiones instaladas de los tres entornos.
- `registry/final-integrity-receipt.json`: 133 archivos protegidos intactos, 12 versiones históricas por ambas rutas y dos contextos TabPFN 2.5 recuperados a 1e-10.
- `registry/closing-tests.xml`: 47 pruebas finales aprobadas, sin fallos ni omisiones.
- `registry/P06-official-inputs-check.json`: inferencia de 59 consultas con entradas oficiales, sin tablas NASA ni ajuste nuevo.

## Entorno y verificación

La `.venv` de esta fase es nueva; no se copió ni modificó la del modelo activo. `requirements.lock` fija las dependencias instaladas, incluidas `interpret==0.7.8` e `interpret-core==0.7.8`. El entorno se creó con Python 3.12.14.

Desde la carpeta de esta fase:

```powershell
& './.venv/Scripts/python.exe' -m pytest tests -q -p no:cacheprovider --junitxml 'registry/recheck-tests.xml'
```

Los ensayos EBM usan dos hilos y no usan early stopping. El sandbox de Windows bloquea sus canales internos; requieren ejecución local autorizada fuera de ese sandbox. Los temporales de las pruebas conservan ACL heredada dentro de `tmp/`, sin cambiar permisos de otras carpetas. Los intentos fallidos se conservan y no cuentan como verificaciones positivas.

No ejecutar `agrocebada.phase prepare/run`: es el orquestador histórico copiado como base. La fase nueva usa `scripts/freeze_priority.py`, `scripts/execute_priority.py` y `scripts/report_priority.py`. No activar, desplegar ni enviar estas predicciones. Un modelo elegible sigue requiriendo una decisión posterior de activación.

La versión congelada y `registry/implementation-tests.xml` son inmutables. Los IDs cerrados no se reutilizan. Los paquetes usan la instantánea común completa de código/datos/pesos y los objetos o contextos particulares de cada ejecución; sus rutas y hashes están en `runs/<id>/artifacts/recovery-package.json`. Véase [recuperación](docs/recovery.md).
