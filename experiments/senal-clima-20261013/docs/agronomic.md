# Registros agronómicos opcionales

CSV local con columnas `ID_POLIGONO,campana,campo,valor,unidad,fecha_evento,procedencia`. Campos admitidos: `siembra`, `variedad` y `riego`. Siembra usa fecha; variedad, nombre y unidad vacía; riego acepta mm/cm/m y conserva conversión a mm. Cada registro tiene fecha del evento y una fuente comprobable. No se infieren valores ausentes.

Invocar `.venv/Scripts/python.exe experiments/senal-clima-20261013/scripts/import_agronomic.py` sin argumento registra la ausencia. Un argumento añade un CSV local explícito. Los originales, duplicados y conflictos se conservan bajo `data/descriptive/agronomic`; no se unen a tablas predictivas ni se usan para escoger un registro por rendimiento. Ese directorio y su recibo descriptivo están separados de los insumos congelados del modelo. Incorporar datos tarde no modifica ventanas, código, catálogo o predicciones; su uso predictivo requiere un protocolo posterior.
