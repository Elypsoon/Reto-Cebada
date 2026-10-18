"""NASA diario con caché por celda/año y características compartidas cerradas."""
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import urlopen
import numpy as np
import pandas as pd
from .common import ROOT, ID, digest, now, save
from .spatial import GRID
from .weighted import COLUMNS, CONTINUOUS, STATES, validate_features

PARAMETERS = {'T2M':'C','T2M_MIN':'C','T2M_MAX':'C','PRECTOTCORR':'mm/day'}
API = 'https://power.larc.nasa.gov/api/temporal/daily/point'


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Claves NASA duplicadas: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def parse_daily(data, year, cell):
    if not (2012 <= year <= 2022 or year == 2025):
        raise ValueError('Campaña NASA fuera del protocolo')
    header = data['header']
    if header['time_standard'] != 'LST' or 'MERRA2' not in header['sources']:
        raise ValueError('Tiempo o fuente meteorológica incompatible')
    if header['start'] != f'{year}0401' or header['end'] != f'{year}1031':
        raise ValueError('Corte temporal incompatible')
    coords = data['geometry']['coordinates'][:2]
    if not np.allclose(coords, cell, atol=1e-10, rtol=0):
        raise ValueError('Respuesta de otra celda NASA')
    for coord, origin, step in zip(coords, [-180.,-90.], [.625,.5]):
        if abs((coord-origin)/step-round((coord-origin)/step)) > 1e-9:
            raise ValueError('Nodo ajeno a la malla nativa documentada')
    if any(data['parameters'].get(k,{}).get('units') != u for k,u in PARAMETERS.items()):
        raise ValueError('Unidades NASA incompatibles')
    expected = pd.date_range(f'{year}-04-01', f'{year}-10-31')
    expected_keys = set(expected.strftime('%Y%m%d'))
    params = data['properties']['parameter']
    if any(set(params[k]) != expected_keys for k in PARAMETERS):
        raise ValueError('Cobertura NASA incompleta o fechas inesperadas')
    frame = pd.DataFrame({k:params[k] for k in PARAMETERS})
    frame.index = pd.to_datetime(frame.index,format='%Y%m%d')
    frame = frame.sort_index().astype(float)
    if len(frame) != 214 or not frame.index.equals(expected):
        raise ValueError('Serie NASA no contiene los 214 días únicos')
    if not np.isfinite(frame.to_numpy()).all() or frame.eq(header['fill_value']).any().any():
        raise ValueError('Rellenos o valores no finitos NASA')
    physical = (frame.T2M_MIN.le(frame.T2M_MAX) & frame.T2M.between(-60,60)
        & frame.T2M_MIN.between(-80,60) & frame.T2M_MAX.between(-60,70) & frame.PRECTOTCORR.between(0,2000))
    if not physical.all():
        raise ValueError('Límites físicos NASA incompatibles')
    return frame


def query_url(year, cell):
    lon, lat = cell
    return API+'?'+urlencode({'parameters':','.join(PARAMETERS),'community':'AG','longitude':lon,
        'latitude':lat,'start':f'{year}0401','end':f'{year}1031','format':'JSON','time-standard':'LST'})


def cache_name(year, cell):
    lon, lat = cell
    return f'nasa_{lat:g}_{lon:g}_{year}0401_{year}1031.json'


def acquire_pairs(pairs, cache_dir, opener=urlopen, wait=time.sleep):
    pairs = sorted(set((int(year),float(lon),float(lat)) for year,lon,lat in pairs))
    if len(pairs) > 1000:
        raise ValueError('Presupuesto de 1.000 celdas/año excedido')
    cache_dir = Path(cache_dir); cache_dir.mkdir(parents=True,exist_ok=True)
    records = []
    for year, lon, lat in pairs:
        path = cache_dir/cache_name(year,(lon,lat))
        url = query_url(year,(lon,lat)); attempts = 0
        if path.exists():
            data = strict_json(path.read_bytes()); parse_daily(data,year,(lon,lat))
            origin = 'cache'
        else:
            for attempt in range(1,4):
                attempts = attempt
                try:
                    with opener(url,timeout=90) as response:
                        raw = response.read()
                    data = strict_json(raw); parse_daily(data,year,(lon,lat))
                    # Solo almacenar una respuesta completa y validada.
                    path.write_bytes(raw)
                    break
                except (OSError, ValueError, KeyError) as error:
                    if attempt == 3:
                        raise ValueError(f'NASA falló tres intentos para {year}/{lon}/{lat}: {error}') from error
                    wait(attempt*2)
            origin = 'download'
        records.append({'year':year,'longitude':lon,'latitude':lat,'url':url,'path':str(path),
            'sha256':digest(path),'origin':origin,'attempts':attempts,'at':now(),
            'api_version':data['header']['api']['version'],'sources':data['header']['sources'],
            'units':PARAMETERS,'days':214,'time_standard':'LST','grid':GRID})
        print(f'Clima verificado {len(records)}/{len(pairs)}: {year}, {origin}',flush=True)
    return records


def common_row(area, state, daily):
    if not np.isfinite(area) or area <= 0:
        raise ValueError('Área común incompatible')
    row = {'log_area':float(np.log1p(area))}
    for name, lo, hi in [('early',4,5),('mid',6,7),('late',8,10)]:
        f = daily.loc[daily.index.month.to_series(index=daily.index).between(lo,hi)]
        row[f'nasa_precip_{name}'] = float(f.PRECTOTCORR.sum())
        row[f'nasa_tmean_{name}'] = float(f.T2M.mean())
        row[f'nasa_amplitude_{name}'] = float((f.T2M_MAX-f.T2M_MIN).mean())
    state = str(state).upper().strip()
    state = state if state in ['PUEBLA','HIDALGO','TLAXCALA'] else 'OTRO'
    row.update({column:float(column == 'region__'+state) for column in STATES})
    return row


def build_matrix(frame, daily, area_column, state_column):
    matrix = pd.DataFrame([common_row(float(row[area_column]),row[state_column],
        daily[(int(row['year']),float(row['cell_lon']),float(row['cell_lat']))])
        for _,row in frame.iterrows()],index=frame.index,columns=COLUMNS)
    validate_features(matrix)
    return matrix
