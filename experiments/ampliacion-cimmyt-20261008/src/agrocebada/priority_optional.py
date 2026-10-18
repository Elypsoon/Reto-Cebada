"""Trabajadores fundacionales CPU: identidad fija y contexto recuperable sin red."""
import argparse
import json
import time
from pathlib import Path
from importlib.metadata import version
import numpy as np
import pandas as pd
from .common import ROOT, PROCESSED, ID, TARGET, sha256
from .tracking import atomic_json


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def configuration(name, override=None):
    folder = ROOT/'optional'/name
    manifest = override or read(folder/'manifest.json')
    if sha256(folder/manifest['checkpoint']) != manifest['sha256'] or sha256(folder/'LICENSE') != manifest['license_sha256']:
        raise ValueError('Checkpoint/licencia alterados')
    if version(manifest['package']) != manifest['package_version']:
        raise ValueError('Dependencia fundacional incompatible')
    if name == 'tabicl-v2' and 'regressor-v2-20260212' not in manifest['checkpoint']:
        raise ValueError('Generación TabICLv2 no compatible')
    if name == 'tabpfn-3' and manifest['checkpoint'] != 'tabpfn-v3-regressor-v3_default.ckpt':
        raise ValueError('Generación TabPFN-3 no compatible')
    return manifest


def estimator(name):
    import torch
    import random
    random.seed(2026)
    np.random.seed(2026)
    torch.set_num_threads(2)
    if torch.get_num_interop_threads()!=1:
        torch.set_num_interop_threads(1)
    torch.backends.mkldnn.enabled=False
    torch.manual_seed(2026)
    torch.use_deterministic_algorithms(True)
    manifest = configuration(name)
    path = ROOT/'optional'/name/manifest['checkpoint']
    if name == 'tabicl-v2':
        from tabicl import TabICLRegressor
        return TabICLRegressor(model_path=str(path), allow_auto_download=False,
                checkpoint_version=manifest['checkpoint'], n_estimators=8, random_state=2026,
                device='cpu', n_jobs=2, use_amp=False, kv_cache=False, batch_size=8, verbose=False)
    if name == 'tabpfn-3':
        from tabpfn import TabPFNRegressor
        return TabPFNRegressor(model_path=str(path), n_estimators=8, random_state=2026,
                device='cpu', fit_mode='fit_preprocessors', n_preprocessing_jobs=1)
    raise ValueError('Modelo opcional desconocido')


def save_context(destination, X, y, columns, manifest):
    np.savez(destination/'training-context.npz', X=np.asarray(X, dtype=np.float64), y=np.asarray(y, dtype=np.float64))
    atomic_json(destination/'context-contract.json', {'context_hash': sha256(destination/'training-context.npz'),
        'columns': list(columns), 'checkpoint_sha256': manifest['sha256'], 'model': manifest['model'],
        'dependencies': {n: version(n) for n in [manifest['package'], 'torch', 'numpy', 'pandas', 'scikit-learn', 'scipy']},
        'preprocessing': 'Preprocesadores nativos ajustados con contexto de train; sin etiquetas externas.',
        'parameters': manifest['parameters'], 'export_dtype':'float64', 'export_digits':17})


def validate_context(name, destination, override=None):
    manifest = configuration(name)
    contract = override or read(destination/'context-contract.json')
    if (sha256(destination/'training-context.npz') != contract['context_hash'] or
            contract['checkpoint_sha256'] != manifest['sha256'] or contract['model'] != name or
            any(version(package) != value for package, value in contract['dependencies'].items()) or
            contract['parameters'] != manifest['parameters']):
        raise ValueError('Contexto, checkpoint o dependencias incompatibles')
    return np.load(destination/'training-context.npz')


def smoke(name):
    import psutil
    folder = ROOT/'optional'/name
    destination = folder/'synthetic'
    destination.mkdir(exist_ok=True)
    started = time.perf_counter()
    manifest = configuration(name)
    rng = np.random.default_rng(2026)
    X = rng.normal(size=(80, 60))
    y = 3+.2*X[:, 0]+.1*X[:, 1]
    model = estimator(name).fit(X[:60], y[:60])
    prediction = np.asarray(model.predict(X[60:]), dtype=np.float64)
    if not np.isfinite(prediction).all():
        raise ValueError('Preflight sintético produjo valores no finitos')
    pd.DataFrame({'prediction':prediction}).to_csv(destination/'predictions.csv', index=False, float_format='%.17g')
    np.save(destination/'queries.npy', X[60:])
    save_context(destination, X[:60], y[:60], [f'x{i}' for i in range(60)], manifest)
    bad = {**manifest, 'sha256':'0'*64}
    try:
        configuration(name, bad)
    except ValueError:
        checkpoint_guard = True
    else:
        checkpoint_guard = False
    bad_context = {**read(destination/'context-contract.json'), 'context_hash':'0'*64}
    try:
        validate_context(name, destination, bad_context)
    except ValueError:
        context_guard = True
    else:
        context_guard = False
    if not checkpoint_guard or not context_guard:
        raise ValueError('Guardas de identidad incompletas')
    atomic_json(folder/'preflight.json', {'available':True, 'synthetic_only':True, 'manifest':manifest,
        'effective_parameters': {k: repr(v) for k, v in model.get_params().items()},
        'seconds':time.perf_counter()-started, 'rss_mb':psutil.Process().memory_info().rss/1024**2,
        'checkpoint_guard':checkpoint_guard, 'context_guard':context_guard, 'fresh_process_verified':False,
        'limits':{'rss_mb':4096,'seconds_per_configuration':1800,'cpu_threads':2},
        'dependencies':read(destination/'context-contract.json')['dependencies']})
    print(name, 'preflight sintético completado', flush=True)


def verify(name, destination, synthetic=False):
    context = validate_context(name, destination)
    if synthetic:
        queries = np.load(destination/'queries.npy')
        saved = pd.read_csv(destination/'predictions.csv', float_precision='round_trip').prediction.to_numpy()
    else:
        contract = read(destination/'context-contract.json')
        table = pd.read_parquet(PROCESSED/f"features_{contract['table_key']}.parquet")
        master = pd.read_parquet(PROCESSED/'parcels.parquet')
        if list(table.columns) != contract['columns'] or sha256(PROCESSED/f"features_{contract['table_key']}.parquet") != contract['table_hash']:
            raise ValueError('Tabla de consultas incompatible')
        hidden_ids = master.loc[master[TARGET].isna(), ID]
        queries = table.loc[hidden_ids].to_numpy(dtype=np.float64)
        saved = pd.read_csv(destination/'predictions_59.csv', float_precision='round_trip').set_index(ID).loc[hidden_ids, TARGET].to_numpy()
    fitted = estimator(name).fit(context['X'], context['y'])
    pred = np.asarray(fitted.predict(queries), dtype=np.float64)
    np.testing.assert_allclose(pred, saved, atol=1e-10, rtol=0)
    if not synthetic:
        from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
        for scheme,expected in read(destination/'metrics.json').items():
            frame=pd.read_csv(destination/f'oof-{scheme}.csv',float_precision='round_trip')
            got={'rmse':float(np.sqrt(mean_squared_error(frame[TARGET],frame.official))),
                 'mae':float(mean_absolute_error(frame[TARGET],frame.official)),
                 'r2':float(r2_score(frame[TARGET],frame.official)),
                 'bias':float((frame.official-frame[TARGET]).mean())}
            for key,value in expected.items():
                np.testing.assert_allclose(got[key],value,atol=1e-10,rtol=0)
    atomic_json(destination/'fresh-process-check.json', {'passed':True, 'n':len(pred), 'atol':1e-10, 'rtol':0,
                 'context_hash':sha256(destination/'training-context.npz'), 'offline':True,'metrics_recalculated':not synthetic})
    print(name, 'recuperación sin red verificada', len(pred), flush=True)


def run(name, key, destination):
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    def metric(y, p):
        return {'rmse':float(np.sqrt(mean_squared_error(y,p))), 'mae':float(mean_absolute_error(y,p)),
                'r2':float(r2_score(y,p)), 'bias':float(np.mean(p-y))}
    manifest = configuration(name)
    master = pd.read_parquet(PROCESSED/'parcels.parquet').set_index(ID)
    table = pd.read_parquet(PROCESSED/f'features_{key}.parquet').loc[master.index]
    y = master[TARGET]
    labeled_ids, hidden_ids = master.index[y.notna()], master.index[y.isna()]
    assignments = pd.read_csv(ROOT/'registry/schemes.csv')
    metrics = {}
    for scheme in ['principal-5','balanceado-4','rotado-45-5']:
        groups = assignments.loc[assignments.scheme.eq(scheme)].set_index(ID).fold.loc[labeled_ids]
        pred = pd.Series(index=labeled_ids, dtype=float)
        for fold in sorted(groups.unique()):
            tr, va = groups.index[groups.ne(fold)], groups.index[groups.eq(fold)]
            print(name, key, scheme, 'fold', fold, flush=True)
            fitted = estimator(name).fit(table.loc[tr].to_numpy(dtype=float), y.loc[tr].to_numpy())
            pred.loc[va] = np.asarray(fitted.predict(table.loc[va].to_numpy(dtype=float)), dtype=np.float64)
        frame = master.loc[labeled_ids, ['Estado','Municipio','AREA_HA',TARGET]].copy()
        frame['spatial_group'], frame['official'] = groups, pred
        frame.reset_index().to_csv(destination/f'oof-{scheme}.csv', index=False, float_format='%.17g')
        metrics[scheme] = metric(y.loc[labeled_ids], pred)
        atomic_json(destination/f'validation-{scheme}.json', {'metrics':metrics[scheme],
            'by_state':{s:metric(p[TARGET],p.official) for s,p in frame.groupby('Estado')},
            'generation':name,'configuration':key,'selection_by_outer_oof':False})
    fitted = estimator(name).fit(table.loc[labeled_ids].to_numpy(dtype=float), y.loc[labeled_ids].to_numpy())
    pred = np.asarray(fitted.predict(table.loc[hidden_ids].to_numpy(dtype=float)), dtype=np.float64)
    if len(pred) != 59 or not np.isfinite(pred).all() or (pred < 0).any():
        raise ValueError('Predicciones ocultas incompatibles')
    pd.DataFrame({ID:hidden_ids,TARGET:pred}).to_csv(destination/'predictions_59.csv',index=False,float_format='%.17g')
    save_context(destination, table.loc[labeled_ids], y.loc[labeled_ids], table.columns, manifest)
    contract = read(destination/'context-contract.json')
    contract.update(table_key=key,table_hash=sha256(PROCESSED/f'features_{key}.parquet'),training_ids=labeled_ids.tolist())
    atomic_json(destination/'context-contract.json',contract)
    atomic_json(destination/'metrics.json',metrics)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['smoke','verify-smoke','run','verify'])
    parser.add_argument('name',choices=['tabicl-v2','tabpfn-3'])
    parser.add_argument('key',nargs='?')
    parser.add_argument('destination',nargs='?')
    args = parser.parse_args()
    if args.action == 'smoke':
        smoke(args.name)
    elif args.action == 'verify-smoke':
        verify(args.name, ROOT/'optional'/args.name/'synthetic',True)
    elif args.action == 'run':
        run(args.name,args.key,Path(args.destination))
    else:
        verify(args.name,Path(args.destination or args.key))
