"""Contrato de población y particiones importadas por identificador."""
import numpy as np
import pandas as pd
from .common import ID, TARGET, CUTOFF

SCHEMES = {'principal-5': 5, 'balanceado-4': 4, 'rotado-45-5': 5, 'intraestado-3': 3}


def validate_population_and_schemes(master, assignments, cutoff=CUTOFF):
    if cutoff != '2025-10-31':
        raise ValueError('Corte incompatible')
    labeled = master[TARGET].notna()
    if (len(master) != 197 or not master[ID].is_unique or labeled.sum() != 138 or
            (~labeled).sum() != 59 or not np.isfinite(master.loc[labeled, TARGET]).all() or
            not master.loc[labeled, TARGET].gt(0).all()):
        raise ValueError('Población incompatible: 197 IDs, 138 etiquetas y 59 consultas')
    if not (master.loc[labeled, 'CONJUNTO'].eq('ENTRENAMIENTO').all() and
            master.loc[~labeled, 'CONJUNTO'].eq('PREDICCION').all()):
        raise ValueError('Etiquetas ocultas o conjunto incompatible')
    if assignments.duplicated([ID, 'scheme']).any() or set(assignments.scheme) != set(SCHEMES):
        raise ValueError('Particiones duplicadas o esquemas incompatibles')
    required_ids = set(master.loc[labeled, ID])
    report = {}
    for name, folds in SCHEMES.items():
        part = assignments.loc[assignments.scheme.eq(name)]
        if len(part) != 138 or set(part[ID]) != required_ids or part.fold.isna().any():
            raise ValueError('IDs/folds no corresponden a etiquetas oficiales')
        if set(part.fold) != set(range(folds)):
            raise ValueError('Número o identidad de folds incompatible')
        counts = part.fold.value_counts().sort_index()
        if counts.min() < 15 or 138 - counts.max() < 80:
            raise ValueError('Tamaño mínimo de train/validación incumplido')
        report[name] = {'counts': {str(k): int(v) for k, v in counts.items()},
                        'minimum_train': int(138-counts.max()), 'valid': True}
    return {'cutoff': cutoff, 'total': 197, 'labeled': 138, 'hidden': 59, 'schemes': report}
