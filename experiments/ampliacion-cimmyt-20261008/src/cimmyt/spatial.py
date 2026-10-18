"""Admisión de puntos asumidos; distancias inferiores en ECEF, nunca en grados."""
from dataclasses import dataclass
import hashlib
import math
import numpy as np
import pandas as pd

PROTOCOL = 'cimmyt-point-assumption-v2'
GRID = {'latitude_step': .5, 'longitude_step': .625, 'latitude_origin': -90.,
        'longitude_origin': -180., 'nodes_are_cell_centers': True,
        'source': 'NASA MERRA-2 native grid; POWER meteorology',
        'reference': 'https://gmao.gsfc.nasa.gov/pubs/docs/Collow1437.pdf'}


@dataclass(frozen=True)
class Policy:
    name: str
    margin: float
    buffer_m: float


POLICIES = (Policy('narrow', .001, 1000.), Policy('principal', .01, 2000.), Policy('wide', .02, 3000.))
PRINCIPAL = POLICIES[1]


def validate_evidence(evidence=None):
    evidence = evidence or {}
    if evidence.get('source_crs', 'unknown') not in ['unknown', 'EPSG:4326']:
        raise ValueError('Referencia posterior incompatible: revisar protocolo antes de ajustar')
    if float(evidence.get('documented_uncertainty_degrees', 0)) > PRINCIPAL.margin:
        raise ValueError('Incertidumbre posterior mayor: revisar protocolo antes de ajustar')


def coherent(lat, lon):
    return bool(np.isfinite([lat, lon]).all() and 0 <= lat <= 35 and -120 <= lon <= -85)


def point_bounds(lat, lon, policy=PRINCIPAL):
    if not coherent(lat, lon):
        raise ValueError('Punto incompatible con controles de coherencia; no corregir signos/ejes')
    return (lon-policy.margin, lat-policy.margin, lon+policy.margin, lat+policy.margin)


def single_cell(bounds):
    """Caja cerrada estrictamente interior; contacto con frontera no se desempata."""
    west, south, east, north = bounds
    if not (west <= east and south <= north):
        raise ValueError('Caja inválida')
    node = []
    for low, high, origin, step in [(west, east, -180., .625), (south, north, -90., .5)]:
        center = origin + math.floor(((low+high)/2-origin)/step + .5)*step
        if low <= center-step/2+1e-10 or high >= center+step/2-1e-10:
            return None
        node.append(center)
    return tuple(node)  # longitude, latitude


def coordinate_rows(frame, policy=PRINCIPAL, evidence=None):
    validate_evidence(evidence)
    result = frame.copy()
    reasons, cells, bounds = [], [], []
    for row in result.itertuples():
        if not coherent(row.latitude, row.longitude):
            reasons.append('incoherent_point'); cells.append(None); bounds.append(None)
            continue
        b = point_bounds(row.latitude, row.longitude, policy)
        cell = single_cell(b)
        reasons.append(None if cell else 'ambiguous_cell_or_boundary')
        cells.append(cell); bounds.append(b)
    result['spatial_reason'] = pd.Series(reasons, index=result.index, dtype='string')
    result['cell_lon'] = [c[0] if c else np.nan for c in cells]
    result['cell_lat'] = [c[1] if c else np.nan for c in cells]
    for i, field in enumerate(['west', 'south', 'east', 'north']):
        result[field] = [b[i] if b else np.nan for b in bounds]
    result['source_crs'] = 'unknown'
    result['analysis_crs'] = 'EPSG:4326'
    result['crs_basis'] = 'explicit_assumption'
    result['location_kind'] = 'approximate_point'
    result['point_semantics'] = 'unknown'
    result['spatial_protocol'] = PROTOCOL
    result['spatial_policy'] = policy.name
    return result


def _trig_interval(lo, hi, func):
    samples = [lo, hi] + [k*math.pi/2 for k in range(math.ceil(lo/(math.pi/2)), math.floor(hi/(math.pi/2))+1)]
    values = [func(x) for x in samples]
    return min(values), max(values)


def ecef_bounds(bounds):
    """Caja XYZ que contiene TODOS los puntos de la caja geográfica WGS84 (altura 0).

    N*cos(phi) decrece con |phi|; N*(1-e2)*sin(phi) es creciente.
    Productos de intervalos cubren extremos interiores de sin/cos(lambda).
    No se aproxima la caja mediante su centro o solo cuatro esquinas.
    """
    west, south, east, north = bounds
    if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
        raise ValueError('Caja geográfica incompatible')
    a, flattening = 6378137., 1/298.257223563
    e2 = flattening*(2-flattening)
    def radial(phi):
        return a*math.cos(phi)/math.sqrt(1-e2*math.sin(phi)**2)
    def vertical(phi):
        return a*(1-e2)*math.sin(phi)/math.sqrt(1-e2*math.sin(phi)**2)
    low, high = math.radians(south), math.radians(north)
    rv = [radial(low), radial(high)] + ([a] if low <= 0 <= high else [])
    rlo, rhi = min(rv), max(rv)
    limits = []
    for trig in [math.cos, math.sin]:
        tlo, thi = _trig_interval(math.radians(west), math.radians(east), trig)
        products = [rlo*tlo, rlo*thi, rhi*tlo, rhi*thi]
        limits.append((min(products), max(products)))
    limits.append((vertical(low), vertical(high)))
    return np.array([v[0] for v in limits]), np.array([v[1] for v in limits])


def distance_lower_bound(aux_bounds, polygon_bounds):
    """Distancia entre cajas ECEF <= cuerda <= distancia sobre el elipsoide.

    La caja geográfica oficial contiene el polígono (segmentos en CRS4326).
    Puede excluir de más; jamás acredita una distancia exacta a la parcela.
    1 cm adicional protege frente a redondeo de cálculos en doble precisión.
    """
    amin, amax = ecef_bounds(aux_bounds)
    bmin, bmax = ecef_bounds(polygon_bounds)
    return max(0., float(np.linalg.norm(np.maximum(0., np.maximum(amin-bmax, bmin-amax))))-.01)


def support(frame):
    counts = {'labels': len(frame), 'groups': int(frame.dependence_group.nunique()),
              'campaigns': int(frame.year.nunique())}
    return dict(counts, viable=counts['labels'] >= 30 and counts['groups'] >= 10 and counts['campaigns'] >= 2)


def keys_hash(keys):
    return hashlib.sha256('\n'.join(sorted(str(k) for k in keys)).encode()).hexdigest()


class SpatialGuard:
    def __init__(self, candidates, official, policy=PRINCIPAL):
        if official.crs is None or official.crs.to_epsg() != 4326:
            raise ValueError('Guardia exige geometría oficial con referencia 4326 verificada')
        if not official.geometry.is_valid.all() or official.geometry.is_empty.any():
            raise ValueError('Geometría oficial inválida')
        self.policy = policy
        self.rows = coordinate_rows(candidates, policy)
        self.official_ids = list(official.index)
        self.distances = pd.DataFrame(np.inf, index=self.rows.index, columns=self.official_ids)
        for ix, row in self.rows.iterrows():
            # También controlar los puntos del grupo cuya celda climática es ambigua.
            if pd.notna(row.spatial_reason) and row.spatial_reason == 'incoherent_point':
                continue
            box = tuple(row[f] for f in ['west', 'south', 'east', 'north'])
            for pid, polygon in official.geometry.items():
                self.distances.loc[ix, pid] = distance_lower_bound(box, polygon.bounds)

    def admit(self, cohort, retained_ids=()):
        retained_ids = list(dict.fromkeys(retained_ids))
        if not set(retained_ids).issubset(self.official_ids):
            raise ValueError('Parcela retenida ajena al maestro oficial')
        pool = self.rows if cohort == 'C-mexico' else self.rows[self.rows.candidate_local] if cohort == 'C-local' else None
        if pool is None:
            raise ValueError('Cohorte no autorizada')
        mins = self.distances[retained_ids].min(axis=1) if retained_ids else pd.Series(np.inf, index=self.rows.index)
        near = mins.le(self.policy.buffer_m)
        blocked = set(self.rows.loc[near, 'dependence_group'])
        reasons = pool.spatial_reason.copy()
        reasons.loc[pool.dependence_group.isin(blocked)] = 'group_within_buffer'
        accepted = pool.loc[reasons.isna()].copy()
        exclusions = [{'auxiliary_id': str(row.auxiliary_id), 'group': str(row.dependence_group),
            'reason': str(reasons.loc[ix]), 'distance_lower_bound_m': None if not np.isfinite(mins.loc[ix]) else float(mins.loc[ix])}
            for ix, row in pool.loc[reasons.notna()].iterrows()]
        contract = {'policy': self.policy.name, 'margin_degrees': self.policy.margin, 'buffer_m': self.policy.buffer_m,
            'retained_ids': retained_ids, 'keys': accepted.auxiliary_id.tolist(),
            'keys_sha256': keys_hash(accepted.auxiliary_id), 'support': support(accepted), 'exclusions': exclusions,
            'distance_method': 'lower_bound_ECEF_AABB_chord_WGS84_height0_minus_0.01m',
            'spatial_separation_certified': False}
        return accepted, contract
