import copy
import io
import json
import numpy as np
import pandas as pd
import pytest
from cimmyt.climate import parse_daily, strict_json, acquire_pairs, common_row, build_matrix, PARAMETERS
from cimmyt.weighted import COLUMNS


def response(year=2018):
    dates=pd.date_range(f'{year}-04-01',f'{year}-10-31').strftime('%Y%m%d')
    return {'header':{'time_standard':'LST','sources':['MERRA2'],'start':f'{year}0401','end':f'{year}1031',
        'fill_value':-999.,'api':{'version':'test'}},'geometry':{'coordinates':[-98.125,19.5,0]},
        'parameters':{k:{'units':u} for k,u in PARAMETERS.items()},
        'properties':{'parameter':{k:{day:v for day in dates} for k,v in
            [('T2M',15.),('T2M_MIN',10.),('T2M_MAX',20.),('PRECTOTCORR',1.)]}}}


@pytest.mark.parametrize('fault',['missing','fill','units','physical','time','cell','year'])
def test_incompatible_climate_rejected(fault):
    d=response()
    if fault=='missing': d['properties']['parameter']['T2M'].pop('20180401')
    if fault=='fill': d['properties']['parameter']['T2M']['20180401']=-999.
    if fault=='units': d['parameters']['PRECTOTCORR']['units']='m'
    if fault=='physical': d['properties']['parameter']['T2M_MIN']['20180401']=30.
    if fault=='time': d['header']['time_standard']='UTC'
    if fault=='cell': d['geometry']['coordinates'][0]=-98.75
    if fault=='year': d['header']['start']='20250401'
    with pytest.raises(ValueError): parse_daily(d,2018,(-98.125,19.5))


def test_duplicate_json_keys_rejected():
    with pytest.raises(ValueError): strict_json('{"day":1,"day":2}')


def test_acquisition_dedup_cache_and_three_attempts(tmp_path):
    calls=[]
    def fetch(url,timeout):
        calls.append(url)
        return io.BytesIO(json.dumps(response()).encode())
    pairs=[(2018,-98.125,19.5)]*3
    first=acquire_pairs(pairs,tmp_path,fetch,lambda _:None)
    second=acquire_pairs(pairs,tmp_path,fetch,lambda _:None)
    assert len(calls)==1 and first[0]['sha256']==second[0]['sha256']
    assert second[0]['origin']=='cache' and second[0]['attempts']==0
    failures=[]
    def bad(url,timeout):
        failures.append(url); raise OSError('synthetic failure')
    with pytest.raises(ValueError,match='tres intentos'):
        acquire_pairs([(2019,-98.125,19.5)],tmp_path,bad,lambda _:None)
    assert len(failures)==3 and len(list(tmp_path.glob('*.json')))==1


def test_budget_and_no_corrupt_cache_replacement(tmp_path):
    with pytest.raises(ValueError,match='1.000'):
        acquire_pairs([(2018+i,-98.125,19.5) for i in range(1001)],tmp_path)
    from cimmyt.climate import cache_name
    path=tmp_path/cache_name(2018,(-98.125,19.5)); path.write_text('{}')
    with pytest.raises(KeyError): acquire_pairs([(2018,-98.125,19.5)],tmp_path)
    assert path.read_text()=='{}'


def test_windows_units_year_and_identical_source_contract():
    f=parse_daily(response(),2018,(-98.125,19.5))
    row=common_row(2.,'Puebla',f)
    assert row['nasa_precip_early']==61 and row['nasa_precip_mid']==61 and row['nasa_precip_late']==92
    assert row['nasa_amplitude_early']==10 and row['region__PUEBLA']==1
    data=pd.DataFrame({'area':[2.,3.],'state':['PUEBLA','MEXICO'],'year':[2018,2018],
        'cell_lon':[-98.125]*2,'cell_lat':[19.5]*2},index=['official','cimmyt:donor'])
    matrix=build_matrix(data,{(2018,-98.125,19.5):f},'area','state')
    assert list(matrix.columns)==COLUMNS and matrix.loc['cimmyt:donor','region__OTRO']==1
    with pytest.raises(KeyError): build_matrix(data.assign(year=2025),{(2018,-98.125,19.5):f},'area','state')
