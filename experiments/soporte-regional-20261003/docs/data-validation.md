# Contrato y auditoría de datos

La unidad es una parcela de la campaña abril–octubre de 2025. `ID_POLIGONO` es la clave; se normaliza el alias `ID_POLIGON` del shapefile. El rendimiento usa t/ha y la superficie ha. Se exigen 197 identificadores únicos: 138 ENTRENAMIENTO con etiquetas finitas positivas y 59 PREDICCION sin etiqueta. Se rechazan discrepancias de área o conjunto entre CSV y geometría, duplicados, nube fuera de 0–100 y geometrías inválidas.

Los originales de `Reto-Cebada/DataSet` se leen sin modificarlos. `data/processed/source-manifest.json` contiene hashes SHA-256, tamaños, proveedor, unidades, escala y condiciones. Las doce descargas verificadas se copian a `data/external` sin sobrescribir una copia alterada; se conserva la evidencia original. El manifiesto identifica la versión de la caché por contenido.

El shapefile usa EPSG:4326. Distancias, áreas de intersección y ponderaciones se calculan en UTM 14N EPSG:32614. El reporte `audit.json` conserva solapamientos mayores de 1 m² sin reparar ni eliminar parcelas automáticamente. La comprobación del CSV usa fechas día/mes/año y registra codificación UTF-8; DGSIAP requiere CP1252.

Sentinel-2 contiene 59 040 registros, Landsat 48 626 y Planet 47 804. No se imputa NDVI de Landsat: únicamente se representa VI6T. Las columnas vacías de otros índices son ausencias estructurales. LAI negativo se marca como no físico y queda excluido de los predictores; no se alteran los originales. La auditoría comprueba media frente a mínimo/máximo y desviaciones negativas. No se convierte VI6T en grados Celsius ni se recortan indiscriminadamente índices a 0–1.

Tlaxcala tiene etiquetas 2.5 (9 parcelas), 3.0 (14) y 3.5 (8) t/ha. Esta cuantización limita el detalle de evaluación y no se corrige ni se usa para redondear predicciones. Puebla aporta 71 etiquetas e Hidalgo 36. Las 59 etiquetas ocultas no se reconstruyen ni se sustituyen por datos municipales.

Reproducir con el Python del entorno aislado:

```powershell
.\.venv\Scripts\python.exe -m agrocebada.cli audit
.\.venv\Scripts\python.exe scripts/check_preparation.py
.\.venv\Scripts\python.exe -m pytest -q
```

La segunda auditoría exige igualdad completa del reporte y verifica hashes de originales y caché. Su resultado queda en `artifacts/preparation-check.json`. Las pruebas incluyen etiquetas ocultas, duplicados y discrepancias de área. La auditoría detecta problemas de integridad; no acredita precisión agronómica ni calidad del test oculto.
