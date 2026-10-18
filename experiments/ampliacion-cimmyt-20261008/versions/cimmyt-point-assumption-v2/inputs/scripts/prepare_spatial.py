"""Cohortes y sensibilidad de admisión sin leer etiquetas oficiales ni consultar red."""
import geopandas as gpd
import pandas as pd
from cimmyt.common import ROOT, ID, SCHEMES, save, digest
from cimmyt.spatial import PROTOCOL, GRID, POLICIES, SpatialGuard, coordinate_rows, keys_hash

official = gpd.read_parquet(ROOT/'data/processed/parcels.parquet').set_index(ID)
candidates = pd.read_parquet(ROOT/'data/processed/cimmyt-label-candidates.parquet')
assert candidates.auxiliary_id.is_unique and candidates.auxiliary_id.str.startswith('cimmyt:v6:').all()
assert candidates.dependence_group.notna().all()
assert not set(candidates.auxiliary_id).intersection(official.index)
assert candidates.groupby('plot').dependence_group.nunique().max() == 1
known = candidates.dropna(subset=['farmer'])
assert known.groupby('farmer').dependence_group.nunique().max() == 1
rows = coordinate_rows(candidates)
rows.to_parquet(ROOT/'data/processed/cimmyt-spatial-candidates.parquet', index=False)
cohorts = {}
for name, pool in [('C-local', rows[rows.candidate_local]), ('C-mexico', rows)]:
    pool.to_parquet(ROOT/f'data/processed/{name}-candidates.parquet', index=False)
    cohorts[name] = {'candidate_count': len(pool), 'groups': int(pool.dependence_group.nunique()),
        'plots': int(pool['plot'].nunique()), 'campaigns': int(pool.year.nunique()),
        'known_farmers': int(pool.farmer.nunique()), 'keys': pool.auxiliary_id.tolist(),
        'keys_sha256': keys_hash(pool.auxiliary_id), 'training_admission_pending': True}
save(ROOT/'registry/cohorts.json', {'protocol': PROTOCOL, 'cohorts': cohorts,
    'input_sha256': digest(ROOT/'data/processed/cimmyt-label-candidates.parquet')})
schemes = pd.read_csv(ROOT/'registry/schemes.csv')
records = []
for policy in POLICIES:
    guard = SpatialGuard(candidates, official, policy)
    for cohort in cohorts:
        _, contract = guard.admit(cohort)
        records.append(dict(contract, cohort=cohort, scheme=None, outer_fold=None, inner_fold=None, stage='population'))
    for scheme in SCHEMES:
        part = schemes[schemes.scheme.eq(scheme)].set_index(ID).fold
        for outer in sorted(part.unique()):
            outer_ids = part.index[part.eq(outer)].tolist()
            for cohort in cohorts:
                _, contract = guard.admit(cohort, outer_ids)
                records.append(dict(contract, cohort=cohort, scheme=scheme, outer_fold=int(outer), inner_fold=None, stage='outer'))
            for inner in sorted(part[~part.eq(outer)].unique()):
                retained = outer_ids + part.index[part.eq(inner)].tolist()
                for cohort in cohorts:
                    _, contract = guard.admit(cohort, retained)
                    records.append(dict(contract, cohort=cohort, scheme=scheme, outer_fold=int(outer), inner_fold=int(inner), stage='inner'))
    print('Política de admisión comprobada:', policy.name, flush=True)
matched = {}
for record in records:
    key = (record['cohort'], record['scheme'], record['outer_fold'], record['inner_fold'], record['stage'])
    matched.setdefault(key, []).append((record['keys_sha256'], record['support']['viable']))
changed = sum(len(set(values)) > 1 for values in matched.values())
principal = [r for r in records if r['policy'] == 'principal']
summary = {cohort: {'population': next(r['support'] for r in principal if r['cohort'] == cohort and r['stage'] == 'population'),
    'viable_outer_fits': sum(r['support']['viable'] for r in principal if r['cohort'] == cohort and r['stage'] == 'outer'),
    'viable_inner_fits': sum(r['support']['viable'] for r in principal if r['cohort'] == cohort and r['stage'] == 'inner')}
    for cohort in cohorts}
save(ROOT/'registry/spatial-admission.json', {'protocol': PROTOCOL, 'grid': GRID,
    'official_geometry_sha256': digest(ROOT/'data/processed/parcels.parquet'),
    'candidate_sha256': digest(ROOT/'data/processed/cimmyt-label-candidates.parquet'),
    'schemes_sha256': digest(ROOT/'registry/schemes.csv'), 'principal_summary': summary,
    'geographic_sensitivity': 'detected' if changed else 'not_detected_in_tested_policies',
    'changed_fit_populations': changed, 'training_performed': False, 'climate_requests': 0, 'records': records})
print('Admisión principal:', summary, 'cambios de sensibilidad:', changed)
