# Recuperación de versiones

La versión activa sigue intacta. El paquete `artifacts/versions/selection-current-20261003` conserva código, requisitos, tablas preparadas, cachés externas, modelos, contratos, exportaciones e informes de la ejecución vigente. Su manifiesto registra los hashes originales. Se comprobaron en un proceso nuevo sus 59 predicciones y 138 OOF; sus 25 pruebas pasaron.

Para consultar ese paquete sin reemplazar nada, usar el intérprete existente del proyecto y establecer `PYTHONPATH` al directorio `src` del paquete. Desde el paquete ejecutar `python -m agrocebada.cli verify`. Para abrir su aplicación ejecutar `python -m streamlit run app.py` con ese mismo entorno.

Para restaurar un directorio de trabajo, copiar conjuntamente las carpetas y archivos enumerados en `version-manifest.json` del paquete, conservando las rutas relativas. Comprobar todos los hashes y después ejecutar la verificación en un proceso nuevo. No mezclar código, contratos o datos entre versiones, ni cambiar hashes para hacer compatibles modelos antiguos. `restoration-check.json` registra la comparación íntegra del paquete con su manifiesto y su prueba de inferencia.

El experimento está en `experiments/regional-20261003`. Desde PowerShell del proyecto: `./experiments/regional-20261003/run.ps1 verify`. Para reproducir su evaluación: `./experiments/regional-20261003/run.ps1 robust`; para una nueva salida aislada: añadir `-ArtifactDirectory artifacts-reproduction`. Para ver la aplicación experimental: `./experiments/regional-20261003/run.ps1 app`. Estos comandos fijan el código de la copia experimental y evitan importar accidentalmente el paquete editable vigente.

Las fuentes originales grandes permanecen en la carpeta original, que se usa para auditoría en lectura. Las predicciones y la aplicación utilizan las tablas y cachés contenidas en cada versión. Mantener las versiones instaladas de `requirements.lock` para reproducir contratos.
