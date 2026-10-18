"""Registro descriptivo opcional: no altera predictores ni el protocolo."""
from pathlib import Path
import numpy as np
import pandas as pd
from .common import ID,safe

COLUMNS=[ID,'campana','campo','valor','unidad','fecha_evento','procedencia']


def import_records(path,ids,destination):
    destination=safe(destination)
    destination.mkdir(parents=True,exist_ok=True)
    if path is None:
        empty=pd.DataFrame(columns=COLUMNS)
        empty.to_csv(destination/'records.csv',index=False)
        return {'status':'absent','n':0,'unknown_fields':['siembra','variedad','riego'],'predictive_use':False}
    path=Path(path)
    if path.suffix.lower()!='.csv' or not path.is_file():raise ValueError('Se requiere CSV local')
    d=pd.read_csv(path,dtype=str,keep_default_na=False)
    if not set(COLUMNS).issubset(d):raise ValueError('Campos obligatorios ausentes')
    d=d[COLUMNS].copy()
    if not d[ID].isin([str(x) for x in ids]).all():raise ValueError('ID ajeno al conjunto oficial')
    if not d.campana.str.fullmatch(r'\d{4}').all():raise ValueError('Campaña inválida')
    if not d.campo.isin(['siembra','variedad','riego']).all():raise ValueError('Campo no admitido')
    if d.procedencia.str.strip().eq('').any() or d.valor.str.strip().eq('').any():raise ValueError('Valor/procedencia ausente')
    dates=pd.to_datetime(d.fecha_evento,errors='coerce')
    if dates.isna().any():raise ValueError('Fecha del evento inválida')
    for i,row in d.iterrows():
        if row.campo=='siembra':
            sow=pd.to_datetime(row.valor,errors='coerce')
            if pd.isna(sow) or row.unidad not in ['', 'fecha']:raise ValueError('Fecha/unidad de siembra inválida')
            d.loc[i,'valor']=sow.strftime('%Y-%m-%d')
        elif row.campo=='riego':
            factors={'mm':1.,'cm':10.,'m':1000.}
            try:value=float(row.valor)*factors[row.unidad]
            except (ValueError,KeyError):raise ValueError('Unidad/valor de riego inválido')
            if not np.isfinite(value) or value<0:raise ValueError('Riego físicamente inválido')
            d.loc[i,'valor']=str(value);d.loc[i,'unidad']='mm'
        elif row.unidad!='':raise ValueError('Variedad no tiene unidad física')
    keys=[ID,'campana','campo','fecha_evento']
    conflict=d.groupby(keys,dropna=False).valor.transform('nunique').gt(1)
    variety=d.campo.eq('variedad')
    if variety.any():
        conflicts=d[variety].groupby([ID,'campana']).valor.transform('nunique').gt(1)
        conflict.loc[conflicts.index]|=conflicts
    d['conflict']=conflict
    d['duplicate']=d.duplicated(COLUMNS,keep=False)
    d.to_csv(destination/'records.csv',index=False)
    d[conflict].to_csv(destination/'conflicts.csv',index=False)
    (destination/'original.csv').write_bytes(path.read_bytes())
    return {'status':'descriptive','n':len(d),'conflicts':int(conflict.sum()),'duplicates':int(d.duplicate.sum()),'predictive_use':False}
