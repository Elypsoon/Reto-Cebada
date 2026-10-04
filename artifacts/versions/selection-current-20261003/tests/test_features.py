import numpy as np
import pandas as pd
from agrocebada.features import season,integral,reconstruct


def test_cutoff_and_independent_years():
    d=pd.DataFrame({"date":pd.to_datetime(["2024-06-01","2025-06-01","2025-11-01"])})
    assert season(d).date.tolist()==[pd.Timestamp("2025-06-01")]


def test_integral_uses_real_days():
    dates=pd.to_datetime(["2025-04-01","2025-04-03","2025-04-11"])
    assert integral(dates,[2,2,2])==20


def test_long_gap_does_not_fabricate_peak():
    dates=pd.to_datetime(["2025-04-01","2025-04-08","2025-04-15","2025-04-22","2025-06-01","2025-06-08","2025-06-15","2025-06-22"])
    d=pd.DataFrame({"date":dates,"ndvi_promedio":np.linspace(.2,.8,8),"porcentaje_nubosidad":0})
    curve,reason=reconstruct(d,"ndvi_promedio")
    assert curve.empty and "21" in reason
def test_integral_pandas_series():
    import pandas as pd
    from agrocebada.features import integral
    assert integral(pd.Series(pd.to_datetime(["2025-04-01","2025-04-11"])),pd.Series([2.,2.]))==20.
