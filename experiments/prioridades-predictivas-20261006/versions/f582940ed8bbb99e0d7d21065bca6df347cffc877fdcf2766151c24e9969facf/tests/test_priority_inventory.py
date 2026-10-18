import numpy as np
import pandas as pd
from agrocebada.common import ROOT, ID
from agrocebada.priority_curves import BRANCHES, QUALITY, common_covariates
from agrocebada.priority_selectors import ENVIRONMENT


def test_same_covariates_and_quality_for_both_axes():
    processed = ROOT / 'data/processed'
    master = pd.read_parquet(processed / 'parcels.parquet')
    quality = pd.read_parquet(processed / 'priority-quality.parquet')
    covariates = pd.read_parquet(processed / 'priority-covariates.parquet')
    calendar = pd.read_parquet(processed / 'features_priority_calendar_nasa.parquet')
    thermal = pd.read_parquet(processed / 'features_priority_thermal.parquet')
    assert len(quality) == 197 and quality.index.is_unique
    assert set(quality.index) == set(master[ID])
    assert quality.columns.tolist() == list(QUALITY)
    assert len(BRANCHES) == 5 and len(QUALITY) == 10 and len(ENVIRONMENT) == 9
    assert not any('ndre' in c or 'landsat_evi' in c for c in covariates)
    assert np.isfinite(quality.to_numpy()).all()
    assert quality.filter(like='supported_fraction').le(1).all().all()
    for frame in [calendar, thermal]:
        assert frame.index.is_unique and len(frame) == 197
        pd.testing.assert_frame_equal(frame[list(covariates)], covariates)
    pd.testing.assert_series_equal(calendar.nasa_gdd_total, thermal.nasa_gdd_total)
