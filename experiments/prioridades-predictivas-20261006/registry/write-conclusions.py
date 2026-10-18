"""Síntesis de los resultados registrados; no selecciona una receta nueva."""
import json
from pathlib import Path
from agrocebada.common import ROOT


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


states = read(ROOT/'registry/priority-summary.json')
decision = read(ROOT/'registry/P06-eligibility.json')
intervals = read(ROOT/'runs/P06/artifacts/intervals.json')
stress = read(ROOT/'runs/P06/artifacts/stress.json')
assert len(states) == 12 and all(s['predictively_tested'] for s in states)
lines = ['# Conclusiones de la evaluación prioritaria', '',
    'Se completaron las 12 ejecuciones predeclaradas de P00–P08 y su recuperación sin red. P06 no es elegible para sustituir el modelo activo. TabPFN-3 mensual ofrece una señal favorable en los tres esquemas, pero sigue siendo un diagnóstico experimental y no modifica esa decisión.', '',
    'Las métricas usan las mismas 138 etiquetas de una campaña, abril–octubre de 2025. Las 59 consultas no tienen etiquetas para medir exactitud. La repetición de investigaciones sobre estas etiquetas limita la fuerza de cualquier mejora observada; no se afirma validación en una nueva campaña ni haber agotado todos los modelos posibles.', '',
    '| Procedimiento | RMSE principal | RMSE balanceado | RMSE rotado |',
    '| --- | --- | --- | --- |']
for state in states:
    metrics = state['metrics']
    values = [metrics[s]['official']['rmse'] if state['block'] == 'P00' else metrics[s]['rmse']
              for s in ['principal-5', 'balanceado-4', 'rotado-45-5']]
    lines.append('| '+state['run_id']+' | '+' | '.join(f'{v:.6f}' for v in values)+' |')
lines += ['', 'Todas las cifras de RMSE están en t/ha; menor es mejor. Las filas P00 usan su ruta oficial. Las rutas seleccionadas de los controles, MAE, sesgo, estado, superficie y fold están en [resultados completos](priority-results.md) y `detailed-results.json`.', '',
    '## Decisión P06', '',
    'Los umbrales quedaron congelados antes de los resultados. Fallaron las siguientes condiciones: mejora principal de al menos 2% frente a media regional; mejora de al menos 2% en dos esquemas; razón media ≤0,98 frente a media regional; protección de MAE por estado; mejora principal de al menos 2% frente a la activa; y deterioro máximo de 5% en cualquier esquema frente a la activa.', '',
    f"En principal, P06 mejora {(1-decision['active_ratios']['principal-5'])*100:.2f}% frente a la activa, por debajo del 2% exigido, y empeora {(decision['regional_ratios']['principal-5']-1)*100:.2f}% frente a media regional. En rotado empeora {(decision['active_ratios']['rotado-45-5']-1)*100:.2f}% frente a la activa.", '',
    '| Esquema | Estado | n | MAE P06 | MAE media regional | Aumento |',
    '| --- | --- | --- | --- | --- | --- |']
for failure in decision['state_failures']:
    lines.append(f"| {failure['scheme']} | {failure['state']} | {failure['n']} | {failure['mae']:.6f} | {failure['regional_mae']:.6f} | {(failure['mae']/failure['regional_mae']-1)*100:.2f}% |")
lines += ['', 'La protección estatal permite como máximo 10% de aumento de MAE en estados con al menos diez etiquetas. La receta P06 no se reconfiguró con ganadores externos. Se conserva también la decisión negativa E08 histórica. Activación, despliegue y envío permanecen en false.', '',
    '## Qué aportan las comparaciones', '',
    '- La lista agronómica mejora frente al ranking en 20/24 pares del esquema principal y 20/24 del balanceado; el efecto es menos uniforme en rotado. Esto apoya revisar el filtro, pero la selección anidada P01 no produce una mejora estable entre los tres esquemas.',
    '- El tiempo térmico gana en dos de cuatro pares por esquema y pierde en otros dos, con diferencias medianas pequeñas. Esta comparación mantiene el mismo contexto NASA y no se atribuye a la ruta oficial.',
    '- La covarianza estatal GPR ayuda en algunos pares; el efecto estatal Ridge empeora en todos los pares comparados. La estructura regional necesita soporte suficiente: un fold rotado no tiene etiquetas de Tlaxcala en entrenamiento.',
    '- Las dos interacciones EBM mejoran sus pares aditivos en los tres esquemas, aunque el procedimiento P04 no mejora de forma estable frente a los controles. Las curvas funcionales tampoco muestran una ventaja consistente.',
    '- TabICL v2 mensual tiene el menor RMSE rotado entre estas configuraciones fijas. TabPFN-3 mensual mejora frente a la activa en los tres esquemas. Son procedimientos diagnósticos separados: no se selecciona una tabla, se mezclan pesos ni se incorporan a P06 a partir de esas OOF.', '',
    'Los [405 contrastes de mecanismos](mechanism-comparisons.md) y la comparación pareada con TabPFN 2.5 (`optional-vs-TabPFN25.json`) conservan tanto resultados favorables como negativos. Sus mínimos individuales son descriptivos y no sustituyen la selección interna.', '',
    '## Sensibilidad e intervalos', '',
    '| Sensibilidad P06 | Exclusión | Estado | Train | Validación | RMSE | Motivo |',
    '| --- | --- | --- | --- | --- | --- | --- |']
for item in stress:
    lines.append(f"| {item['kind']} | {item['held_out']} | {item['status']} | {len(item['train_ids'])} | {len(item['validation_ids'])} | {format(item['metrics']['rmse'], '.6f') if 'metrics' in item else '—'} | {item.get('reason', '—')} |")
lines += ['', 'Las sensibilidades inviables no se cuentan como predicciones evaluadas ni se promedian con las completadas. Los casos de estado ausente completados verificaron la media global exacta; los buffers usan distancia entre polígonos y mínimo de 1000 m.', '',
    f"Los intervalos de nominal 90% cubren {intervals['coverage']*100:.2f}% de las 138 etiquetas en el esquema principal, con amplitud media {intervals['mean_width']:.3f} t/ha. La calibración final reserva {intervals['final_calibration_n']} etiquetas. La disponibilidad de intervalos ({intervals['available']}) es una comprobación separada de la elegibilidad puntual y no revierte el rechazo P06. El detalle por estado está en `runs/P06/artifacts/intervals.json`.", '',
    '## Cobertura y recuperación', '',
    'La [matriz de evidencia y cobertura](evidence-and-coverage.md) vincula P00–P08 con L01–L08, controles, estados y artefactos reales. BART, TabM, NGBoost, radar, ERA5, SoilGrids, AlphaEarth, simulación completa de cultivo y variantes de mayor complejidad siguen explícitamente diferidos; no fueron probados en esta fase.', '',
    'Pasaron 47 pruebas de cierre. Se verificaron los 12 paquetes, tres entornos de dependencias, las 59 consultas por ruta y las métricas recalculadas. Los 133 archivos protegidos siguen intactos. Las 12 versiones históricas convencionales reprodujeron ambas rutas y los dos contextos TabPFN 2.5 recuperaron sus consultas con el entorno original. El intento histórico fallido bajo ajustes numéricos nuevos permanece documentado.', '',
    'Véanse [recuperación](recovery.md), `registry/package-verification.json` y `registry/final-integrity-receipt.json` para recibos y límites de reproducción.']
(ROOT/'docs/conclusions.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('Conclusiones escritas desde 12 ejecuciones verificadas', flush=True)
