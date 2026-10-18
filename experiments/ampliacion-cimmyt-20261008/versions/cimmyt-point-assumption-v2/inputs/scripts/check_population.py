import geopandas as gpd
import pandas as pd
from cimmyt.common import ROOT, ID, TARGET, SCHEMES, read, save, digest

master = gpd.read_parquet(ROOT / 'data/processed/parcels.parquet')
groups = pd.read_csv(ROOT / 'registry/schemes.csv')
assert len(master) == 197 and master[ID].is_unique
assert master[TARGET].notna().sum() == 138 and master[TARGET].isna().sum() == 59
assert master.crs is not None and master.geometry.is_valid.all() and not master.geometry.is_empty.any()
assert (master.AREA_HA > 0).all()
for scheme, count in zip(SCHEMES, [5, 4, 5]):
    part = groups[groups.scheme.eq(scheme)]
    assert len(part) == 138 and part[ID].is_unique and part.fold.nunique() == count
    assert set(part[ID]) == set(master.loc[master[TARGET].notna(), ID])
copies = read(ROOT / 'registry/copy-origins.json')
for name in ['data/processed/parcels.parquet', 'registry/schemes.csv']:
    assert digest(ROOT / name) == copies[name]['sha256'] == digest(copies[name]['source'])
save(ROOT / 'registry/population-check.json', {'passed': True, 'official': 197, 'labels': 138, 'hidden': 59,
    'schemes': SCHEMES, 'source_hashes': {n: copies[n]['sha256'] for n in ['data/processed/parcels.parquet', 'registry/schemes.csv']}})
print('Población oficial y tres esquemas verificados: 197 / 138 / 59')
