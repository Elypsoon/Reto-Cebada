"""Armonización verificable sin inferir unidades, fechas o ubicación desconocidas."""
import numpy as np
import pandas as pd

FARMER_MAP = {'LOGBOOK ID': 'logbook', 'LOGBOOK ID__2': 'logbook_duplicate',
    'FARMER ID': 'farmer', 'PLOT ID': 'plot', 'STATE': 'state', 'YEAR': 'year',
    'WINTER/SUMMER \u00a0SEASON': 'season', 'HYDRIC REGIME': 'regime',
    'LATITUDE N': 'latitude', 'LONGITUDE W': 'longitude',
    'INNOVATION/CONVENTIONAL_PRACTICES_ID': 'practice',
    'TOTAL PLOT AREA (HA) DATA OBTAINED BY SURVEY WITH THE FARMER': 'area_survey',
    'AREA (HA) APPROACH DATA CALCULATED BY THE DELIMITATION OF THE PLOT IN SATELLITE IMAGE': 'area_satellite'}
YIELD_MAP = {'FARMER.ID': 'farmer', 'PLOT.ID': 'plot', 'LOGBOOK.ID': 'logbook',
    'STATE': 'state', 'YEAR': 'year', 'WINTER/SUMER.\u00a0SEASON': 'season', 'HYDRIC.REGIME': 'regime',
    'INNOVATION/CONVENTIONAL_PRACTICES_ID': 'practice', 'YIELD.ID': 'yield_id',
    'PRODUCT.OBTAINED': 'product', 'UNIT.OF.MEASURE/HA': 'unit', 'ACTUAL.YIELD.(UNIT/HA)': 'yield_original',
    'CROP.SOWING.DATE': 'sowing',
    'HARVEST.DATE.(FIRST.ACTIVITY.IN.THE.PLOT.BY.PRODUCTION.CYCLE)': 'harvest_start',
    'HARVEST.DATE.(LAST.ACTIVITY.IN.THE.PLOT.BY.PRODUCTION.CYCLE': 'harvest_end',
    'AREA.(HA).SOWING.WHIT.INNOVATION.OR.CONVENTIONAL.PRACTICES': 'treatment_area',
    'ACTIVITY.PERFORMED': 'activity', 'CROP': 'crop', 'SOWING.ID.(PRIMARY.KEY)': 'sowing_id'}


def safe_join(yields, farmers):
    """La clave de tratamiento evita duplicar la bitácora compartida por tratamientos."""
    keys = ['logbook', 'practice']
    if farmers[keys].isna().any().any() or farmers.duplicated(keys).any():
        raise ValueError('Clave de bitácora/tratamiento no única; unión rechazada')
    result = yields.merge(farmers, on=keys, how='left', validate='many_to_one',
                          suffixes=('', '_farmer'), indicator=True)
    if len(result) != len(yields):
        raise ValueError('Unión multiplicó rendimientos')
    return result


def dependence_groups(frame):
    """Componente conexo: productor enlaza parcelas y parcela enlaza campañas/productores."""
    parents = {}
    def find(x):
        parents.setdefault(x, x)
        while parents[x] != x:
            parents[x] = parents[parents[x]]
            x = parents[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        parents[max(a, b)] = min(a, b)
    for row in frame.itertuples():
        if pd.isna(row.plot):
            continue
        plot = 'plot:' + str(row.plot)
        find(plot)
        if pd.notna(row.farmer):
            union(plot, 'farmer:' + str(row.farmer))
    return pd.Series(['cimmyt:' + find('plot:' + str(p)) if pd.notna(p) else pd.NA for p in frame['plot']], index=frame.index, dtype='string')


def harmonize(yields, farmers):
    required_y = set(YIELD_MAP.values())
    required_f = set(FARMER_MAP.values())
    if not required_y.issubset(yields.columns) or not required_f.issubset(farmers.columns):
        raise ValueError('Faltan columnas canónicas verificadas')
    if not farmers['logbook'].equals(farmers['logbook_duplicate']):
        raise ValueError('Columnas LOGBOOK ID discordantes en original')
    joined = safe_join(yields, farmers)
    joined['source_row'] = np.arange(len(joined))
    joined['reason'] = pd.Series(pd.NA, index=joined.index, dtype='string')
    steps = []
    def retain(condition, reason):
        condition = condition.fillna(False).astype(bool)
        active = joined.reason.isna()
        joined.loc[active & ~condition, 'reason'] = reason
        steps.append({'stage': reason, 'remaining_rows': int(joined.reason.isna().sum()),
                      'excluded_here': int((active & ~condition).sum())})
    retain(joined['_merge'].eq('both'), 'unmatched_logbook_practice')
    for name in ['farmer', 'plot', 'state', 'year', 'season', 'regime']:
        peer = name + '_farmer'
        if peer in joined:
            # El productor puede faltar; la parcela y el resto del contexto son obligatorios.
            match = joined[name].eq(joined[peer])
            if name == 'farmer':
                match = match | (joined[name].isna() & joined[peer].isna())
            retain(match, 'context_mismatch_' + name)
    retain(joined.crop.eq('BARLEY') & joined['product'].eq('GRAIN'), 'not_barley_grain')
    retain(joined.yield_id.notna() & joined['plot'].notna() & joined.logbook.notna() & joined.practice.notna(), 'missing_identity')
    signatures = ['farmer', 'plot', 'logbook', 'practice', 'year', 'season', 'regime', 'product', 'unit',
                  'yield_original', 'sowing', 'harvest_start', 'harvest_end', 'treatment_area', 'sowing_id']
    grain = joined[joined.reason.isna()]
    conflicts = grain.groupby('yield_id')[signatures].nunique(dropna=False).max(axis=1)
    bad = set(conflicts[conflicts > 1].index)
    retain(~joined.yield_id.isin(bad), 'conflicting_yield_id')
    duplicate = joined.loc[joined.reason.isna()].duplicated('yield_id', keep='first')
    duplicate_rows = set(duplicate.index[duplicate])
    retain(~joined.index.to_series().isin(duplicate_rows), 'duplicate_yield_id')
    joined['yield_t_ha'] = pd.to_numeric(joined.yield_original, errors='coerce') * joined.unit.map({'TON': 1., 'KG': .001})
    retain(joined.unit.isin(['TON', 'KG']) & np.isfinite(joined.yield_t_ha) & joined.yield_t_ha.ge(0), 'invalid_grain_unit_or_yield')
    joined['area_ha'] = pd.to_numeric(joined.treatment_area, errors='coerce')
    retain(np.isfinite(joined.area_ha) & joined.area_ha.gt(0), 'invalid_treatment_area')
    joined['year'] = pd.to_numeric(joined['year'], errors='coerce')
    retain(joined.year.between(2012, 2022) & joined.year.mod(1).eq(0), 'invalid_campaign')
    retain(joined.season.eq('SUMMER') & joined.regime.eq('RAINFED'), 'outside_summer_rainfed')
    retain(joined.activity.eq('SOWING'), 'resowing_or_unknown_activity')
    dates = {}
    for name in ['sowing', 'harvest_start', 'harvest_end']:
        dates[name] = pd.to_datetime(joined[name], errors='coerce', format='mixed')
        retain(dates[name].notna() & dates[name].dt.year.eq(joined.year) & dates[name].dt.month.between(4, 10), 'outside_window_' + name)
    retain(dates['sowing'].le(dates['harvest_start']) & dates['harvest_start'].le(dates['harvest_end']), 'dates_out_of_order')
    # Varias observaciones del mismo grano/parcela/campaña no se agregan sin evidencia incremental.
    unresolved = joined.loc[joined.reason.isna()].duplicated(['plot', 'year', 'season', 'product'], keep=False)
    retain(~joined.index.to_series().isin(unresolved.index[unresolved]), 'multiple_treatments_or_harvests_unresolved')
    joined['latitude'] = pd.to_numeric(joined.latitude, errors='coerce')
    joined['longitude'] = pd.to_numeric(joined.longitude, errors='coerce')
    retain(np.isfinite(joined.latitude) & np.isfinite(joined.longitude), 'missing_coordinates')
    joined['auxiliary_id'] = 'cimmyt:v6:' + joined.logbook.astype('string') + ':' + joined.practice.astype('string') + ':' + joined.yield_id.astype('string')
    joined['dependence_group'] = dependence_groups(joined)
    candidates = joined[joined.reason.isna()].copy()
    candidates['candidate_local'] = candidates.state.isin(['PUEBLA', 'HIDALGO', 'TLAXCALA'])
    return joined, candidates, steps
