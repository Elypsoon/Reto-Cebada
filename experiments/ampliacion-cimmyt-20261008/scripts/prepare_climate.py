import geopandas as gpd
import pandas as pd
from cimmyt.common import ROOT, ID, save, read, digest
from cimmyt.climate import acquire_pairs, parse_daily, strict_json, build_matrix
from cimmyt.spatial import PROTOCOL

admission = read(ROOT/'registry/spatial-admission.json')
assert admission['protocol'] == PROTOCOL and admission['climate_requests'] == 0
principal = [r for r in admission['records'] if r['policy']=='principal']
keys = set(next(r for r in principal if r['stage']=='population' and r['cohort']=='C-mexico')['keys'])
aux = pd.read_parquet(ROOT/'data/processed/cimmyt-spatial-candidates.parquet').set_index('auxiliary_id')
aux = aux.loc[aux.index.isin(keys)].copy()
pairs = [(row.year,row.cell_lon,row.cell_lat) for row in aux.itertuples()]
records = acquire_pairs(pairs,ROOT/'data/raw/nasa-cache')
daily = {(r['year'],r['longitude'],r['latitude']):parse_daily(strict_json(open(r['path'],'rb').read()),
    r['year'],(r['longitude'],r['latitude'])) for r in records}
official_records = []
for path in sorted((ROOT/'data/external').glob('nasa*.json')):
    data = strict_json(path.read_bytes()); cell = tuple(data['geometry']['coordinates'][:2])
    daily[(2025,*cell)] = parse_daily(data,2025,cell)
    official_records.append({'path':str(path),'sha256':digest(path),'year':2025,'cell':cell,
        'api_version':data['header']['api']['version'],'reused_original':True})
assert len(official_records)==4
master = gpd.read_parquet(ROOT/'data/processed/parcels.parquet').set_index(ID)
cells = pd.read_csv(ROOT/'data/processed/nasa-cells.csv').set_index(ID).rename(columns={'longitude':'cell_lon','latitude':'cell_lat'})
assert cells.index.is_unique and set(cells.index)==set(master.index)
official = master.join(cells,validate='one_to_one').assign(year=2025)
official_X = build_matrix(official,daily,'AREA_HA','Estado')
aux_X = build_matrix(aux,daily,'area_ha','state')
assert len(official_X)==197 and len(aux_X)==len(keys)
official_X.to_parquet(ROOT/'data/processed/common-official.parquet')
aux_X.to_parquet(ROOT/'data/processed/common-auxiliary.parquet')
aux.to_parquet(ROOT/'data/processed/cimmyt-admitted.parquet')
save(ROOT/'registry/climate-acquisition.json',{'protocol':PROTOCOL,'policy':'principal','pairs':len(records),
    'records':records,'official_reused':official_records,'admission_sha256':digest(ROOT/'registry/spatial-admission.json')})
save(ROOT/'registry/common-features.json',{'representation':'common-area-nasa-v1','columns':list(official_X.columns),
    'official_count':197,'auxiliary_count':len(aux_X),'complete':True,
    'area_auxiliary':'verified treatment area in ha; not inferred from anonymized geometry',
    'official_area':'AREA_HA from official verified polygons',
    'year':'2025 official; actual 2012-2022 campaign auxiliary','excluded_predictors':['source','year','coordinates','management','demographics'],
    'hashes':{n:digest(ROOT/'data/processed'/n) for n in ['common-official.parquet','common-auxiliary.parquet','cimmyt-admitted.parquet']}})
print('Características completas:',len(official_X),'oficiales y',len(aux_X),'auxiliares')
