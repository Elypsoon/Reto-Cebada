import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
from pyproj import Geod, Transformer
from shapely.geometry import box
from cimmyt.spatial import (point_bounds, single_cell, coordinate_rows, validate_evidence,
    distance_lower_bound, ecef_bounds, SpatialGuard, support, Policy, PRINCIPAL)


def candidates():
    return pd.DataFrame({'auxiliary_id': ['cimmyt:a', 'cimmyt:b', 'cimmyt:c'],
        'dependence_group': ['same', 'same', 'other'], 'candidate_local': [True]*3,
        'latitude': [19.51, 21., 22.], 'longitude': [-98.14, -102., -105.], 'year': [2014, 2018, 2019]})


def test_closed_box_and_cell_boundary():
    assert single_cell(point_bounds(19.5, -98.125)) == (-98.125, 19.5)
    boundary = -98.125+.625/2
    assert single_cell((boundary-.02, 19.49, boundary+.02, 19.51)) is None
    assert single_cell((boundary-.02, 19.49, boundary, 19.51)) is None
    assert single_cell((boundary+.001, 19.49, boundary+.02, 19.51)) == (-97.5, 19.5)


def test_negative_longitude_and_unknown_metadata_remain():
    f = coordinate_rows(candidates())
    assert f.longitude.equals(candidates().longitude)
    assert set(f.source_crs) == {'unknown'} and set(f.crs_basis) == {'explicit_assumption'}
    assert set(f.point_semantics) == {'unknown'}
    assert f.west.iloc[0] == pytest.approx(-98.15)
    for lat, lon in [(np.nan, -98.), (19., 98.), (-98., 19.), (40., -98.)]:
        with pytest.raises(ValueError):
            point_bounds(lat, lon)


def test_conflicting_later_evidence_blocks():
    with pytest.raises(ValueError, match='Referencia posterior'):
        validate_evidence({'source_crs': 'EPSG:4269'})
    with pytest.raises(ValueError, match='Incertidumbre posterior'):
        validate_evidence({'documented_uncertainty_degrees': .1})


@pytest.mark.parametrize('bounds', [(-98.15,19.49,-98.13,19.51), (-117.02,31.98,-116.98,32.02),
    (-85.02,9.98,-84.98,10.02), (-1.,-1.,1.,1.)])
def test_ecef_interval_covers_edges_and_interior_extrema(bounds):
    low, high = ecef_bounds(bounds)
    transform = Transformer.from_crs(4326,4978,always_xy=True)
    lon, lat = np.meshgrid(np.linspace(bounds[0],bounds[2],21), np.linspace(bounds[1],bounds[3],21))
    xyz = np.stack(transform.transform(lon,lat,np.zeros_like(lon)),axis=-1)
    assert (xyz >= low-1e-7).all() and (xyz <= high+1e-7).all()


def test_whole_box_lower_bound_not_center_distance():
    aux = (-98.15,19.49,-98.13,19.51)
    parcel = (-98.1501,19.5,-98.149,19.501)
    assert distance_lower_bound(aux,parcel) == 0
    for lon, lat in [(-117.,32.),(-98.,19.5),(-86.,20.)]:
        distant = (lon-.001,lat-.001,lon+.001,lat+.001)
        bound = distance_lower_bound(aux,distant)
        geodesic = Geod(ellps='WGS84').inv(-98.14,19.5,lon,lat)[2]
        assert 0 <= bound <= geodesic


def test_group_campaigns_and_both_retained_sets_excluded():
    official = gpd.GeoDataFrame(geometry=[box(-98.15,19.5,-98.13,19.52),box(-105.001,21.999,-104.999,22.001)],
        index=['outer','inner'],crs=4326)
    guard=SpatialGuard(candidates(),official)
    f, contract=guard.admit('C-local',['outer'])
    assert f.auxiliary_id.tolist() == ['cimmyt:c']
    assert len(contract['exclusions']) == 2
    f, contract=guard.admit('C-local',['outer','inner'])
    assert f.empty
    assert all(e['reason']=='group_within_buffer' for e in contract['exclusions'])


def test_inclusive_threshold_and_support():
    official=gpd.GeoDataFrame(geometry=[box(-100.,20.,-99.999,20.001)],index=['o'],crs=4326)
    guard=SpatialGuard(candidates(),official)
    guard.distances.loc[:, 'o']=PRINCIPAL.buffer_m
    assert guard.admit('C-mexico',['o'])[0].empty
    f=pd.DataFrame({'dependence_group': [str(i%10) for i in range(30)], 'year': [2014,2015]*15})
    assert support(f)['viable']
    assert not support(f.iloc[:29])['viable']
    assert not support(f.assign(year=2014))['viable']
