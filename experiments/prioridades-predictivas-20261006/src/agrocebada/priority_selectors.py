"""Selectores congelables ajustados exclusivamente en el entrenamiento."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from .modeling import CompactSelector

WINDOWS = ('early', 'middle', 'late')
ENVIRONMENT = tuple(f'climate_{var}_{window}' for var in ('PREC', 'Tmean') for window in WINDOWS) + (
    'elevation', 'slope', 'log_area')
AGRONOMIC = tuple(f'{prefix}_{window}' for prefix in ('s2_evi', 'planet_msavi') for window in WINDOWS) + (
    'landsat_vi6t_late',) + ENVIRONMENT
FORBIDDEN = {'ID_POLIGONO', 'RENDIMIENTO_T_HA', 'CONJUNTO', 'location_x', 'location_y',
             'longitude', 'latitude', 'centroid_x', 'centroid_y', 'fold', 'spatial_group'}


class PrioritySelector(TransformerMixin, BaseEstimator):
    def __init__(self, mode='rank', k=20):
        self.mode = mode
        self.k = k

    def fit(self, X, y=None):
        if self.mode not in ('rank', 'agronomic', 'all'):
            raise ValueError('Modo de selección desconocido')
        numeric = [c for c in X.select_dtypes(include='number') if c not in FORBIDDEN
                   and not c.startswith('region__')]
        if self.mode == 'agronomic':
            numeric = [c for c in AGRONOMIC if c in numeric]
        self.input_columns_ = list(X.columns)
        self.availability_ = X[numeric].notna().mean()
        self.medians_ = X[numeric].median().fillna(0.)
        filled = X[numeric].fillna(self.medians_)
        valid = (self.availability_ >= .5) & (filled.std() > 1e-8)
        self.eligible_columns_ = valid.index[valid].tolist()
        if not self.eligible_columns_:
            raise ValueError('Sin predictores elegibles en train')
        if self.mode == 'rank':
            if y is None:
                raise ValueError('Ranking requiere etiquetas de entrenamiento')
            self.ranking_ = CompactSelector(self.k).fit(X[self.eligible_columns_], y)
            self.columns_ = self.ranking_.columns_
        else:
            self.columns_ = list(self.eligible_columns_)
        self.effective_dimension_ = len(self.columns_)
        return self

    def transform(self, X):
        if any(c not in X for c in self.columns_):
            raise ValueError('Contrato de variables incompatible')
        return X[self.columns_].fillna(self.medians_[self.columns_])

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.columns_, dtype=object)

    def contract(self):
        return {'mode': self.mode, 'k': self.k if self.mode == 'rank' else None,
                'columns': self.columns_, 'effective_dimension': self.effective_dimension_,
                'availability': self.availability_.to_dict(), 'medians': self.medians_.to_dict()}
