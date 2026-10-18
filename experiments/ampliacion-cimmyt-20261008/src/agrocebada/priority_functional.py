"""Proyección B-spline latente y PCA aprendida únicamente en train."""
import numpy as np
import pandas as pd
from scipy.interpolate import BSpline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import PCA
from .common import ID
from .priority_curves import BRANCHES, START_DATE, SEASON_DAYS, QUALITY
from .priority_selectors import ENVIRONMENT

KNOTS = np.r_[np.zeros(4), [1/3, 2/3], np.ones(4)]
PENALTY = np.diff(np.eye(6), n=2, axis=0)


def individual_projection(branch):
    if not branch['pieces']:
        return np.full(6, np.nan), {'available': False, 'reason': 'sin segmentos utilizables'}
    points = pd.concat([original for original, _ in branch['pieces']]).drop_duplicates('date').sort_values('date')
    x = (points.date - START_DATE).dt.days.to_numpy(dtype=float) / SEASON_DAYS
    thirds = np.minimum((x*3).astype(int), 2)
    if len(points) < 8 or len(np.unique(thirds)) < 2:
        return np.full(6, np.nan), {'available': False, 'reason': 'menos de ocho observaciones o dos tercios',
                                  'observations': len(points), 'calendar_thirds': len(np.unique(thirds))}
    basis = BSpline.design_matrix(x, KNOTS, k=3, extrapolate=False).toarray()
    weights = np.maximum(.01, 1-points.porcentaje_nubosidad.to_numpy()/100)
    values = points[branch['column']].to_numpy()
    # Solo las fechas realmente observadas contribuyen al ajuste. Sin reconstrucción de curvas.
    matrix = basis.T @ (weights[:, None]*basis) + 10*PENALTY.T @ PENALTY
    coefficients = np.linalg.solve(matrix, basis.T @ (weights*values))
    return coefficients, {'available': True, 'observations': len(points),
                         'calendar_thirds': len(np.unique(thirds)),
                         'weighted_dates': points.date.dt.strftime('%Y-%m-%d').tolist(),
                         'unobserved_weight': 0., 'reconstructed_values': False}


def coefficient_table(master, branches, covariates):
    table = pd.DataFrame(index=pd.Index(master[ID], name=ID),
                         columns=[f'coef_{branch}_{j}' for branch in BRANCHES for j in range(6)], dtype=float)
    diagnostics = []
    for pid in master[ID]:
        for branch in BRANCHES:
            coef, metadata = individual_projection(branches[(pid, branch)])
            table.loc[pid, [f'coef_{branch}_{j}' for j in range(6)]] = coef
            diagnostics.append({ID: pid, 'branch': branch, **metadata})
    return table.join(covariates, validate='one_to_one'), diagnostics


class FunctionalProjection(TransformerMixin, BaseEstimator):
    def __init__(self, n_components=2):
        self.n_components = n_components

    def fit(self, X, y=None):
        if self.n_components not in (2, 3):
            raise ValueError('Solo dos o tres componentes predeclarados')
        self.bases_, self.support_, self.coefficient_columns_ = {}, {}, {}
        self.covariates_ = list(ENVIRONMENT) + list(QUALITY)
        self.region_columns_ = [c for c in X if c.startswith('region__')]
        if any(c not in X for c in self.covariates_):
            raise ValueError('Covariables funcionales incompletas')
        for branch in BRANCHES:
            cols = [f'coef_{branch}_{j}' for j in range(6)]
            if any(c not in X for c in cols):
                raise ValueError('Contrato de coeficientes incompatible')
            valid = np.isfinite(X[cols]).all(axis=1)
            n = int(valid.sum())
            eligible = n >= 20 and n >= .5*len(X)
            self.support_[branch] = {'valid_train': n, 'train_n': len(X), 'available': eligible}
            if not eligible:
                continue
            model = PCA(n_components=self.n_components, svd_solver='full').fit(X.loc[valid, cols])
            for component in model.components_:
                if component[np.argmax(np.abs(component))] < 0:
                    component *= -1
            self.bases_[branch], self.coefficient_columns_[branch] = model, cols
        if not self.bases_:
            raise ValueError('Ninguna rama funcional aprendible en train')
        self.columns_ = [f'fpca_{branch}_{j}' for branch in self.bases_ for j in range(self.n_components)] + self.covariates_ + self.region_columns_
        return self

    def transform(self, X):
        if any(c not in X for c in self.covariates_):
            raise ValueError('Contrato de covariables incompatible')
        result = pd.DataFrame(index=X.index)
        for branch, model in self.bases_.items():
            cols = self.coefficient_columns_[branch]
            if any(c not in X for c in cols):
                raise ValueError('Contrato de coeficientes incompatible')
            valid = np.isfinite(X[cols]).all(axis=1)
            scores = np.full((len(X), self.n_components), np.nan)
            if valid.any():
                scores[valid] = model.transform(X.loc[valid, cols])
            for j in range(self.n_components):
                result[f'fpca_{branch}_{j}'] = scores[:, j]
        if any(c not in X for c in self.region_columns_):
            raise ValueError('Contrato de índices estatales incompatible')
        return result.join(X[self.covariates_ + self.region_columns_], validate='one_to_one')

    def contract(self):
        return {'method': 'PCA de seis coeficientes B-spline cúbicos; proyección latente sin reconstruir lagunas',
                'n_components': self.n_components, 'knots': KNOTS.tolist(), 'coefficient_penalty': 10,
                'support': self.support_, 'covariates': self.covariates_, 'region_columns': self.region_columns_,
                'bases': {b: {'mean': p.mean_.tolist(), 'components': p.components_.tolist(),
                              'explained_variance': p.explained_variance_.tolist()}
                          for b, p in self.bases_.items()}}
