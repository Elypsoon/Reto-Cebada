"""Cinco ramas oficiales con soporte explícito y ejes auditables."""
import numpy as np
import pandas as pd
from .common import ID, START, CUTOFF, PROCESSED, EXTERNAL, sha256, write_json
from .priority_selectors import ENVIRONMENT
from .segments import reconstruct_segments
from .external import read_nasa

BRANCHES = {'s2_ndvi': ('Sentinel-2', 'ndvi'), 's2_evi': ('Sentinel-2', 'evi'),
            'planet_ndvi': ('Planet', 'ndvi'), 'planet_msavi': ('Planet', 'msavi'),
            'landsat_vi6t': ('Landsat', 'vi6t')}
START_DATE, END_DATE = pd.Timestamp(START), pd.Timestamp(CUTOFF)
SEASON_DAYS = (END_DATE - START_DATE).days
QUALITY = tuple(f'quality_{branch}_{field}' for branch in BRANCHES
                for field in ('observations', 'supported_fraction'))


def supported_branches(master, satellite):
    if not master[ID].is_unique or len(master) != 197:
        raise ValueError('Población parcelaria incompatible')
    if not set(satellite[ID]).issubset(set(master[ID])):
        raise ValueError('Observación de parcela ajena')
    clean = satellite.loc[satellite.date.between(START, CUTOFF) &
                          satellite.porcentaje_nubosidad.le(20)]
    branches = {}
    quality = pd.DataFrame(index=pd.Index(master[ID], name=ID), columns=QUALITY, dtype=float)
    for branch, (sensor, index) in BRANCHES.items():
        column = f'{index}_promedio'
        if column not in clean:
            raise ValueError(f'Índice estructuralmente ausente: {sensor}/{index}')
        sensor_data = clean.loc[clean.sensor.eq(sensor)]
        groups = {pid: group for pid, group in sensor_data.groupby(ID)}
        for pid in master[ID]:
            group = groups.get(pid, sensor_data.iloc[:0])
            group = group.loc[np.isfinite(group[column])]
            pieces, curves, report = reconstruct_segments(group, column, lam=10)
            accepted = group.date.nunique()
            days = sum(item['supported_days'] for item in report)
            quality.loc[pid, f'quality_{branch}_observations'] = accepted
            quality.loc[pid, f'quality_{branch}_supported_fraction'] = days / SEASON_DAYS
            branches[(pid, branch)] = {'pieces': pieces, 'report': report, 'column': column,
                                     'sensor': sensor, 'index': index, 'accepted_observations': accepted}
    return branches, quality


def common_covariates(monthly, quality):
    if not monthly.index.is_unique or not quality.index.is_unique:
        raise ValueError('Covariables duplicadas')
    if set(monthly.index) != set(quality.index) or any(c not in monthly for c in ENVIRONMENT):
        raise ValueError('Covariables ambientales o población incompatibles')
    result = monthly[list(ENVIRONMENT)].join(quality[list(QUALITY)], validate='one_to_one')
    if any(c not in result for c in QUALITY) or len(result) != 197:
        raise ValueError('Calidad compartida incompleta')
    return result


def thermal_axis(frame):
    expected = pd.date_range(START, CUTOFF)
    if not frame.index.equals(expected):
        raise ValueError('Temperaturas diarias incompletas o duplicadas')
    lo, hi = frame.T2M_MIN, frame.T2M_MAX
    if not (np.isfinite(lo).all() and np.isfinite(hi).all() and (lo <= hi).all() and
            lo.between(-80, 60).all() and hi.between(-60, 70).all()):
        raise ValueError('Temperaturas diarias incompatibles')
    increments = (lo.clip(0, 26) + hi.clip(0, 26)) / 2
    accumulated = increments.cumsum()
    return accumulated - accumulated.iloc[0], float(increments.sum())


def audited_thermal_context(master):
    frames, reports = read_nasa()
    assignments = pd.read_csv(PROCESSED / 'nasa-cells.csv')
    if (len(assignments) != 197 or not assignments[ID].is_unique or
            set(assignments[ID]) != set(master[ID])):
        raise ValueError('Mapeo NASA incompatible')
    axes, totals = {}, {}
    for cell, frame in frames.items():
        axes[cell], totals[cell] = thermal_axis(frame)
    parcel_axes, parcel_totals = {}, {}
    for row in assignments.itertuples(index=False):
        cell = (row.longitude, row.latitude)
        if cell not in axes:
            raise ValueError('Celda no pertenece a respuesta nativa auditada')
        parcel_axes[getattr(row, ID)] = axes[cell]
        parcel_totals[getattr(row, ID)] = totals[cell]
    report = {'start': START, 'cutoff': CUTOFF, 'base_C': 0, 'cap_C': 26,
              'origin': 'G(t)-G(2025-04-01)', 'units': 'grado-día',
              'interpretation': 'Contexto regional desde origen convencional; siembra no observada.',
              'mapping_source_sha256': sha256(PROCESSED / 'nasa-cells.csv'),
              'daily_sources': {p.name: sha256(p) for p in sorted(EXTERNAL.glob('nasa*.json'))},
              'native_cells': len(frames), 'cells_used': assignments.groupby(['longitude', 'latitude']).size()
                  .rename('parcels').reset_index().to_dict(orient='records'), 'original_audit': reports}
    return parcel_axes, pd.Series(parcel_totals, name='nasa_gdd_total').rename_axis(ID), report


def summarize_branch(branch, axis=None):
    """Cada segmento se integra por separado; coordenadas repetidas llevan su peso."""
    maximum = float(axis.iloc[-1]) if axis is not None else float(SEASON_DAYS)
    if maximum <= 0:
        raise ValueError('Eje temporal sin rango')
    parts, original_parts, rejected = [], [], 0
    auc, support = 0., 0.
    for original, curve in branch['pieces']:
        x = (axis.reindex(pd.DatetimeIndex(curve.date)).to_numpy() if axis is not None else
             (curve.date - START_DATE).dt.days.to_numpy(dtype=float))
        if not np.isfinite(x).all():
            raise ValueError('Eje incompleto en segmento observado')
        # Peso uniforme por bin semanal, conservando el número de bins coincidentes.
        piece = pd.DataFrame({'x': x, 'value': curve.value.to_numpy(), 'weight': 1.})
        repeated = piece.groupby('x', sort=True).agg(total=('value', 'sum'), weight=('weight', 'sum'))
        repeated['value'] = repeated.total / repeated.weight
        if len(repeated) < 2:
            rejected += 1
            continue
        integral = float(np.trapezoid(repeated.value, repeated.index.to_numpy()))
        duration = float(repeated.index[-1] - repeated.index[0])
        auc += integral
        support += duration
        parts.append(repeated.reset_index())
        original_parts.append(original)
    result = {f'mean_{name}': np.nan for name in ['early', 'middle', 'late']}
    result.update(supported_integral=auc if support > 0 else np.nan,
                  supported_axis=support, auc_per_supported_axis=auc/support if support > 0 else np.nan,
                  local_max=np.nan, peak_coordinate=np.nan, repeated_axis_segments_rejected=rejected)
    if parts:
        accepted = pd.concat(parts, ignore_index=True)
        window = np.minimum((accepted.x.to_numpy()/maximum*3).astype(int), 2)
        for j, name in enumerate(['early', 'middle', 'late']):
            selected = accepted.loc[window == j]
            if len(selected):
                result[f'mean_{name}'] = float(np.average(selected.value, weights=selected.weight))
        result['local_max'] = float(accepted.value.max())
        originals = pd.concat(original_parts).drop_duplicates('date')
        if len(originals) >= 8:
            peak = accepted.loc[accepted.value.idxmax(), 'x']
            ox = (axis.reindex(pd.DatetimeIndex(originals.date)).to_numpy() if axis is not None else
                  (originals.date-START_DATE).dt.days.to_numpy())
            if (ox < peak).sum() >= 2 and (ox > peak).sum() >= 2:
                result['peak_coordinate'] = float(peak)
    return result


def summary_table(master, branches, covariates, axes=None):
    rows, diagnostics = [], []
    for pid in master[ID]:
        row = {ID: pid}
        for branch in BRANCHES:
            values = summarize_branch(branches[(pid, branch)], None if axes is None else axes[pid])
            diagnostics.append({ID: pid, 'branch': branch, **values,
                                'integral_units': 'índice × día' if axes is None else 'índice × grado-día'})
            for field in ['mean_early', 'mean_middle', 'mean_late', 'auc_per_supported_axis', 'local_max']:
                row[f'{branch}_{field}'] = values[field]
        rows.append(row)
    return pd.DataFrame(rows).set_index(ID).join(covariates, validate='one_to_one'), diagnostics
