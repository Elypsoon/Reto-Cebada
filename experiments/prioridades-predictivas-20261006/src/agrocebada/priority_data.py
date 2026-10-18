"""Entradas oficiales y enriquecidas explícitas, unidas exclusivamente por ID."""
import pandas as pd
import numpy as np
import geopandas as gpd
from .common import ROOT, PROCESSED, ID, TARGET
from .priority_selectors import AGRONOMIC


def load():
    master = gpd.read_parquet(PROCESSED/'parcels.parquet').set_index(ID)
    if master.crs is None or not master.geometry.is_valid.all() or master.geometry.is_empty.any():
        raise ValueError('Geometría o CRS incompatibles')
    if len(master)!=197 or not master.index.is_unique or master[TARGET].notna().sum()!=138:
        raise ValueError('Población incompatible')
    regions = pd.get_dummies(master.Estado,prefix='region',prefix_sep='__',dtype=float)
    tables = {key:pd.read_parquet(PROCESSED/f'features_{key}.parquet').loc[master.index]
              for key in ['monthly_20_10','whittaker_20_10']}
    for key, table in list(tables.items()):
        tables[key] = table.loc[:,~table.columns.str.startswith('region__')].join(regions,validate='one_to_one')
    quality = pd.read_parquet(PROCESSED/'priority-quality.parquet').loc[master.index]
    tables['compact'] = tables['monthly_20_10'][list(AGRONOMIC)].join(quality,validate='one_to_one').join(regions)
    for key in ['calendar','calendar_nasa','thermal']:
        tables[key] = pd.read_parquet(PROCESSED/f'features_priority_{key}.parquet').loc[master.index].join(regions)
    coeff = pd.read_parquet(PROCESSED/'priority-functional-coefficients.parquet').loc[master.index]
    tables['functional'] = coeff.join(regions,validate='one_to_one')
    if any(not t.index.equals(master.index) or t.columns.duplicated().any() for t in tables.values()):
        raise ValueError('Contrato de tabla incompatible')
    groups = pd.read_csv(ROOT/'registry/schemes.csv')
    return master, tables, {s:part.set_index(ID).fold for s,part in groups.groupby('scheme')}
