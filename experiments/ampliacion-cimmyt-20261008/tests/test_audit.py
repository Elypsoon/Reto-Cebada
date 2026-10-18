import numpy as np
import pandas as pd
import pytest
from cimmyt.audit import FARMER_MAP, YIELD_MAP, safe_join, harmonize, dependence_groups


def inputs(n=1):
    rows, farmers = [], []
    for i in range(n):
        identity = {'farmer': f'f{i}', 'plot': f'p{i}', 'logbook': f'l{i}', 'practice': f't{i}',
                    'state': 'HIDALGO', 'year': '2018', 'season': 'SUMMER', 'regime': 'RAINFED'}
        row = {name: pd.NA for name in YIELD_MAP.values()}
        row.update(identity, yield_id=f'y{i}', product='GRAIN', unit='TON', yield_original='3.5',
                   sowing='2018-05-01', harvest_start='2018-09-15', harvest_end='2018-09-16',
                   treatment_area='2', activity='SOWING', crop='BARLEY', sowing_id=f's{i}')
        rows.append(row)
        farmer = {name: pd.NA for name in FARMER_MAP.values()}
        farmer.update(identity, logbook_duplicate=identity['logbook'], latitude='19.5', longitude='-98.125',
                      area_survey='2', area_satellite='2')
        farmers.append(farmer)
    return pd.DataFrame(rows).astype('string'), pd.DataFrame(farmers).astype('string')


def test_logbook_with_two_treatments_does_not_multiply_rows():
    y, f = inputs(2)
    y.loc[1, 'logbook'] = f.loc[1, 'logbook'] = f.loc[1, 'logbook_duplicate'] = 'l0'
    assert len(safe_join(y, f)) == 2
    with pytest.raises(ValueError, match='no única'):
        safe_join(y, pd.concat([f, f.iloc[[0]]], ignore_index=True))


def test_zero_yield_is_preserved_and_kg_conversion_explicit():
    y, f = inputs(2)
    y.loc[0, 'yield_original'] = '0'
    y.loc[1, ['unit', 'yield_original']] = ['KG', '3500']
    _, admitted, _ = harmonize(y, f)
    assert admitted.yield_t_ha.tolist() == [0., 3.5]


@pytest.mark.parametrize('field,value,expected', [
    ('product', 'FORAGE', 'not_barley_grain'),
    ('unit', 'BALE', 'invalid_grain_unit_or_yield'),
    ('treatment_area', '0', 'invalid_treatment_area'),
    ('activity', 'RESEED', 'resowing_or_unknown_activity'),
    ('harvest_end', '2019-09-16', 'outside_window_harvest_end'),
    ('harvest_start', '2018-11-01', 'outside_window_harvest_start'),
    ('harvest_start', None, 'outside_window_harvest_start'),
    ('harvest_start', '2018-04-01', 'dates_out_of_order'),
])
def test_invalid_products_units_and_dates_are_excluded(field, value, expected):
    y, f = inputs()
    y.loc[0, field] = value
    rows, admitted, _ = harmonize(y, f)
    assert admitted.empty and rows.loc[0, 'reason'] == expected


def test_winter_irrigation_excluded_without_invented_context():
    y, f = inputs()
    y.loc[0, ['season', 'regime']] = ['WINTER', 'IRRIGATION']
    f.loc[0, ['season', 'regime']] = ['WINTER', 'IRRIGATION']
    rows, admitted, _ = harmonize(y, f)
    assert admitted.empty and rows.loc[0, 'reason'] == 'outside_summer_rainfed'


def test_duplicate_yield_and_conflicts_have_different_reasons():
    y, f = inputs()
    rows, admitted, _ = harmonize(pd.concat([y, y], ignore_index=True), f)
    assert len(admitted) == 1 and rows.reason.eq('duplicate_yield_id').sum() == 1
    conflict = pd.concat([y, y], ignore_index=True)
    conflict.loc[1, 'yield_original'] = '9'
    rows, admitted, _ = harmonize(conflict, f)
    assert admitted.empty and rows.reason.eq('conflicting_yield_id').all()


def test_same_plot_campaign_treatments_are_not_averaged():
    y, f = inputs(2)
    y.loc[1, ['farmer', 'plot', 'logbook']] = ['f0', 'p0', 'l0']
    f.loc[1, ['farmer', 'plot', 'logbook', 'logbook_duplicate']] = ['f0', 'p0', 'l0', 'l0']
    rows, admitted, _ = harmonize(y, f)
    assert admitted.empty and rows.reason.eq('multiple_treatments_or_harvests_unresolved').all()


def test_dependence_components_link_years_and_producer_changes():
    frame = pd.DataFrame({'plot': ['a', 'a', 'b', 'c', None], 'farmer': ['f1', 'f2', 'f2', None, 'f3']})
    groups = dependence_groups(frame)
    assert groups.iloc[0] == groups.iloc[1] == groups.iloc[2]
    assert groups.iloc[3] != groups.iloc[0] and pd.isna(groups.iloc[4])


def test_repeated_logbook_header_disagreement_rejected():
    y, f = inputs()
    f.loc[0, 'logbook_duplicate'] = 'different'
    with pytest.raises(ValueError, match='discordantes'):
        harmonize(y, f)
