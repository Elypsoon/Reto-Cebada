# Fase experimental: soporte regional

Predicción retrospectiva de rendimiento en t/ha, campaña abril–octubre de 2025, corte 2025-10-31 y semilla 2026. Se conservan 197 parcelas, 138 etiquetas y 59 consultas ocultas. La fase desarrolla hipótesis sobre las mismas etiquetas; no constituye una evaluación temporal ni una evaluación del organizador.

La activa y el experimento regional anterior se conservan por separado. Todos los destinos de esta fase permanecen en este directorio. Cada ejecución guarda protocolo, estado, cambios, métricas, OOF, modelos, contratos, predicciones y manifiestos. Un resultado negativo también se publica.

## Consultar los resultados

- `docs/experiment-history.md`: índice incremental.
- `registry/summary.csv`: métricas por ejecución, ruta y esquema.
- `registry/catalog.json`: protocolos de la revisión vigente y su orden.
- `runs/<run-id>/result.md`, `changes.json` y `artifacts/`: detalle y evidencia.
- `docs/phase-results.md`: entrega acumulada al cerrar la fase.

La revisión 1 conserva el intento original y sus resultados parciales. La revisión 2 corrige un defecto de cortes binarios que dejaba entrenamiento insuficiente en el diagnóstico intraestado. Los cortes iguales usan solo geometría y orden de ID. La evidencia está en `registry/partition-revision.json`; no se eligieron factores usando resultados de variantes.

## Ejecutar y reproducir

Desde la raíz del proyecto, con su Python compatible:

```powershell
.venv\Scripts\python.exe experiments/soporte-regional-20261003/scripts/run_suite.py E08-v2
.venv\Scripts\python.exe experiments/soporte-regional-20261003/scripts/run_tests.py
.venv\Scripts\python.exe experiments/soporte-regional-20261003/scripts/recover_package.py E00-v2
```

El ejecutor es secuencial y salta ejecuciones cerradas correctamente. Un run fallido no se sobrescribe. Una recuperación exige un checkpoint verificable y hashes iguales; una modificación de código/protocolo exige IDs nuevos. El ensamblador de paquetes reúne en un destino nuevo código por hash, dependencias, tablas, modelos, contratos y salidas, y comprueba 59 predicciones por ruta en un proceso nuevo. No sobrescribe paquetes existentes.

La suite prueba una copia de los artefactos finales, incluida la aplicación sin conexión, para conservar los manifiestos de entrenamiento.

## TabPFN y elegibilidad

TabPFN-2.5 usa pesos verificados, contexto de entrenamiento recuperable y un entorno propio bajo `optional/tabpfn-2.5`. Sus dos tablas se evalúan separadamente, con configuración fija y sin elegir una con las OOF externas. El checkpoint sintético y las condiciones están documentados en su manifiesto y licencia; solo se usa para esta evaluación local.

El intento E07-v2 se conserva como fallido por redondeo del CSV float32. E07-v3 utiliza el código independiente `optional/adapter-v3`, con manifiesto completo, para exportar float64 con 17 dígitos sin cambiar el modelo. Su catálogo adicional quedó congelado antes de entrenar en `registry/optional-retry-catalog.json`; incluye ambas configuraciones y sus relaciones con los intentos previos. Los manifiestos originales y el código base de E00–E08 permanecen intactos.

E08 combina exclusivamente E01a + E02 + E04a. Los restantes diagnósticos no se incorporan por tener un RMSE favorable. Solo E08 recibe elegibilidad por ruta, con los umbrales congelados y protección regional. La elegibilidad nunca equivale a activación; esta fase no sustituye la activa.

Los datos verificables de otra campaña y de manejo siguen pendientes. No se inventan etiquetas ni variables de manejo para completar experimentos.
