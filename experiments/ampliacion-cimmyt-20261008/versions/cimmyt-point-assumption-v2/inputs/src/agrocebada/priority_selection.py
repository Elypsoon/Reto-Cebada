"""Selección anidada completa; cada candidato conserva todos los inner-folds."""
from dataclasses import asdict
import numpy as np
from .modeling import metric, admission
from .priority_adapter import FittedCandidate, FittedProcedure
from .priority_catalog import candidates as catalog_candidates, ENSEMBLES


def choose(scores):
    minimum = min(s['rmse'] for s in scores)
    tied = [s for s in scores if s['rmse'] <= minimum + 1e-10]
    return min(tied, key=lambda s: (not s['candidate'].family.endswith('_mean'),
               s['candidate'].kind != 'direct', s['candidate'].components,
               s['candidate'].knots, s['candidate'].id))


def cross_validate(candidate, train_ids, target, groups, tables):
    ids = np.asarray(train_ids)
    y = target.loc[ids].to_numpy(dtype=float)
    fold = groups.loc[ids].to_numpy()
    if len(np.unique(fold)) < 2:
        raise ValueError('Menos de dos grupos internos')
    prediction = np.full(len(ids), np.nan)
    fits = []
    for group in sorted(np.unique(fold)):
        tr, va = ids[fold != group], ids[fold == group]
        model = FittedCandidate(candidate).fit(tables[candidate.representation].loc[tr], target.loc[tr])
        prediction[fold == group] = model.predict(tables[candidate.representation].loc[va])
        fits.append({'fold': int(group), 'train_ids': tr.tolist(), 'validation_ids': va.tolist(),
                     'contract': model.contract()})
    if not np.isfinite(prediction).all():
        raise ValueError('Predicción interna incompleta')
    return {'candidate': candidate, 'rmse': metric(y, prediction)['rmse'], 'prediction': prediction,
            'fold': fold, 'fits': fits}


def select(block, train_ids, target, groups, states, tables, grid=None, progress=None):
    grid = catalog_candidates(block) if grid is None else grid
    scores, failed = [], []
    for index, candidate in enumerate(grid):
        try:
            scores.append(cross_validate(candidate, train_ids, target, groups, tables))
        except (ValueError, np.linalg.LinAlgError) as error:
            if candidate.family.endswith('_mean'):
                raise
            failed.append({'candidate_id': candidate.id, 'reason': str(error),
                           'excluded_from_selection': True, 'averaged_partial_folds': False})
        if progress:
            progress(index+1, len(grid))
    reference_scores = [s for s in scores if s['candidate'].family.endswith('_mean')]
    if len(reference_scores) != 2:
        raise ValueError('Referencias completas obligatorias')
    reference = choose(reference_scores)
    regional = next(s for s in reference_scores if s['candidate'].family == 'regional_mean')
    ids = np.asarray(train_ids)
    y, state, fold = target.loc[ids].to_numpy(), states.loc[ids].to_numpy(), groups.loc[ids].to_numpy()
    families = sorted({c.family for c in grid if not c.family.endswith('_mean')})
    winners = {f: choose([s for s in scores if s['candidate'].family == f])
               for f in families if any(s['candidate'].family == f for s in scores)}
    decisions, eligible = [], []
    for score in winners.values():
        gate = admission(score['prediction'], reference['prediction'], y, state, fold)
        decisions.append({'candidate_id': score['candidate'].id, 'kind': 'family_winner', **gate})
        if gate['admitted']:
            eligible.append(score)
    best = choose(eligible) if eligible else reference
    pool = {'regional_mean': regional}
    pool.update({f'family_{j+1}': winners[f] for j, f in enumerate(families) if f in winners})
    ensemble_options = []
    for recipe in ENSEMBLES:
        if not all(name in pool for name in recipe):
            decisions.append({'kind': 'ensemble', 'recipe': list(recipe), 'admitted': False,
                              'reason': 'Familia inviable en algún inner-fold'})
            continue
        parts = [pool[name] for name in recipe]
        prediction = np.column_stack([s['prediction'] for s in parts]).mean(axis=1)
        current = admission(prediction, best['prediction'], y, state, fold)
        baseline = admission(prediction, reference['prediction'], y, state, fold)
        accepted = current['admitted'] and baseline['admitted']
        decisions.append({'kind': 'ensemble', 'recipe': list(recipe), 'admitted': bool(accepted),
                          'against_current': current, 'against_reference': baseline,
                          'component_ids': [s['candidate'].id for s in parts]})
        if accepted:
            ensemble_options.append({'rmse': metric(y, prediction)['rmse'], 'parts': parts, 'recipe': recipe})
    selected = [best['candidate']]
    strategy = best['candidate'].id
    if ensemble_options:
        minimum = min(s['rmse'] for s in ensemble_options)
        option = min([s for s in ensemble_options if s['rmse'] <= minimum+1e-10],
                     key=lambda s: (len(s['parts']), s['recipe']))
        selected = [s['candidate'] for s in option['parts']]
        strategy = '+'.join(option['recipe'])
    return {'candidates': selected, 'weights': [1/len(selected)]*len(selected), 'strategy': strategy,
            'train_ids': ids.tolist(), 'decisions': decisions, 'failures': failed,
            'scores': [{'candidate': dict(asdict(s['candidate']), id=s['candidate'].id), 'rmse': s['rmse'],
                        'prediction': s['prediction'].tolist(), 'fold': s['fold'].tolist(), 'fits': s['fits']}
                       for s in scores]}


def fit_selection(selection, target, tables):
    ids = selection['train_ids']
    models = [FittedCandidate(c).fit(tables[c.representation].loc[ids], target.loc[ids])
              for c in selection['candidates']]
    return FittedProcedure(selection['candidates'], models)


def calibrate(block, train_ids, target, groups, states, tables, grid=None):
    ids = np.asarray(train_ids)
    fold = groups.loc[ids].to_numpy()
    options = [g for g in sorted(set(fold)) if (fold == g).sum() >= 25]
    if not options:
        return None
    group = min(options, key=lambda g: (int((fold == g).sum()), int(g)))
    cal_ids, fit_ids = ids[fold == group], ids[fold != group]
    if len(fit_ids) < 45 or len(set(groups.loc[fit_ids])) < 2:
        return None
    selection = select(block, fit_ids, target, groups, states, tables, grid=grid)
    model = fit_selection(selection, target, tables)
    center = model.predict(tables, cal_ids)
    residual = np.abs(target.loc[cal_ids].to_numpy()-center)
    level = min(1., np.ceil((len(cal_ids)+1)*.9)/len(cal_ids))
    return {'model': model, 'selection': selection, 'radius': float(np.quantile(residual, level, method='higher')),
            'calibration_ids': cal_ids.tolist(), 'fit_ids': fit_ids.tolist(), 'nominal': .9}
