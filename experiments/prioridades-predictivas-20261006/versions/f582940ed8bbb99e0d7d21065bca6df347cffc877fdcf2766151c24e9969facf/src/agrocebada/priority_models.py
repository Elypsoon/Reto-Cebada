"""Efectos estatales regularizados y predicciones descompuestas en t/ha."""
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.preprocessing import StandardScaler, SplineTransformer
from sklearn.gaussian_process.kernels import Matern
from .priority_selectors import PrioritySelector


def states_from_frame(X):
    columns = [c for c in X if c.startswith('region__')]
    if not columns:
        raise ValueError('Faltan indicadores oficiales de estado')
    values = X[columns].to_numpy(dtype=float)
    if not np.isfinite(values).all() or not np.isin(values, [0., 1.]).all() or (values.sum(axis=1) > 1).any():
        raise ValueError('Codificación estatal incompatible')
    return np.where(values.sum(axis=1) > 0, np.asarray(columns)[values.argmax(axis=1)], '__unseen__')


class HierarchicalAdditive(RegressorMixin, BaseEstimator):
    def __init__(self, alpha=1., state_penalty=10., spline=False, n_knots=3, selector='agronomic'):
        self.alpha, self.state_penalty = alpha, state_penalty
        self.spline, self.n_knots, self.selector = spline, n_knots, selector

    def _design(self, X, fitting=False):
        if fitting:
            self.select_ = PrioritySelector(self.selector).fit(X)
            self.scale_ = StandardScaler().fit(self.select_.transform(X))
        features = self.scale_.transform(self.select_.transform(X))
        if self.spline:
            if fitting:
                self.splines_ = SplineTransformer(n_knots=self.n_knots, degree=2, knots='quantile',
                                                include_bias=False, extrapolation='constant').fit(features)
            features = self.splines_.transform(features)
        if fitting:
            self.feature_center_ = features.mean(axis=0)
        return features - self.feature_center_

    def fit(self, X, y):
        if self.alpha <= 0 or self.state_penalty <= 0:
            raise ValueError('Penalizaciones deben ser positivas')
        states = states_from_frame(X)
        if '__unseen__' in states:
            raise ValueError('Train debe tener estado oficial observado')
        target = np.asarray(y, dtype=float)
        self.global_mean_ = float(target.mean())
        self.target_std_ = max(float(target.std()), 1e-12)
        normalized = (target-self.global_mean_)/self.target_std_
        self.state_counts_ = {s: int((states == s).sum()) for s in sorted(set(states))}
        self.states_ = list(self.state_counts_)
        features = self._design(X, fitting=True)
        self.columns_ = self.select_.columns_
        if np.isinf(self.state_penalty):
            matrix = features.T@features + self.alpha*np.eye(features.shape[1])
            self.coef_ = np.linalg.solve(matrix, features.T@normalized)
            self.state_effects_ = {s: 0. for s in self.states_}
        else:
            state_design = np.column_stack([states == s for s in self.states_]).astype(float)
            design = np.column_stack([features, state_design])
            dimension = features.shape[1]
            penalty = np.r_[np.full(dimension, self.alpha), np.full(len(self.states_), self.state_penalty)]
            hessian = design.T@design + np.diag(penalty)
            constraint = np.r_[np.zeros(dimension), [self.state_counts_[s]/len(X) for s in self.states_]]
            kkt = np.block([[hessian, constraint[:, None]], [constraint[None, :], np.zeros((1, 1))]])
            solution = np.linalg.solve(kkt, np.r_[design.T@normalized, 0.])[:-1]
            self.coef_ = solution[:dimension]
            self.state_effects_ = dict(zip(self.states_, solution[dimension:]))
        return self

    def decompose(self, X):
        states = states_from_frame(X)
        seen = np.asarray([s in self.state_counts_ for s in states])
        features = self._design(X)
        correction = np.where(seen, features@self.coef_*self.target_std_, 0.)
        state_effect = np.array([self.state_effects_.get(s, 0.) for s in states])*self.target_std_
        return {'reference': np.full(len(X), self.global_mean_), 'state_effect': state_effect,
                'parcel_effect': correction, 'state_support': np.array([self.state_counts_.get(s, 0) for s in states]),
                'unseen': ~seen}

    def predict(self, X):
        parts = self.decompose(X)
        return parts['reference'] + parts['state_effect'] + parts['parcel_effect']

    def contract(self):
        return {'family': 'hierarchical_gam' if self.spline else 'hierarchical_ridge',
                'parameters': {k: ('infinite' if isinstance(v,float) and np.isinf(v) else v) for k,v in self.get_params().items()}, 'selector': self.select_.contract(),
                'global_mean_t_ha': self.global_mean_, 'target_std': self.target_std_,
                'state_counts': self.state_counts_, 'normalized_state_effects': self.state_effects_,
                'coefficients': self.coef_.tolist(), 'feature_center': self.feature_center_.tolist(),
                'scale_mean': self.scale_.mean_.tolist(), 'scale_std': self.scale_.scale_.tolist(),
                'spline_knots': [b.t.tolist() for b in self.splines_.bsplines_] if self.spline else None,
                'unseen_state': 'media global exacta, sin efecto estatal ni parcelario'}


class HierarchicalGPR(RegressorMixin, BaseEstimator):
    def __init__(self, length_scale=1., state_variance=.25, noise=.15, selector='agronomic'):
        self.length_scale, self.state_variance, self.noise, self.selector = length_scale, state_variance, noise, selector

    def fit(self, X, y):
        if self.state_variance < 0 or self.noise != .15 or self.length_scale not in (1, 5):
            raise ValueError('Parámetros fuera del protocolo jerárquico')
        self.train_states_ = states_from_frame(X)
        if '__unseen__' in self.train_states_:
            raise ValueError('Train sin estado observado')
        self.state_counts_ = {s: int((self.train_states_ == s).sum()) for s in sorted(set(self.train_states_))}
        self.select_ = PrioritySelector(self.selector).fit(X)
        self.scale_ = StandardScaler().fit(self.select_.transform(X))
        self.train_features_ = self.scale_.transform(self.select_.transform(X))
        self.columns_ = self.select_.columns_
        target = np.asarray(y, dtype=float)
        self.global_mean_, self.target_std_ = float(target.mean()), max(float(target.std()), 1e-12)
        self.kernel_ = Matern(length_scale=self.length_scale, nu=2.5)
        self.parcel_covariance_ = self.kernel_(self.train_features_)
        state_kernel = self.state_variance*(self.train_states_[:, None] == self.train_states_[None, :])
        covariance = self.parcel_covariance_ + state_kernel + self.noise*np.eye(len(X))
        self.posterior_weights_ = cho_solve(cho_factor(covariance, lower=True),
                                          (target-self.global_mean_)/self.target_std_)
        return self

    def decompose(self, X):
        states = states_from_frame(X)
        seen = np.array([s in self.state_counts_ for s in states])
        features = self.scale_.transform(self.select_.transform(X))
        parcel = self.kernel_(features, self.train_features_)@self.posterior_weights_*self.target_std_
        state = self.state_variance*(states[:, None] == self.train_states_[None, :])@self.posterior_weights_*self.target_std_
        return {'reference': np.full(len(X), self.global_mean_), 'state_effect': np.where(seen, state, 0.),
                'parcel_effect': np.where(seen, parcel, 0.), 'unseen': ~seen,
                'state_support': np.array([self.state_counts_.get(s, 0) for s in states])}

    def predict(self, X):
        parts = self.decompose(X)
        return parts['reference'] + parts['state_effect'] + parts['parcel_effect']

    def contract(self):
        return {'family': 'hierarchical_gpr', 'parameters': self.get_params(),
                'selector': self.select_.contract(), 'global_mean_t_ha': self.global_mean_,
                'target_std': self.target_std_, 'state_counts': self.state_counts_,
                'kernel': str(self.kernel_), 'state_variance': self.state_variance, 'noise': self.noise,
                'posterior_weights': self.posterior_weights_.tolist(),
                'train_features': self.train_features_.tolist(), 'train_states': self.train_states_.tolist(),
                'scale_mean': self.scale_.mean_.tolist(), 'scale_std': self.scale_.scale_.tolist()}


class DirectGAM(HierarchicalAdditive):
    """GAM sin efecto estatal; transferencia directa distinta del fallback jerárquico."""
    def __init__(self, alpha=1., n_knots=3, selector='agronomic'):
        super().__init__(alpha=alpha, state_penalty=np.inf, spline=True, n_knots=n_knots, selector=selector)

    def _with_global_state(self, X):
        value = X.loc[:, ~X.columns.str.startswith('region__')].copy()
        value['region__global'] = 1.
        return value

    def fit(self, X, y):
        return super().fit(self._with_global_state(X), y)

    def decompose(self, X):
        return super().decompose(self._with_global_state(X))

    def contract(self):
        value = super().contract()
        value.update(family='direct_gam', unseen_state='transferencia directa; sin efecto estatal')
        return value


class PriorityEBM(RegressorMixin, BaseEstimator):
    def __init__(self, max_bins=8, interactions='none'):
        self.max_bins, self.interactions = max_bins, interactions

    def fit(self, X, y):
        from importlib.metadata import version
        from interpret.glassbox import ExplainableBoostingRegressor
        if version('interpret') != '0.7.8' or version('interpret-core') != '0.7.8':
            raise ValueError('Dependencia EBM distinta de la verificada')
        if self.max_bins not in (8, 16) or self.interactions not in ('none', 'fixed_pairs'):
            raise ValueError('Configuración EBM fuera del protocolo')
        self.select_ = PrioritySelector('agronomic').fit(X)
        features = self.select_.transform(X)
        self.columns_ = self.select_.columns_
        pairs = [('s2_evi_middle', 'climate_PREC_middle'), ('planet_msavi_late', 'climate_Tmean_late')]
        if self.interactions == 'fixed_pairs':
            if any(c not in features for pair in pairs for c in pair):
                raise ValueError('Interacción predefinida sin variables elegibles en train')
            interactions = [tuple(features.columns.get_loc(c) for c in pair) for pair in pairs]
        else:
            interactions = 0
        self.model_ = ExplainableBoostingRegressor(max_bins=self.max_bins, max_interaction_bins=self.max_bins,
              interactions=interactions, outer_bags=8, inner_bags=0, max_rounds=1000,
              learning_rate=.01, early_stopping_rounds=0, validation_size=.15, n_jobs=2, random_state=2026)
        # Dos hilos en el mismo proceso: evita pipes del backend loky en Windows.
        from joblib import parallel_backend
        with parallel_backend('threading', n_jobs=2):
            self.model_.fit(features, np.asarray(y, dtype=float))
        effective_pairs = {tuple(self.columns_[i] for i in term) for term in self.model_.term_features_ if len(term) > 1}
        expected = set(pairs) if self.interactions == 'fixed_pairs' else set()
        if effective_pairs != expected:
            raise ValueError('EBM no conserva exactamente las interacciones declaradas')
        return self

    def predict(self, X):
        return np.asarray(self.model_.predict(self.select_.transform(X)), dtype=np.float64)

    def decompose(self, X):
        terms = self.model_.eval_terms(self.select_.transform(X))
        return {'reference': np.full(len(X), float(np.asarray(self.model_.intercept_).item())),
                'state_effect': np.zeros(len(X)), 'parcel_effect': terms.sum(axis=1), 'terms': terms,
                'interpretation': 'Transferencia directa; términos EBM aditivos en t/ha.'}

    def contract(self):
        return {'family': 'ebm', 'dependency': 'interpret==0.7.8 / interpret-core==0.7.8',
                'selector': self.select_.contract(), 'parameters': self.model_.get_params(),
                'effective_interactions': [[self.columns_[i] for i in term] for term in self.model_.term_features_ if len(term) > 1],
                'term_names': self.model_.term_names_, 'early_stopping_rounds': 0,
                'parallel_backend': 'threading', 'threads': 2,
                'outer_test_used': False, 'validation': 'Bagging interno de train, sin early stopping.'}
