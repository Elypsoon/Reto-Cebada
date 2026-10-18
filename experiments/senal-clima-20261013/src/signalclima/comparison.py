"""Diferencias pareadas, verificadas por identidad, etiqueta y partición."""
import numpy as np
from .common import ID,TARGET
from .modeling import original


def paired(candidate,reference,reference_column='prediction'):
    a=candidate.set_index(ID).sort_index();b=reference.set_index(ID).sort_index()
    if len(a)!=138 or not a.index.is_unique or not b.index.is_unique or not a.index.equals(b.index):
        raise ValueError('IDs/filas incompatibles para comparación pareada')
    for column in [TARGET,'spatial_group','Estado']:
        if not np.array_equal(a[column],b[column]):raise ValueError('Etiqueta/partición/estado incompatible')
    y=a[TARGET];p=a.prediction;q=b[reference_column]
    if not np.isfinite(np.column_stack([y,p,q])).all():raise ValueError('OOF incompleta/no finita')
    rows=a[[TARGET,'Estado','spatial_group']].copy();rows['candidate']=p;rows['reference']=q
    rows['prediction_difference']=p-q
    rows['absolute_error_difference']=np.abs(p-y)-np.abs(q-y)
    rows['squared_error_difference']=(p-y)**2-(q-y)**2
    def summary(g):
        first=original.metric(g[TARGET],g.candidate);second=original.metric(g[TARGET],g.reference)
        return {'n':len(g),'candidate':first,'reference':second,'difference':{k:first[k]-second[k] if first[k] is not None and second[k] is not None else None for k in first}}
    report={'overall':summary(rows),'by_state':{str(k):summary(g) for k,g in rows.groupby('Estado')},
            'by_fold':{str(k):summary(g) for k,g in rows.groupby('spatial_group')},'positive_difference_means':'higher candidate error for MAE/RMSE; r2 has its usual orientation'}
    return rows.reset_index(),report
