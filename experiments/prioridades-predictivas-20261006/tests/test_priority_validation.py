import numpy as np
import pandas as pd
from agrocebada.common import ID, TARGET
from agrocebada.priority_validation import SCHEMES, evaluate_eligibility, interval_summary


def frames():
    frame = pd.DataFrame({ID: [f'ID{i}' for i in range(138)], TARGET: 3.,
          'Estado': ['Puebla']*71+['Hidalgo']*36+['Tlaxcala']*31,
          'spatial_group': np.arange(138)%5, 'official': 3.1, 'regional_mean': 3.5})
    candidate = {s: frame.copy() for s in SCHEMES}
    active = {s: frame.assign(official=3.4) for s in SCHEMES}
    return candidate, active


def test_diagnostic_and_missing_controls_never_promote():
    candidate, active = frames()
    assert evaluate_eligibility('P06', candidate, active, True, True)['eligible']
    assert not evaluate_eligibility('P07', candidate, active, True, True)['eligible']
    assert not evaluate_eligibility('P06', candidate, active, True, False)['eligible']
    del candidate['balanceado-4']
    assert not evaluate_eligibility('P06', candidate, active, True, True)['eligible']


def test_puebla_rotated_protection_and_active_gain_required():
    candidate, active = frames()
    candidate['rotado-45-5'].loc[candidate['rotado-45-5'].Estado.eq('Puebla'), 'official'] = 3.6
    result = evaluate_eligibility('P06', candidate, active, True, True)
    assert not result['eligible'] and any(v['state'] == 'Puebla' for v in result['state_failures'])
    candidate, active = frames()
    active['principal-5']['official'] = 3.09
    assert not evaluate_eligibility('P06', candidate, active, True, True)['checks']['principal_active_gain']


def test_interval_gate_below_85pct_or_insufficient_calibration():
    candidate, _ = frames()
    frame = candidate['principal-5'].assign(interval_low=2.9, interval_high=3.1)
    calibration = {'calibration_ids': list(range(25))}
    assert interval_summary(frame, calibration)['available']
    frame.loc[:21, 'interval_low'] = 3.05  # 116/138 <85%
    assert not interval_summary(frame, calibration)['available']
    frame['interval_low'] = 2.9
    assert not interval_summary(frame, {'calibration_ids': list(range(24))})['available']
