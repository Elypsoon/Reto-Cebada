"""Promoción de P06 exclusivamente y disponibilidad separada de intervalos."""
import numpy as np
from .common import ID, TARGET
from .modeling import metric

SCHEMES = ['principal-5', 'balanceado-4', 'rotado-45-5']


def evaluate_eligibility(block, frames, active_frames, verified=False, controls_reproduced=False):
    checks = {'official_combined_only': block == 'P06', 'three_complete_schemes': True,
              'controls_reproduced': bool(controls_reproduced), 'verification': bool(verified)}
    ratios, active_ratios, failures, invalid = {}, {}, [], []
    for scheme in SCHEMES:
        candidate, active = frames.get(scheme), active_frames.get(scheme)
        if candidate is None or active is None:
            invalid.append(scheme)
            continue
        a, b = candidate.set_index(ID).sort_index(), active.set_index(ID).sort_index()
        needed = ['official', 'regional_mean', TARGET]
        if (len(a) != 138 or not a.index.is_unique or not a.index.equals(b.index) or
                not np.isfinite(a[needed].to_numpy()).all() or
                not np.isfinite(b.official).all() or not np.array_equal(a[TARGET], b[TARGET]) or
                not np.array_equal(a.spatial_group, b.spatial_group)):
            invalid.append(scheme)
            continue
        error = metric(a[TARGET], a.official)['rmse']
        regional_error, active_error = metric(a[TARGET], a.regional_mean)['rmse'], metric(b[TARGET], b.official)['rmse']
        ratios[scheme] = error/regional_error if regional_error > 0 else np.inf
        active_ratios[scheme] = error/active_error if active_error > 0 else np.inf
        for state, part in a.groupby('Estado'):
            c, r = metric(part[TARGET], part.official)['mae'], metric(part[TARGET], part.regional_mean)['mae']
            if len(part) >= 10 and c > 1.1*r+1e-12:
                failures.append({'scheme': scheme, 'state': state, 'n': len(part), 'mae': c, 'regional_mae': r})
    checks.update(three_complete_schemes=len(ratios) == 3 and not invalid,
        principal_gain=ratios.get(SCHEMES[0], np.inf) <= .98,
        two_schemes_gain=sum(v <= .98 for v in ratios.values()) >= 2,
        mean_ratio=len(ratios) == 3 and np.mean(list(ratios.values())) <= .98,
        none_above_105=len(ratios) == 3 and max(ratios.values()) <= 1.05,
        regional_protection=not failures,
        principal_active_gain=active_ratios.get(SCHEMES[0], np.inf) <= .98,
        none_above_active_105=len(active_ratios) == 3 and max(active_ratios.values()) <= 1.05)
    return {'eligible': bool(all(checks.values())), 'activated': False, 'deployed': False, 'sent': False,
            'checks': {k: bool(v) for k, v in checks.items()}, 'regional_ratios': ratios,
            'active_ratios': active_ratios, 'state_failures': failures, 'invalid_schemes': invalid,
            'evidence': 'Desarrollo sobre las mismas 138 etiquetas; sin otra campaña validada.'}


def interval_summary(frame, final_calibration=None):
    valid = np.isfinite(frame.interval_low)&np.isfinite(frame.interval_high)
    covered = frame[TARGET].between(frame.interval_low, frame.interval_high)
    coverage = float(covered[valid].mean()) if valid.any() else None
    cal_n = len(final_calibration['calibration_ids']) if final_calibration else 0
    return {'nominal': .9, 'valid_n': int(valid.sum()), 'n': len(frame), 'coverage': coverage,
            'mean_width': float((frame.interval_high-frame.interval_low)[valid].mean()) if valid.any() else None,
            'final_calibration_n': cal_n, 'available': bool(len(frame) == 138 and valid.all() and
               coverage is not None and coverage >= .85 and cal_n >= 25),
            'by_state': {state: {'n': len(part), 'valid_n': int(valid.loc[part.index].sum()),
                  'coverage': float(covered.loc[part.index][valid.loc[part.index]].mean()) if valid.loc[part.index].any() else None,
                  'mean_width': float((part.interval_high-part.interval_low)[valid.loc[part.index]].mean()) if valid.loc[part.index].any() else None}
                         for state, part in frame.groupby('Estado')},
            'limitation': 'Cobertura de desarrollo; disponibilidad separada de elegibilidad puntual.'}
