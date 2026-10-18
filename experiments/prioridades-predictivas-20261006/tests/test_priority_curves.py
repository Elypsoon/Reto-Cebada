import numpy as np
import pandas as pd
import pytest
from agrocebada.priority_curves import thermal_axis, summarize_branch, START_DATE, SEASON_DAYS
from agrocebada.segments import reconstruct_segments


def test_gdd_manual_and_origin():
    dates = pd.date_range('2025-04-01', '2025-10-31')
    frame = pd.DataFrame({'T2M_MIN': 10., 'T2M_MAX': 30.}, index=dates)
    axis, total = thermal_axis(frame)
    assert total == len(dates)*18 and axis.iloc[0] == 0 and axis.iloc[-1] == SEASON_DAYS*18
    frame.iloc[0] = [-10., 20.]
    axis, total = thermal_axis(frame)
    assert total == 10+(len(dates)-1)*18 and axis.iloc[1] == 18
    with pytest.raises(ValueError):
        thermal_axis(frame.iloc[1:])
    frame.iloc[3, 0] = np.nan
    with pytest.raises(ValueError):
        thermal_axis(frame)


def test_long_gap_remains_unintegrated_and_units_follow_axis():
    dates = pd.to_datetime(['2025-04-01', '2025-04-08', '2025-04-15', '2025-04-22',
                            '2025-08-01', '2025-08-08', '2025-08-15', '2025-08-22'])
    observations = pd.DataFrame({'date': dates, 'v': 1., 'porcentaje_nubosidad': 0.})
    pieces, _, _ = reconstruct_segments(observations, 'v')
    assert len(pieces) == 2
    calendar = summarize_branch({'pieces': pieces})
    axis = pd.Series(np.arange(SEASON_DAYS+1)*2., index=pd.date_range('2025-04-01', '2025-10-31'))
    thermal = summarize_branch({'pieces': pieces}, axis)
    assert calendar['supported_axis'] == 42
    assert abs(calendar['supported_integral'] - 42) < 1e-8
    assert thermal['supported_axis'] == 84
    assert abs(thermal['supported_integral'] - 84) < 1e-8
    assert abs(thermal['auc_per_supported_axis'] - 1) < 1e-8


def test_repeated_thermal_times_no_artificial_increment():
    dates = pd.date_range('2025-04-01', periods=4, freq='7D')
    observations = pd.DataFrame({'date': dates, 'v': [1., 2., 3., 4.], 'porcentaje_nubosidad': 0.})
    pieces, _, _ = reconstruct_segments(observations, 'v')
    axis = pd.Series(0., index=pd.date_range('2025-04-01', '2025-10-31'))
    axis.iloc[40:] = 5.
    summary = summarize_branch({'pieces': pieces}, axis)
    assert summary['supported_axis'] == 0
    assert np.isnan(summary['supported_integral'])
    assert summary['repeated_axis_segments_rejected'] == 1
