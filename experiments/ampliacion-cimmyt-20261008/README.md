# Ampliación CIMMYT — fase 2026-10-08

Estado: protocolo revisado aplicado y comparaciones verificadas el 9 de octubre de 2026. Leer [resultados](docs/conclusions.md), [cobertura](registry/coverage-v2.json) y [auditoría v2](docs/auditoria-cimmyt-v2.md); la [auditoría anterior](docs/auditoria-cimmyt.md) se conserva como antecedente histórico.

La fase conserva las 138 etiquetas oficiales como única población de evaluación. Hay 48 etiquetas auxiliares candidatas antes de admisión espacial y 45 con celda única y clima completo bajo `cimmyt-point-assumption-v2`; por ajuste quedan 40–43 mexicanas. Los 29 candidatos locales siguen siendo insuficientes.

La ampliación A02 no supera los criterios congelados: frente a A01 aumenta el RMSE un 2,72% en principal y un 2,42% en balanceado; en rotado conserva íntegramente el respaldo oficial y el mismo error. Tampoco supera a A00 activa. Se admitieron auxiliares en tres de los catorce ajustes externos. Es una conclusión de desarrollo condicionada al supuesto espacial, sin validación independiente de otra campaña.

A03 verificó la selección reproducible por grupos: las fracciones 25% y 50% son inviables en los tres ajustes que admitieron auxiliares; el 100% reproduce A02. Los otros once ajustes no requieren curva porque A02 eligió el respaldo oficial. A04 no se entrenó por soporte local insuficiente. Estos estados no acreditan experimentos predictivos que no se ejecutaron.

Pasaron 52 pruebas y las recuperaciones en procesos nuevos sin red, con tolerancia absoluta 1e−10. Se comprobaron las 229 entradas congeladas y los 2.596 archivos protegidos; los resultados no cambian el modelo activo.

Usar el Python fijado del proyecto con `PYTHONDONTWRITEBYTECODE=1`, `PROJ_NETWORK=OFF` y `PYTHONPATH` apuntando a `src` de esta fase. Para leer XLSX, añadir su `vendor` al mismo `PYTHONPATH`; `reader-requirements.lock` fija las dos dependencias adicionales. `requirements.lock` conserva el entorno numérico de origen y `registry/preparation.json` sus versiones efectivas.

Entradas de la fase:

- `scripts/check_population.py`: verifica población y particiones oficiales.
- `scripts/offline_worker.py script scripts/recover_a00.py`: recupera el control histórico copiado en proceso sin red.
- `scripts/acquire_cimmyt.py`: adquiere/verifica los tres archivos públicos; no evade autenticación ni sustituye versiones silenciosamente.
- `scripts/profile_cimmyt.py`: descubre el esquema y genera tablas locales con claves heterogéneas preservadas como texto.
- `scripts/audit_cimmyt.py`: recalcula el embudo y las etiquetas candidatas; no realiza admisión geográfica ficticia.
- `scripts/prepare_spatial.py`: construye cohortes y publica sensibilidad de admisión antes de solicitar clima.
- `scripts/prepare_climate.py`: adquiere 13 pares celda/año y construye las matrices comunes completas.
- `scripts/reconcile_audit.py`: conserva antecedentes y registra la admisión asumida sin afirmar que se encontraron los metadatos ausentes.
- `scripts/preflight_phase.py`: verifica recursos y recuperación con datos sintéticos, además de la identidad opcional autorizada.
- `scripts/freeze_phase.py`: congela el protocolo antes del primer ajuste real; rechaza una segunda congelación bajo el mismo identificador.
- `scripts/execute_phase.py A01 A02 A03`: ejecuta y recupera secuencialmente; los identificadores ya cerrados no se reutilizan.
- `scripts/summarize_phase.py`: recalcula comparaciones pareadas y verifica integridad; no elige otra receta por sus resultados.
- `tests/`: pruebas de armonización, separación, clima, selección, contaminación, registro y recuperación.
- `scripts/interim_receipt.py`: recibo histórico de la pausa v1; no volver a ejecutarlo después de aplicar v2.

Los datos originales y derivados se mantienen localmente sujetos a los términos CIMMYT. No redistribuirlos ni subir la carpeta de datos o contextos a un repositorio público. No se ha activado, desplegado o enviado ningún modelo.
