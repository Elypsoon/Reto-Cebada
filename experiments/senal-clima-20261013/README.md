# Señal hídrica verificada y clima diario

Fase independiente para la campaña abril–octubre de 2025: 197 parcelas, 138 etiquetas y 59 consultas. Las tablas y modelos operativos se conservan intactos. Los resultados de adquisición y entrenamiento se publicarán en `docs/sources.md` y `docs/results.md` con sus estados reales.

Usar el Python local fijado del proyecto con `PYTHONDONTWRITEBYTECODE=1`, `PROJ_NETWORK=OFF`, `PYTHONHASHSEED=2026` y `PYTHONPATH` dirigido a `src` de esta fase. Las dependencias efectivas están en `registry/preparation-receipt.json`; los originales y copias tienen hashes verificables.

Desde la raíz del proyecto, preparar una sola vez:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:PROJ_NETWORK='OFF'
.venv/Scripts/python.exe experiments/senal-clima-20261013/scripts/setup_phase.py
```

Adquisición: máximo 4 GiB, 45 minutos y tres intentos por solicitud. Cada ejecución principal: seis horas y 6 GiB medidos, incluidos procesos hijos. No se amplían límites ni se sustituyen productos para fabricar viabilidad. Inferencia y recuperación operan sin red.

Los comandos de adquisición, pruebas, congelación, entrenamiento y recuperación se documentan al implementar sus módulos. Las fuentes excluidas conservan su motivo y no reciben métricas inventadas. Los registros de productores son opcionales y descriptivos. Activación, despliegue y envío permanecen fuera de esta fase.
