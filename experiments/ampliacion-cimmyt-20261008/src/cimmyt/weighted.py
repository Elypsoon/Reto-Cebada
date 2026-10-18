"""Ridge con influencia auxiliar limitada y preprocesamiento dentro de cada ajuste."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

WINDOWS = ['early', 'mid', 'late']
CONTINUOUS = ['log_area'] + [f'nasa_{variable}_{window}' for window in WINDOWS for variable in ['precip', 'tmean', 'amplitude']]
STATES = ['region__PUEBLA', 'region__HIDALGO', 'region__TLAXCALA', 'region__OTRO']
COLUMNS = CONTINUOUS + STATES


def validate_features(frame):
    if list(frame.columns) != COLUMNS or not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError('Contrato común de características incompatible o incompleto')
    state = frame[STATES].to_numpy()
    if not np.isin(state, [0., 1.]).all() or not (state.sum(axis=1) == 1).all():
        raise ValueError('Indicadores estatales incompatibles')


def sample_weights(n_official, groups, influence):
    if n_official < 1 or influence not in [0, .25, .5, 1]:
        raise ValueError('Influencia fuera del protocolo')
    groups = pd.Series(list(groups), dtype='string')
    if groups.isna().any():
        raise ValueError('Grupo auxiliar desconocido')
    if influence == 0:
        if len(groups):
            raise ValueError('El control sin auxiliares no incorpora filas auxiliares')
        return np.ones(n_official)
    if groups.empty:
        raise ValueError('Influencia positiva sin auxiliares')
    sizes = groups.value_counts()
    donor = np.asarray([influence * n_official / (len(sizes) * sizes[g]) for g in groups], dtype=float)
    return np.r_[np.ones(n_official), donor]


class WeightedNumericScale(TransformerMixin, BaseEstimator):
    def fit(self, X, y=None, sample_weight=None):
        validate_features(X)
        self.scaler_ = StandardScaler().fit(X[CONTINUOUS], sample_weight=sample_weight)
        return self

    def transform(self, X):
        validate_features(X)
        return np.column_stack([self.scaler_.transform(X[CONTINUOUS]), X[STATES].to_numpy()])


def fit_weighted(official_X, official_y, donor_X=None, donor_y=None, groups=(), influence=0., alpha=1.):
    if alpha not in [1., 10.]:
        raise ValueError('Regularización fuera del protocolo')
    validate_features(official_X)
    if influence:
        if donor_X is None or donor_y is None or len(groups) != len(donor_X):
            raise ValueError('Población auxiliar incompatible')
        validate_features(donor_X)
        X = pd.concat([official_X, donor_X], ignore_index=True)
        y = np.r_[np.asarray(official_y, dtype=float), np.asarray(donor_y, dtype=float)]
    else:
        if donor_X is not None and len(donor_X):
            raise ValueError('El control exige exclusivamente etiquetas oficiales')
        X = official_X
        y = np.asarray(official_y, dtype=float)
    if len(X) != len(y) or not np.isfinite(y).all():
        raise ValueError('Etiquetas incompatibles')
    weights = sample_weights(len(official_X), groups, influence)
    pipeline = Pipeline([('scale', WeightedNumericScale()), ('ridge', Ridge(alpha=alpha, solver='cholesky'))])
    pipeline.fit(X, y, scale__sample_weight=weights, ridge__sample_weight=weights)
    contract = {'columns': COLUMNS, 'alpha': alpha, 'influence': influence, 'official_count': len(official_X),
        'donor_count': len(X) - len(official_X), 'donor_groups': len(set(groups)), 'weights': weights.tolist(),
        'scale_mean': pipeline['scale'].scaler_.mean_.tolist(), 'scale_std': pipeline['scale'].scaler_.scale_.tolist(),
        'coef': pipeline['ridge'].coef_.tolist(), 'intercept': float(pipeline['ridge'].intercept_)}
    return pipeline, contract
