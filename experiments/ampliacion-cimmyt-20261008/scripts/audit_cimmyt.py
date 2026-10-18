import pandas as pd
from cimmyt.common import ROOT, save, read, digest
from cimmyt.audit import FARMER_MAP, YIELD_MAP, harmonize

farmers = pd.read_parquet(ROOT/'data/processed/cimmyt-farmer.parquet').rename(columns=FARMER_MAP)
yields = pd.read_parquet(ROOT/'data/processed/cimmyt-barley.parquet').rename(columns=YIELD_MAP)
joined, candidates, stages = harmonize(yields, farmers)
joined.to_parquet(ROOT/'data/processed/cimmyt-audit-rows.parquet', index=False)
candidates.to_parquet(ROOT/'data/processed/cimmyt-label-candidates.parquet', index=False)
def counts(frame):
    return {'rows': len(frame), 'yield_ids': int(frame.yield_id.nunique()), 'plots': int(frame['plot'].nunique()),
            'known_farmers': int(frame.farmer.nunique()), 'campaigns': int(frame.year.nunique()),
            'groups': int(frame.dependence_group.nunique()), 'states': {str(k): int(v) for k,v in frame.state.value_counts().items()}}
report = {'status': 'labels_audited_spatial_metadata_pending', 'published_barley_records': 968,
    'downloaded_barley_rows': len(yields), 'unique_yield_ids': int(yields.yield_id.nunique()),
    'grain_rows': int(yields['product'].eq('GRAIN').sum()), 'grain_unique_yield_ids': int(yields.loc[yields['product'].eq('GRAIN'), 'yield_id'].nunique()),
    'join': {'keys': ['logbook', 'practice'], 'validation': 'many_to_one', 'rows_before': len(yields), 'rows_after': len(joined),
       'unmatched': int(joined['_merge'].eq('left_only').sum())},
    'stages': stages, 'before_spatial': {'C-local': counts(candidates[candidates.candidate_local]), 'C-mexico': counts(candidates)},
    'admitted_training_labels': None, 'official_modality': 'not documented in official originals reviewed',
    'official_moisture_basis': 'unknown', 'external_measurement_method': 'heterogeneous, not identified per row',
    'coordinate_metadata': {'fields': ['LATITUDE N','LONGITUDE W'], 'datum_or_crs_in_catalog': None,
         'polygon_vertices_in_download': False, 'article_privacy_precision': 'vertices truncated to 3 decimals',
         'status': 'requires documented interpretation before spatial admission'},
    'files': {n:digest(ROOT/'data/raw'/n) for n in read(ROOT/'registry/cimmyt-schema.json') if n.endswith('.xlsx')}}
save(ROOT/'registry/label-audit.json', report)
save(ROOT/'registry/column-map.json', {'farmer': FARMER_MAP, 'yield': YIELD_MAP,
    'units': {'TON/HA': '1 t/ha', 'KG/HA': '0.001 t/ha'}, 'area': 'hectares of sowing under the identified treatment',
    'source_schema_sha256': digest(ROOT/'registry/cimmyt-schema.json')})
print('Candidatos de etiqueta antes de admisión espacial:', report['before_spatial'])
print('Etiquetas auxiliares admitidas para entrenar: pendientes de metadatos espaciales; no equivalen a cero registros existentes')
