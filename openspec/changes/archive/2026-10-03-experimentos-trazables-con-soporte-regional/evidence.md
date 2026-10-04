# Evidencia de ejecución

Fase aislada: `experiments/soporte-regional-20261003`. Se ejecutaron E00–E08, incluidas las dos configuraciones fijas de TabPFN, y se registraron controles, resultados negativos, incidencias, cambios de procedimiento/modelo y versiones recuperables.

- [Informe completo, tres esquemas y decisión por ruta](../../../../experiments/soporte-regional-20261003/docs/phase-results.md).
- [Historial incremental](../../../../experiments/soporte-regional-20261003/docs/experiment-history.md) y [métricas CSV](../../../../experiments/soporte-regional-20261003/registry/summary.csv).
- [Catálogo congelado](../../../../experiments/soporte-regional-20261003/registry/catalog.json), [incidencia de particiones](../../../../experiments/soporte-regional-20261003/registry/partition-revision.json) y [reintento TabPFN](../../../../experiments/soporte-regional-20261003/registry/optional-retry-catalog.json).
- [68 pruebas pasan: 42 existentes y 26 nuevas](../../../../experiments/soporte-regional-20261003/registry/test-results.json). La suite completa incluye inferencia y aplicación sin red, rechazo de contratos incompatibles, selección sin contaminación, composición de explicaciones, producción por superficie y recuperación del registro.
- [Cierre de fase y hashes](../../../../experiments/soporte-regional-20261003/registry/phase-closure.json) y [paquetes de recuperación](../../../../experiments/soporte-regional-20261003/packages/README.md).

E08 enriquecido obtuvo RMSE 0.687622 / 0.761172 / 0.748305 t/ha en principal / balanceado / rotado; oficial 0.688201 / 0.760462 / 0.748305. Ambas rutas son no elegibles por protección de Puebla en el rotado: MAE 0.424265 frente a máximo 0.415714. Los intervalos permanecen desactivados porque la cobertura principal es 84.78%, inferior a 85%; cobertura en Hidalgo 58.33%.

Se verificaron los 176 archivos originales, los manifiestos iniciales de H00/H01 y las 59 predicciones de la activa por ruta en un proceso nuevo (tolerancia absoluta 1e-10). E00 y E08 reprodujeron ambas rutas desde paquetes independientes; las dos configuraciones TabPFN reprodujeron 59 consultas desde checkpoint/contexto y desde paquetes. No hubo activación, despliegue ni evaluación del organizador.

La prioridad continúa siendo obtener etiquetas verificadas de otra campaña y registros de manejo por parcela. Ambas disponibilidades siguen pendientes. No se ampliaron grillas ni se cambiaron umbrales para forzar una mejora.
