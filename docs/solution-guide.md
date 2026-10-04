# AgroCebada 2026

Estimación retrospectiva del rendimiento de 197 parcelas de Hidalgo, Tlaxcala y Puebla, con 138 etiquetas de 2025 y 59 predicciones por exportar. Python, evaluación espacial anidada y dashboard Streamlit; ejecución inicial local.

## Abrir la solución preparada

```powershell
.\.venv\Scripts\python.exe -m agrocebada.cli verify
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra http://127.0.0.1:8501. Véase `docs/app-guide.md`. La inferencia utiliza datos y artefactos locales; no requiere conexión a APIs.

## Instalar y reproducir desde originales

Python 3.12. El entorno `.venv` es aislado y no modifica el Python global. Dependencias exactas de esta ejecución en `requirements.lock`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m agrocebada.cli prepare
.\.venv\Scripts\python.exe scripts/check_preparation.py
.\.venv\Scripts\python.exe -m agrocebada.cli train
.\.venv\Scripts\python.exe -m agrocebada.cli verify
.\.venv\Scripts\python.exe -m pytest -q
```

`prepare --official-only` y `train --official-only` permiten reproducir exclusivamente con datos del reto. El entrenamiento habitual guarda también el modelo oficial independiente. La regeneración cambia contratos/modelos; conserve íntegra una versión anterior si necesita recuperarla.

## Entregables y límites

Documento técnico, bibliografía con registro de asistencia de IA y anexos listos para revisión en `output/pdf/`. Los anexos tienen dos páginas, incluyen las 59 predicciones oficiales y la distribución de aportaciones de Leonardo Alvarez Gonzalez, Ángel de Jesús Elvis Gutiérrez Pacheco y Diego Cannata Cárdenas, realizada por indicación del usuario. Los siete apartados del informe cumplen los límites de palabras de la guía; el contenido editable se conserva en `docs/technical-report.md`.

`artifacts/predictions_59.csv`: dos columnas, identificadores oficiales, t/ha, sin redondeo artificial. `oof.csv`: 138 predicciones espaciales independientes de cada ajuste. `validation.json`: métricas, búsquedas, decisiones externas, ensambles, intervalos y sensibilidades. `contract_*.json`: versión y hashes. `spatial-folds.html`: mapa sin dependencia de mapas externos.

Documentación: auditoría, variables, fuentes, validación, inferencia, guía de consulta y demo en `docs/`. Los originales `Reto-Cebada/DataSet` se conservan; OpenSpec registra las tareas del cambio `prediccion-cebada-con-datos-verificados`.

La preparación de datos localiza la evidencia tanto en el cambio activo como en su archivo fechado de OpenSpec. El ajuste de compatibilidad previo está documentado en `artifacts/archive-compatibility.json`; su copia se conserva en `artifacts/versions/archive-2026-10-03/`.

La revisión de selección del 3 de octubre de 2026 incorpora medias global y regional como modelos elegibles, exige mejora interna estable antes de añadir complejidad, compara un promedio diverso de familias y vuelve a evaluar NASA/DGSIAP sobre cada familia. Las particiones internas retiran un solo grupo espacial cada vez, como la evaluación externa. Los artefactos actuales corresponden a un entrenamiento nuevo. Modelos, métricas, documentos y código de la ejecución anterior se conservan en `artifacts/versions/selection-before-2026-10-03/`; el primer intento sin corregir las particiones, que empeoró el error, está en `artifacts/versions/selection-attempt-1-2026-10-03/`. La evaluación reutiliza las mismas 138 etiquetas; confirmar la mejora fuera del desarrollo requiere datos adicionales o el test oficial. Los paquetes de `dist/` anteriores a esta revisión conservan su versión previa.

No se valida una campaña futura, pronóstico anterior a cosecha ni cualquier parcela nueva. El test oculto no tiene resultados conocidos. Datos municipales/regionales no acreditan calidad de suelo, causa agronómica ni elegibilidad de crédito. Alojamiento/URL y entrega oficial requieren una instrucción posterior; esta versión prepara la solución local.
