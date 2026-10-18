"""Estimadores y contratos completos por candidato y representación."""
from dataclasses import asdict
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel
from catboost import CatBoostRegressor
from .priority_models import HierarchicalAdditive, HierarchicalGPR, DirectGAM, PriorityEBM, states_from_frame
from .priority_selectors import PrioritySelector
from .priority_functional import FunctionalProjection


def direct_model(candidate):
    c = candidate
    if c.family == 'gpr':
        estimator = GaussianProcessRegressor(kernel=Matern(length_scale=c.setting, nu=2.5)+WhiteKernel(.15),
                     optimizer=None, normalize_y=True, random_state=2026)
    elif c.family == 'catboost':
        estimator = CatBoostRegressor(depth=int(c.setting), iterations=220, learning_rate=.03,
                     l2_leaf_reg=10, random_seed=2026, thread_count=2, verbose=False, allow_writing_files=False)
    elif c.family == 'ridge':
        estimator = Ridge(alpha=c.setting)
    elif c.family == 'gam':
        return DirectGAM(alpha=c.setting, n_knots=c.knots, selector=c.selector)
    elif c.family == 'ebm':
        return PriorityEBM(max_bins=int(c.setting), interactions=c.interactions)
    elif c.family == 'hierarchical_gpr':
        return HierarchicalGPR(length_scale=c.setting, state_variance=c.state_setting, selector=c.selector)
    elif c.family in ['hierarchical_ridge', 'hierarchical_gam']:
        return HierarchicalAdditive(alpha=c.setting,
                   state_penalty=np.inf if c.state_setting == 'infinite' else c.state_setting,
                   spline=c.family == 'hierarchical_gam', n_knots=c.knots, selector=c.selector)
    else:
        raise ValueError('Familia desconocida')
    return Pipeline([('select', PrioritySelector(c.selector, 10 if c.family == 'gpr' else 20)),
                     ('scale', StandardScaler()), ('model', estimator)])


def model_contract(model):
    if hasattr(model, 'contract'):
        return model.contract()
    select, scale, fit = model.named_steps['select'], model.named_steps['scale'], model.named_steps['model']
    params = {k: str(v) if hasattr(v, 'get_params') else v for k, v in fit.get_params().items()}
    return {'selector': select.contract(), 'scale_mean': scale.mean_.tolist(),
            'scale_std': scale.scale_.tolist(), 'model_parameters': params,
            'kernel_effective': str(fit.kernel_) if hasattr(fit, 'kernel_') else None}


class FittedCandidate:
    def __init__(self, candidate):
        self.candidate = candidate

    def fit(self, X, y):
        self.input_columns_ = list(X.columns)
        y = np.asarray(y, dtype=float)
        if len(X) != len(y) or not np.isfinite(y).all() or not X.index.is_unique:
            raise ValueError('Train incompatible')
        states = states_from_frame(X)
        self.global_mean_ = float(y.mean())
        self.state_counts_ = {s: int((states == s).sum()) for s in sorted(set(states))}
        self.state_means_ = {s: float(y[states == s].mean()) for s in self.state_counts_}
        self.training_ids_ = X.index.tolist()
        if self.candidate.family.endswith('_mean'):
            return self
        self.functional_ = FunctionalProjection(self.candidate.components).fit(X) if self.candidate.components else None
        features = self.functional_.transform(X) if self.functional_ else X
        self.model_ = direct_model(self.candidate)
        if self.candidate.kind == 'regional_correction':
            base = np.array([self.state_means_[s] for s in states])
            features = features.loc[:, ~features.columns.str.startswith('region__')]
            self.model_.fit(features, y-base)
        else:
            self.model_.fit(features, y)
        return self

    def _validate(self, X):
        if list(X.columns) != self.input_columns_ or not X.index.is_unique:
            raise ValueError('Contrato de entrada incompatible')

    def decompose(self, X):
        self._validate(X)
        states = states_from_frame(X)
        count = np.array([self.state_counts_.get(s, 0) for s in states])
        reference = np.full(len(X), self.global_mean_)
        state_effect = np.array([self.state_means_.get(s, self.global_mean_) for s in states])-reference
        family = self.candidate.family
        if family.endswith('_mean'):
            return {'reference': reference, 'state_effect': state_effect if family == 'regional_mean' else np.zeros(len(X)),
                    'parcel_effect': np.zeros(len(X)), 'state_support': count}
        features = self.functional_.transform(X) if self.functional_ else X
        if self.candidate.kind == 'regional_correction':
            features = features.loc[:, ~features.columns.str.startswith('region__')]
            parcel = np.where(count > 0, self.candidate.alpha*self.model_.predict(features), 0.)
        elif hasattr(self.model_, 'decompose'):
            parts = self.model_.decompose(features)
            parts.update(state_support=count, unseen=count == 0)
            return parts
        else:
            state_effect = np.zeros(len(X))
            parcel = self.model_.predict(features)-reference
        return {'reference': reference, 'state_effect': state_effect, 'parcel_effect': parcel,
                'state_support': count, 'unseen': count == 0}

    def predict(self, X):
        parts = self.decompose(X)
        return np.asarray(parts['reference']+parts['state_effect']+parts['parcel_effect'], dtype=np.float64)

    def contract(self):
        return {'candidate': dict(asdict(self.candidate), id=self.candidate.id),
                'input_columns': self.input_columns_, 'training_ids': self.training_ids_,
                'global_mean_t_ha': self.global_mean_, 'state_counts': self.state_counts_,
                'state_means_t_ha': self.state_means_,
                'functional': self.functional_.contract() if getattr(self, 'functional_', None) else None,
                'model': model_contract(self.model_) if hasattr(self, 'model_') else None}


class FittedProcedure:
    def __init__(self, candidates, models):
        self.candidates, self.models = candidates, models
        self.weights = np.full(len(models), 1/len(models))

    def predict(self, tables, ids):
        return sum(w*m.predict(tables[c.representation].loc[ids]) for w, m, c in
                   zip(self.weights, self.models, self.candidates))

    def contract(self):
        return {'weights': self.weights.tolist(), 'components': [m.contract() for m in self.models]}

    def decompose(self, tables, ids):
        values = [m.decompose(tables[c.representation].loc[ids]) for m, c in zip(self.models, self.candidates)]
        return {field: sum(w*v[field] for w, v in zip(self.weights, values))
                for field in ['reference', 'state_effect', 'parcel_effect']}
