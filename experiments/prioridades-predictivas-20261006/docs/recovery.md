# Recuperación e integridad

Las 12 ejecuciones están completas. Cada carpeta `runs/<id>/` contiene su protocolo, estado, manifiesto de artefactos, resultados y recibo de recuperación en proceso nuevo. Los recursos de entrenamiento y verificación se registran por separado; ambos procesos bloquearon conexiones IP. La tolerancia permanece en `atol=1e-10, rtol=0`.

El archivo `artifacts/recovery-package.json` de cada ejecución referencia una instantánea común inmutable: `versions/f582940ed8bbb99e0d7d21065bca6df347cffc877fdcf2766151c24e9969facf/`. Incluye código, datos, particiones, controles originales, configuración, dependencias fijadas y pesos/licencias opcionales. La recuperación requiere tanto esa instantánea como los artefactos particulares del run. Un archivo de modelo aislado no constituye el paquete completo.

| Ejecuciones | Estado recuperable | Entorno | Recuperación ya verificada |
| --- | --- | --- | --- |
| P00-C-activa / P00-C-soporte | Modelos y contratos originales de ambas rutas | `.venv` con código del control correspondiente | 59 consultas por ruta y métricas de cada esquema |
| P01–P06 | `model.joblib`, contrato, selección y transformaciones ajustadas | `.venv` | 59 consultas, métricas y suma de componentes, sin reajuste |
| P07, dos tablas | Contexto, columnas, checkpoint y configuración explícitos TabICL v2 | `optional/tabicl-v2/env` | Reconstrucción desde contexto, 59 consultas y métricas |
| P08, dos tablas | Contexto, columnas, checkpoint y configuración explícitos TabPFN-3 | `optional/tabpfn-3/env` | Reconstrucción desde contexto, 59 consultas y métricas |

`registry/package-verification.json` confirma hashes de los 12 manifiestos y versiones instaladas de todas las dependencias fijadas en los tres entornos. `registry/P06-official-inputs-check.json` confirma también que la inferencia puntual P06 necesita únicamente su representación oficial compacta para las 59 consultas. Los intervalos recuperados en `registry/P06-recovered-intervals-59.csv` corresponden al modelo separado que excluye calibración; su centro puede diferir del modelo puntual ajustado con las 138 etiquetas. Son artefactos de investigación de un procedimiento no elegible.

Para repetir las verificaciones de cierre sin entrenamiento, desde la carpeta de esta fase, con `PYTHONPATH` apuntando a `src`:

```powershell
& .venv/Scripts/python.exe registry/verify-packages.py
& .venv/Scripts/python.exe registry/close-audit.py
```

Estos comandos escriben recibos bajo `registry/` y no modifican artefactos cerrados. Las pruebas generales se pueden repetir con un destino XML nuevo; no se debe sobrescribir el recibo de implementación congelado.

La recuperación histórica se efectuó sobre copias nuevas y con el código original de cada versión: activa, regional, diez ejecuciones previas convencionales y los dos contextos E07-v3. Las primeras 12 recuperaron ambas rutas sin ajuste; los contextos opcionales reconstruyeron sus preprocessors desde el contexto original. Se compararon 59 predicciones por ruta y configuración a la misma tolerancia.

El primer intento de TabPFN 2.5 falló al imponer el entorno numérico de la fase nueva. Se conserva su registro `registry/historic-recovery/resources-E07-v3-monthly_20_10.json` y su log. Ambos contextos pasaron después con el entorno original, sin modificar código, datos, pesos, parámetros ni tolerancia. El recibo definitivo es `registry/final-integrity-receipt.json`; el resumen histórico completo está en `registry/historic-recovery/final-summary.json`.
