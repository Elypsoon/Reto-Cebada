"""Auditoría de cierre; lee resultados cerrados sin ajustar ni seleccionar modelos."""
import json
import subprocess
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from agrocebada.common import ROOT, ID, TARGET, sha256
from agrocebada.tracking import atomic_json, check_manifest
from agrocebada.priority_registry import PriorityRegistry
from agrocebada.priority_data import load


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    frozen = read(ROOT/'registry/frozen-priority.json')
    snapshot = ROOT/'versions'/frozen['version']
    assert sha256(snapshot/'manifest.json') == frozen['snapshot_manifest_hash']
    assert check_manifest(snapshot, read(snapshot/'manifest.json'))
    environments = {}
    for name, environment, lock in [
        ('mandatory', ROOT/'.venv', ROOT/'requirements.lock'),
        ('tabicl-v2', ROOT/'optional/tabicl-v2/env', ROOT/'optional/tabicl-v2/requirements.lock'),
        ('tabpfn-3', ROOT/'optional/tabpfn-3/env', ROOT/'optional/tabpfn-3/requirements.lock'),
    ]:
        pins = dict(line.split('==', 1) for line in lock.read_text().splitlines() if '==' in line)
        code = 'import json; from importlib.metadata import version; print(json.dumps({n:version(n) for n in '+repr(list(pins))+'}))'
        installed = json.loads(subprocess.check_output([str(environment/'Scripts/python.exe'), '-c', code], text=True))
        assert pins == installed, name
        environments[name] = {'verified': True, 'packages': len(pins), 'lock_sha256': sha256(lock), 'installed': installed}
    registry = PriorityRegistry()
    states = read(ROOT/'registry/priority-summary.json')
    assert len(states) == 12
    master = pd.read_parquet(ROOT/'data/processed/parcels.parquet').set_index(ID)
    hidden = master.index[master[TARGET].isna()]
    labelled = set(master.index[master[TARGET].notna()])
    results = []
    for state in states:
        run_id = state['run_id']
        art = ROOT/'runs'/run_id/'artifacts'
        protocol = registry.validate(run_id)
        assert state['status'] == 'completed' and state['verified'] and state['predictively_tested']
        assert not any(state[k] for k in ['activated', 'deployed', 'sent'])
        assert check_manifest(art, read(art.parent/'artifact-manifest.json'))
        package = read(art/'recovery-package.json')
        assert Path(package['snapshot']) == snapshot
        assert package['snapshot_manifest_hash'] == sha256(snapshot/'manifest.json')
        assert package['protocol_hash'] == sha256(art.parent/'protocol.json') == state['protocol_hash']
        verification = read(art/'fresh-process-check.json')
        assert verification['passed'] and verification['offline'] and verification['metrics_recalculated']
        assert verification.get('n', verification.get('n_per_route')) == 59
        assert verification['atol'] == 1e-10 and verification['rtol'] == 0
        for action in ['run', 'verify']:
            resource = read(art/f'resources-{action}.json')
            assert resource['exit_code'] == 0 and resource['reason'] is None
            assert resource['offline'] and resource['ip_socket_connections_blocked'] and resource['includes_children']
        schemes = []
        for path in sorted(art.glob('oof-*.csv')):
            frame = pd.read_csv(path, float_precision='round_trip')
            assert len(frame) == 138 and frame[ID].is_unique and set(frame[ID]) == labelled
            assert np.isfinite(frame['official']).all()
            schemes.append(path.stem.removeprefix('oof-'))
        assert {'principal-5', 'balanceado-4', 'rotado-45-5'} <= set(schemes)
        prediction_paths = ([art/'predictions_59.csv', art/'predictions_official_only_59.csv']
                            if state['block'] == 'P00' else
                            [art/'predictions_59.csv'])
        for path in prediction_paths:
            frame = pd.read_csv(path, float_precision='round_trip')
            assert len(frame) == 59 and frame[ID].is_unique and set(frame[ID]) == set(hidden)
            assert np.isfinite(frame[TARGET]).all()
        fitted = 'training-context.npz' if state['block'] in ['P07', 'P08'] else 'model_official.joblib' if state['block'] == 'P00' else 'model.joblib'
        assert (art/fitted).is_file()
        results.append({'run_id': run_id, 'passed': True, 'schemes': schemes, 'n_per_scheme': 138,
                        'n_queries_per_route': 59, 'offline_fresh_process': True,
                        'metrics_recalculated': True, 'artifact_manifest_sha256': sha256(art.parent/'artifact-manifest.json'),
                        'fitted_object_or_context': fitted, 'fitted_sha256': sha256(art/fitted)})
    atomic_json(ROOT/'registry/package-verification.json', {'passed': True, 'snapshot': frozen['version'],
                'snapshot_manifest_intact': True, 'environments': environments, 'runs': results,
                'new_training_or_selection': False, 'atol': 1e-10, 'rtol': 0})
    # Verifica que inferir P06 no requiere tablas NASA ni consultas etiquetadas.
    with threadpool_limits(2):
        master, tables, _ = load()
        bundle = joblib.load(ROOT/'runs/P06/artifacts/model.joblib')
        model = bundle['model']
        required = {c.representation for c in model.candidates}
        assert required <= {'compact', 'functional'}
        minimal = {key: tables[key].loc[hidden] for key in required}
        assert not any('nasa' in str(c).lower() for table in minimal.values() for c in table.columns)
        prediction = model.predict(minimal, hidden)
        saved = pd.read_csv(ROOT/'runs/P06/artifacts/predictions_59.csv', float_precision='round_trip').set_index(ID).loc[hidden, TARGET]
        np.testing.assert_allclose(prediction, saved, atol=1e-10, rtol=0)
        cal = bundle['interval']
        assert not set(cal['fit_ids']) & set(cal['calibration_ids'])
        assert len(cal['calibration_ids']) >= 25 and set(cal['fit_ids']) | set(cal['calibration_ids']) == labelled
        needed = {c.representation for c in cal['model'].candidates}
        centers = cal['model'].predict({key: tables[key].loc[hidden] for key in needed}, hidden)
        output = pd.DataFrame({ID: hidden, 'calibrated_center_t_ha': centers,
                              'interval_low': centers-cal['radius'], 'interval_high': centers+cal['radius']})
        assert np.isfinite(output.iloc[:, 1:]).all().all()
        output.to_csv(ROOT/'registry/P06-recovered-intervals-59.csv', index=False, float_format='%.17g')
        atomic_json(ROOT/'registry/P06-official-inputs-check.json', {'passed': True,
            'n_queries': 59, 'representations': sorted(required), 'no_nasa_columns': True,
            'query_rows_only': True, 'no_fit': True, 'atol': 1e-10, 'rtol': 0,
            'calibration_n': len(cal['calibration_ids']), 'interval_radius': cal['radius'],
            'interval_center': 'Modelo separado ajustado excluyendo calibración; distinto al modelo puntual completo',
            'purpose': 'Recuperación de investigación; P06 no elegible, sin activación ni entrega'} )
    print('12 paquetes, 3 entornos y P06 con entradas oficiales verificados', flush=True)


if __name__ == '__main__':
    main()
