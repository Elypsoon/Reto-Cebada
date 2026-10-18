"""Detecta antes de congelar la discrepancia entre modelos y recetas de ensamble."""
from prepare_phase import PHASE, PROJECT, save, digest

ENSEMBLES = [('family_1', 'family_2'), ('regional_mean', 'family_1'),
             ('regional_mean', 'family_2'), ('regional_mean', 'family_1', 'family_2')]
COUNTS = {'P01': (2*3*4*3+2, 74), 'P02': (2*4+2, 10), 'P03': (2*(4*3+3*2)+2, 38),
          'P04': ((2*3+2*2)*3+2, 32), 'P05': ((2+3)+2*(2+3), 47), 'P06': (2*(3*2+3*2)+2, 26)}


def main():
    rows = []
    for block, (base, limit) in COUNTS.items():
        if block == 'P05':
            base = base*3+2
        rows.append({'block': block, 'models_corrections_and_references': base,
                     'declared_maximum': limit, 'ensemble_recipes': len(ENSEMBLES),
                     'total_with_ensembles': base+len(ENSEMBLES),
                     'within_160': base+len(ENSEMBLES) <= 160,
                     'exceeds_declared_maximum': base+len(ENSEMBLES) > limit})
    design = PROJECT / 'openspec/changes/evaluacion-predictiva-prioritaria-con-evidencia/design.md'
    save(PHASE / 'registry/candidate-budget-review.json', {
         'design_sha256': digest(design), 'status': 'corrected_with_user_authorization', 'training_started': False,
         'rows': rows, 'ensemble_recipes': ENSEMBLES,
         'issue': 'Los máximos incluyen modelos/correcciones/referencias, pero omiten las cuatro recetas de ensamble que el diseño exige contabilizar.',
         'proposed_resolution': 'Conservar todos los modelos y las cuatro recetas existentes; actualizar máximos a 78/14/42/36/51/30 antes de congelar.',
         'protocol_frozen': False, 'new_metrics': None,'corrected_maximums':{r['block']:r['total_with_ensembles'] for r in rows},
         'authorization':'Sí, corrige y sigue; autorizado antes de congelar.'})
    lines = ['# Revisión del presupuesto de candidatos', '',
             'Conteo corregido con autorización del usuario antes de congelar o evaluar etiquetas externas.', '',
             'El diseño exige contar ensambles antes de congelar. Los máximos actuales cuentan modelos, correcciones y referencias; faltan cuatro recetas de promedio uniforme ya declaradas.', '',
             '| Bloque | Máximo actual | Recetas de ensamble | Total propuesto |',
             '| --- | --- | --- | --- |']
    lines += [f"| {r['block']} | {r['declared_maximum']} | {r['ensemble_recipes']} | {r['total_with_ensembles']} |" for r in rows]
    lines += ['', 'Propuesta: conservar modelos, parámetros y ensambles; corregir solamente su contabilización. Todos los bloques siguen bajo el límite general de 160.', '',
              'Corrección aplicada: máximos 78/14/42/36/51/30, sin retirar modelos ni ensambles.', '',
              'La selección de componentes de cada ensamble sigue siendo interna; no se multiplica retrospectivamente la grilla con ganadores externos.']
    (PHASE/'docs/candidate-budget-review.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('Presupuesto corregido: 78/14/42/36/51/30 contando cuatro recetas de ensamble.')


if __name__ == '__main__':
    main()
