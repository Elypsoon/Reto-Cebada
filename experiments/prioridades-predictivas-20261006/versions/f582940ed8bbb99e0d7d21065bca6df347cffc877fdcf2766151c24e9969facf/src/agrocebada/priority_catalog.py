"""Catálogo P01–P06 y cuatro recetas predeclaradas por bloque."""
from dataclasses import dataclass, asdict, replace
from itertools import product
import hashlib
import json

MAXIMUMS = {'P01': 78, 'P02': 14, 'P03': 42, 'P04': 36, 'P05': 51, 'P06': 30}
ENSEMBLES = [('family_1', 'family_2'), ('regional_mean', 'family_1'),
             ('regional_mean', 'family_2'), ('regional_mean', 'family_1', 'family_2')]


@dataclass(frozen=True)
class PriorityCandidate:
    representation: str
    family: str
    selector: str = 'all'
    setting: float = 1.
    state_setting: object = None
    knots: int = 3
    components: int = 0
    kind: str = 'direct'
    alpha: float = 1.
    interactions: str = 'none'

    @property
    def id(self):
        value = json.dumps(asdict(self), sort_keys=True, separators=(',', ':'))
        return self.family + '-' + hashlib.sha256(value.encode()).hexdigest()[:16]


def candidates(block):
    C = PriorityCandidate
    representations = ['monthly_20_10', 'whittaker_20_10']
    if block == 'P01':
        base = [C(rep, family, mode, value) for rep, mode, (family, value) in
                product(representations, ['rank', 'agronomic', 'all'],
                        [('gpr', 1), ('gpr', 5), ('catboost', 2), ('catboost', 3)])]
    elif block == 'P02':
        base = [C(rep, family, 'all', value) for rep, (family, value) in
                product(['calendar_nasa', 'thermal'], [('gpr', 1), ('gpr', 5), ('catboost', 2), ('catboost', 3)])]
    elif block == 'P03':
        base = [C(rep, 'hierarchical_ridge', 'agronomic', a, state)
                for rep, state, a in product(representations, [1, 10, 50, 'infinite'], [.1, 1, 10])]
        base += [C(rep, 'hierarchical_gpr', 'agronomic', length, variance)
                 for rep, variance, length in product(representations, [0, .25, 1], [1, 5])]
    elif block == 'P04':
        base = [C('monthly_20_10', 'gam', 'agronomic', a, knots=k)
                for k, a in product([3, 4], [1, 10, 100])]
        base += [C('monthly_20_10', 'ebm', 'agronomic', bins, interactions=interactions)
                 for bins, interactions in product([8, 16], ['none', 'fixed_pairs'])]
    elif block == 'P05':
        base = [C('calendar', f, 'all', a) for f, a in [('gpr', 1), ('gpr', 5), ('ridge', .1), ('ridge', 1), ('ridge', 10)]]
        base += [C('functional', f, 'all', a, components=q) for q, (f, a) in
                 product([2, 3], [('gpr', 1), ('gpr', 5), ('ridge', .1), ('ridge', 1), ('ridge', 10)])]
    elif block == 'P06':
        base = [C(rep, 'hierarchical_gpr', 'all', length, variance, components=2 if rep == 'functional' else 0)
                for rep, variance, length in product(['compact', 'functional'], [0, .25, 1], [1, 5])]
        base += [C(rep, 'hierarchical_gam', 'all', a, state, knots=3, components=2 if rep == 'functional' else 0)
                 for rep, state, a in product(['compact', 'functional'], [1, 10, 50], [1, 10])]
    else:
        raise ValueError('Bloque no reconocido')
    if block in ['P01', 'P04', 'P05']:
        base += [replace(c, kind='regional_correction', alpha=alpha) for c in list(base) for alpha in [.5, 1.]]
    base += [C(base[0].representation, family) for family in ['global_mean', 'regional_mean']]
    if len(set(c.id for c in base)) != len(base):
        raise ValueError('Candidatos duplicados')
    if len(base) + len(ENSEMBLES) != MAXIMUMS[block]:
        raise ValueError('Presupuesto diferente del diseño corregido')
    if len({c.family for c in base if not c.family.endswith('_mean')}) != 2:
        raise ValueError('Deben conservarse dos familias por bloque')
    if len({c.representation for c in base}) > 2 or len(base) + len(ENSEMBLES) > 160:
        raise ValueError('Bloque fuera de presupuesto')
    return base


def serial_catalog():
    result = {block: {'candidates': [dict(asdict(c), id=c.id) for c in candidates(block)],
                    'ensemble_recipes': ENSEMBLES, 'total': MAXIMUMS[block], 'optional': False}
            for block in MAXIMUMS}
    result['P00'] = {'controls':['C-activa','C-soporte'],'optional':False,
                     'procedure':'Código histórico exacto; grillas separadas en controles/provenance/procedure.json',
                     'routes':['official','selected'],'seconds_limit':7200}
    for block,name in [('P07','tabicl-v2'),('P08','tabpfn-3')]:
        result[block] = {'model':name,'optional':True,'ensemble_recipes':[],
                        'configurations':['monthly_20_10','whittaker_20_10'],'total':2,
                        'n_estimators':8,'seed':2026,'device':'cpu','rss_limit_mb':4096,
                        'seconds_limit_per_configuration':1800,'select_by_outer_oof':False,'enters_P06':False}
    return dict(sorted(result.items()))
