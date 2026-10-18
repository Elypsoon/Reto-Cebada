# experiment-tracking Specification

## Purpose

Mantener un historial verificable de hipótesis, modificaciones del modelo y resultados de cada ejecución experimental, incluyendo controles, resultados negativos y fallos, sin confundir antecedentes con evidencia nueva.

## Requirements

### Requirement: Identidad y protocolo de cada ejecución
El sistema SHALL asignar identificadores únicos de experimento y ejecución, relacionar cada ejecución con su hipótesis y control, y conservar antes del primer ajuste su configuración, límites de búsqueda, semillas, rutas, particiones, población, corte, fuentes y criterios de aceptación. MUST vincular versiones de código, dependencias, datos, variables y modelos mediante hashes verificables.

#### Scenario: Inicio de un experimento
- **WHEN** se solicita entrenar una variante registrada
- **THEN** existe un protocolo congelado y un control identificable antes de cualquier ajuste y la ejecución obtiene un identificador que no sobrescribe otra ejecución.

#### Scenario: Protocolo alterado después de entrenar
- **WHEN** se cambia un parámetro, representación, regla o partición del protocolo ya utilizado
- **THEN** se rechaza la reutilización del identificador y se exige una ejecución nueva con la diferencia y su motivo registrados.

### Requirement: Historial de estados y cambios recuperable
El sistema SHALL conservar eventos de planificación, inicio, finalización, fallo, interrupción y omisión con fecha, motivo y vínculo a la ejecución. MUST conservar el historial de cambios de predictores, procesamiento, selección, modelo, parámetros, soporte regional, componentes y fuentes frente al control; la inexistencia de un modelo final se registrará explícitamente.

#### Scenario: Resultado desfavorable
- **WHEN** una ejecución completada empeora el error o falla un criterio regional
- **THEN** sus métricas, diferencias del modelo, artefactos y decisión negativa permanecen consultables y no se sustituyen por otra variante bajo el mismo identificador.

#### Scenario: Proceso interrumpido
- **WHEN** el entrenamiento se interrumpe antes de completar todos los esquemas requeridos
- **THEN** se conservan los resultados parciales, la ejecución se identifica como incompleta y no dispone de una decisión positiva de promoción.

### Requirement: Resultados pareados y comparabilidad explícita
El sistema SHALL publicar por ejecución y ruta RMSE, MAE, R², sesgo firmado, tamaños, métricas por estado, fold y tercil de área, soporte de entrenamiento y cambios frente al control y la referencia regional. MUST verificar igualdad de identificadores, etiquetas, particiones, corte y versión de datos antes de declarar una comparación pareada; una ejecución nueva SHALL conservar sus predicciones externas y sus métricas recalculables.

#### Scenario: Comparación válida
- **WHEN** candidato y control comparten las 138 etiquetas y las mismas asignaciones espaciales
- **THEN** el informe conserva diferencias por parcela y métricas separadas por esquema, sin presentar las repeticiones como etiquetas adicionales.

#### Scenario: Control incompatible
- **WHEN** cambia la versión de etiquetas o el esquema entre candidato y control
- **THEN** el sistema marca la comparación como no pareada y exige recalcular ambos sobre una versión común antes de atribuir una mejora al modelo.

### Requirement: Publicación incremental y verificada
El sistema SHALL actualizar el resumen consultable y el registro al cerrar cada ejecución, incluyendo rutas a sus artefactos y el estado de verificaciones. MUST marcar una ejecución como completada solo cuando sus métricas se reproduzcan desde las predicciones, sus artefactos obligatorios sean íntegros y sus verificaciones aplicables finalicen; la decisión de promoción se registrará separadamente del estado de ejecución.

#### Scenario: Fin de una comparación
- **WHEN** una ejecución termina y supera sus verificaciones
- **THEN** su fila de resultados y detalle de cambios aparecen en el informe sin esperar a que finalicen los demás experimentos, incluso si su promoción fue rechazada.

#### Scenario: Artefacto alterado
- **WHEN** el hash de un artefacto no coincide o sus métricas no se pueden reproducir
- **THEN** la ejecución no se presenta como completada y verificada, conserva el fallo y bloquea su promoción.

### Requirement: Antecedentes y evidencia pendiente diferenciados
El sistema SHALL importar las ejecuciones anteriores con su procedencia, estado real y limitaciones. MUST registrar experimentos nuevos sin resultados como pendientes y fuentes o dependencias ausentes con su motivo, sin adjudicarles métricas históricas ni inventar rendimientos o disponibilidad.

#### Scenario: Importación de la fase regional
- **WHEN** se incorpora el resultado histórico regional-20261003
- **THEN** se conserva el RMSE principal 0.749458 t/ha y su promoción rechazada como antecedente, sin asignarlos a E01 o a una ejecución nueva.

#### Scenario: Dependencia opcional ausente
- **WHEN** el candidato opcional no puede ejecutarse con dependencias y pesos verificables
- **THEN** se registra como omitido con motivo y los experimentos obligatorios continúan, sin eliminar esquemas obligatorios de su criterio de aceptación.

### Requirement: Recuperación de versiones y conservación de la activa
El sistema SHALL conservar versiones completas recuperables de controles y candidatos, con código, dependencias, tablas necesarias, modelos, contratos, predicciones y manifiestos. MUST mantener intacta la versión activa durante los experimentos y distinguir ejecución completada, elegibilidad para promoción y activación efectiva.

#### Scenario: Experimento candidato
- **WHEN** una ejecución cumple todos sus criterios
- **THEN** se prepara un paquete verificable y se registra su elegibilidad sin afirmar una activación, despliegue o envío que no se realizó.

#### Scenario: Recuperación del control
- **WHEN** se reproduce un control histórico
- **THEN** se usa su versión íntegra y sus contratos originales, sin modificar hashes para aceptar código incompatible.

### Requirement: Evidencia y cierre de la fase hídrica
El sistema SHALL relacionar cada hipótesis hídrica con auditoría de datos, control, protocolo congelado y resultado real. MUST separar fuentes existentes, verificadas, no viables y pendientes; variables disponibles, elegibles y utilizadas en cada ajuste; y antecedente, diagnóstico aislado y combinado elegible. SHALL conservar comparaciones pareadas por esquema, decisiones internas por bloque, diferencias por parcela y paquetes recuperables, con la advertencia de reutilización de las mismas etiquetas.

#### Scenario: Suelo no adquirido
- **WHEN** la auditoría de acceso no recupera capas válidas
- **THEN** el informe publica el motivo y los bloques no ejecutados sin adjudicarles métricas ni afirmar que se descartó científicamente el papel del suelo.

#### Scenario: Variable mostrada pero no utilizada
- **WHEN** pendiente o NDWI existe en las tablas pero no participa en el modelo final
- **THEN** el informe identifica su disponibilidad y su exclusión final, evitando afirmar que el predictor usa esa variable.

#### Scenario: Cierre verificable
- **WHEN** una ejecución recupera contratos, modelos y 59 consultas en un proceso nuevo sin red y reproduce métricas externas
- **THEN** se registra completada y verificada, con elegibilidad separada y activación, despliegue y envío en falso.
