"""Dos contextos TabPFN-3 fijos; no se simulan pesos mediante duplicación."""
import numpy as np
import pandas as pd
from .selection import balanced_context, NonViable, Configuration
from .spatial import support
from .weighted import validate_features


def context_pair(engine, train_ids, target, retained_ids=()):
    donor,admission=engine.donors(Configuration(1.,.25,'C-local'),retained_ids)
    donor=balanced_context(donor)
    if not support(donor)['viable']:
        raise NonViable('A04 requiere 30 etiquetas locales, diez grupos y dos campañas después de muestreo')
    x=engine.X.loc[train_ids];y=target.loc[train_ids].to_numpy(dtype=float)
    dx=engine.aux_X.loc[donor.index];dy=donor.yield_t_ha.to_numpy(dtype=float)
    validate_features(x);validate_features(dx)
    return {'official_common':{'X':x,'y':y,'official_ids':list(train_ids),'donor_keys':[]},
        'official_common_plus_local_cap256':{'X':pd.concat([x,dx],ignore_index=True),
            'y':np.r_[y,dy],'official_ids':list(train_ids),'donor_keys':donor.index.tolist(),
            'donor_groups':donor.dependence_group.tolist(),'admission':admission}}


def estimator(checkpoint):
    from tabpfn import TabPFNRegressor
    return TabPFNRegressor(model_path=str(checkpoint),n_estimators=8,random_state=2026,
        device='cpu',fit_mode='fit_preprocessors',n_preprocessing_jobs=1)
