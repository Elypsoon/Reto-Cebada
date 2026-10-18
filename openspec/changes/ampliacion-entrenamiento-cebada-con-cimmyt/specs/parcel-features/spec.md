## ADDED Requirements

### Requirement: Contrato común entre población oficial y auxiliar
El sistema SHALL construir una representación común con área verificable y clima regional NASA POWER, usando las mismas definiciones, unidades y ventanas abril–mayo, junio–julio y agosto–octubre en el año de cada observación. MUST mantener el corte oficial del 31 de octubre de 2025 y utilizar para los auxiliares exclusivamente información de su campaña hasta el 31 de octubre. SHALL identificar la representación común como distinta de las representaciones espectrales oficiales; MUST conservar un control oficial completo y un control oficial con exactamente las mismas columnas comunes que el candidato ampliado.

#### Scenario: Fuente con fechas históricas
- **WHEN** una observación auxiliar corresponde a 2018
- **THEN** recibe clima de abril–octubre de 2018, nunca clima ni rendimiento de 2025, y su contrato permite verificar año, ventanas y consultas originales.

#### Scenario: Índices ausentes en la fuente auxiliar
- **WHEN** CIMMYT no suministra índices satelitales equivalentes a los del reto
- **THEN** la representación común los excluye para ambas poblaciones, sin rellenar una rama espectral completa con valores imputados ni presentar este control como equivalente al modelo oficial completo.

#### Scenario: Campo disponible únicamente en CIMMYT
- **WHEN** la fuente auxiliar contiene manejo, fecha de cosecha, ingresos, identidad de productor o variables demográficas ausentes del contrato oficial
- **THEN** esos campos sirven únicamente para auditoría, admisión o agrupación y no entran como predictores compartidos del rendimiento.

### Requirement: Localización aproximada y soporte climático verificable
El sistema MUST conservar la incertidumbre espacial documentada y distinguirla de los márgenes asumidos de las ubicaciones auxiliares. SHALL tratar los campos puntuales del Excel como ubicación aproximada bajo `cimmyt-point-assumption-v2`, con WGS84 asumido y caja principal ±0,01° en ambos ejes. SHALL vincular clima únicamente si toda esa caja corresponde a una única celda meteorológica nativa, registrar unidades, cobertura diaria, rellenos y límites físicos, y rechazar ambigüedad incluyendo contacto con un límite de celda. MUST impedir que la caja se presente como límite real, error máximo certificado o soporte comprobado de píxeles satelitales finos. Las consultas históricas y sus cachés SHALL pertenecer a la nueva fase, sin alterar el lector oficial fijado a 2025.

#### Scenario: Incertidumbre entre celdas
- **WHEN** la caja principal asumida de un registro intersecta más de una celda climática o toca su límite
- **THEN** se excluye ese registro del experimento y se registra el motivo sin elegir una celda usando el rendimiento.

#### Scenario: Serie incompleta
- **WHEN** una consulta contiene días ausentes, valores de relleno o unidades incompatibles
- **THEN** no produce una fila aparentemente completa; se registra el fallo y se aplica la regla de cobertura congelada antes de entrenar.

#### Scenario: Punto sin polígono publicado
- **WHEN** el Excel contiene un punto coherente con los controles predeclarados pero no contiene vértices ni precisión verificable
- **THEN** puede evaluarse bajo el supuesto autorizado y su caja principal, sin reconstruir un polígono de parcela, deducir precisión de decimales ni declarar verificado el datum.

#### Scenario: Signo ya expresado en la longitud
- **WHEN** el encabezado indica oeste y el valor original de longitud ya es negativo
- **THEN** se conserva ese signo; no se invierte otra vez ni se intercambian ejes para forzar una ubicación admisible.
