# Spec Delta

## ADDED Requirements

### Requirement: Recuperación acotada de fuentes públicas temporales
El sistema SHALL recuperar fuentes públicas con proveedor, versión, consultas, fechas, licencia, unidades, calendario, cobertura y hashes verificables. MUST separar catálogo consultable, archivo descargado y fuente admitida, limitar los intentos y conservar evidencia de fallos; la ausencia de acceso autenticado no bloqueará los bloques independientes.

#### Scenario: Catálogo accesible sin descarga válida
- **WHEN** existe una escena o producto en el catálogo pero sus datos no se recuperan íntegros
- **THEN** la fuente permanece no admitida, se conserva el motivo y no recibe métricas como si hubiera sido utilizada.

#### Scenario: Alternativa climática no accesible
- **WHEN** ERA5-Land necesita credenciales no disponibles o una estación no tiene datos suficientes de 2025
- **THEN** se registra la exclusión y continúa la auditoría de las fuentes públicas independientes sin crear cuentas ni reemplazar fuentes silenciosamente.

#### Scenario: Recuperación de un original local
- **WHEN** se reconstruye una tabla a partir de una descarga admitida
- **THEN** los hashes, metadatos y consulta permiten identificar exactamente la versión utilizada sin una nueva conexión al proveedor.

### Requirement: Identidad independiente de la señal hídrica nueva
El sistema SHALL admitir una señal hídrica vegetal solo con fórmula, bandas, sensor, reflectancia, tratamiento de calidad y orientación documentados. MUST conservar la identidad del NDWI original cuando su definición sea desconocida; una señal derivada nueva tendrá identidad y procedencia propias y no probará mecanismos fisiológicos.

#### Scenario: Nueva extracción Sentinel frente a NDWI desconocido
- **WHEN** se obtienen bandas verificadas para producir una señal nueva
- **THEN** se registra una variable distinta con su fórmula y no se renombra ni se atribuye esa fórmula al NDWI entregado.

#### Scenario: Fórmula documentada sin soporte observacional
- **WHEN** la fórmula es válida pero faltan píxeles o fechas utilizables
- **THEN** la auditoría semántica se distingue de la viabilidad temporal y la señal no habilita un bloque sin cobertura suficiente.

### Requirement: Metadatos de productores opcionales y vinculados
El sistema SHALL admitir registros opcionales de siembra, variedad y riego con identidad parcelaria, campaña, fecha, unidad cuando corresponda y procedencia. MUST conservar desconocidos y conflictos, rechazar uniones ambiguas y mantener operativa la ruta pública cuando no existan esos registros.

#### Scenario: Ausencia de bitácoras
- **WHEN** no se suministran registros de productores
- **THEN** continúa la fase pública y siembra, variedad y riego permanecen desconocidos, sin asignarlos por municipio o recomendación regional.

#### Scenario: Registros contradictorios
- **WHEN** dos registros asignan información incompatible al mismo ID y campaña
- **THEN** el conflicto queda identificado y no se utiliza una elección automática sustentada en el rendimiento o en el error predictivo.

#### Scenario: Metadatos recibidos después de congelar
- **WHEN** se incorporan registros nuevos después del primer ajuste
- **THEN** se conservan como evidencia descriptiva y no cambian el calendario, catálogo o predicciones de una ejecución cerrada.
