"""Recibo final de integridad, cobertura y recuperación; sin entrenamiento."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from agrocebada.common import ROOT, sha256
from agrocebada.tracking import atomic_json, check_manifest


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    protected = read(ROOT/'registry/source-integrity.json')
    assert all(sha256(r['source']) == r['sha256'] for r in protected.values())
    audit = ROOT/'registry/historic-recovery'
    plan = read(audit/'plan.json')
    checked = 0
    for case in plan['inference_cases']:
        for name, record in case['input_manifest'].items():
            assert sha256(Path(case['root'])/name) == sha256(record['source']) == record['sha256']
            checked += 1
    optional_plan = read(audit/'optional-plan.json')
    for name, record in optional_plan['input_manifest'].items():
        assert sha256(Path(optional_plan['root'])/name) == sha256(record['source']) == record['sha256']
        checked += 1
    historical = read(audit/'summary.json')
    optional = read(audit/'optional-summary.json')
    assert historical['passed'] and len(historical['cases']) == 12
    assert optional['passed'] and len(optional['contexts']) == 2
    for case in historical['cases']:
        assert case['passed'] and case['offline']
        assert all(r['passed'] and r['n'] == 59 and r['no_refit'] for r in case['routes'].values())
    for context in optional['contexts']:
        assert context['passed'] and context['predictions'] == 59 and context['tolerance'] == 1e-10
        resource = read(audit/f'resources-original-env-{context["run_id"]}.json')
        assert resource['exit_code'] == 0 and resource['offline'] and resource['ip_socket_connections_blocked']
    suites = ET.parse(ROOT/'registry/closing-tests.xml').getroot().findall('testsuite')
    assert sum(int(s.get('tests', 0)) for s in suites) == 47
    assert all(int(s.get(k, 0)) == 0 for s in suites for k in ['errors', 'failures', 'skipped'])
    packages = read(ROOT/'registry/package-verification.json')
    assert packages['passed'] and len(packages['runs']) == 12
    frozen = read(ROOT/'registry/frozen-priority.json')
    version = ROOT/'versions'/frozen['version']
    assert sha256(version/'manifest.json') == frozen['snapshot_manifest_hash']
    assert check_manifest(version, read(version/'manifest.json'))
    states = read(ROOT/'registry/priority-summary.json')
    coverage = read(ROOT/'registry/coverage-final.json')
    assert len(coverage['hypotheses']) == 9
    assert all(h['status'] == 'completed' for h in coverage['hypotheses'])
    assert all(s['status'] == 'completed' and s['verified'] and s['predictively_tested'] for s in states)
    assert all(not s[k] for s in states for k in ['activated', 'deployed', 'sent'])
    detail = read(ROOT/'docs/detailed-results.json')
    assert set(detail) == {s['run_id'] for s in states}
    for run in detail.values():
        for scheme in run.values():
            for route in scheme.values():
                assert route['metrics']['n'] == 138
                assert all(route.get(key) for key in ['by_state', 'by_fold', 'by_area'])
    decision = read(ROOT/'registry/P06-eligibility.json')
    assert not decision['eligible'] and decision['state_failures']
    assert all(not decision[k] for k in ['activated', 'deployed', 'sent'])
    receipt = {'passed': True, 'protected_files_intact': len(protected),
        'historical_copy_and_source_hash_pairs': checked, 'frozen_version_intact': frozen['version'],
        'historical_standard_cases': 12, 'historical_routes_per_case': 2,
        'historical_optional_contexts': 2, 'historical_optional_pending': 0,
        'n_queries_per_route': 59, 'new_verified_runs': len(states), 'closing_tests_passed': 47,
        'atol': 1e-10, 'rtol': 0, 'activated': False, 'deployed': False, 'sent': False,
        'preserved_failed_attempts': [{'receipt': 'historic-recovery/resources-E07-v3-monthly_20_10.json',
            'reason': 'Primer supervisor impuso entorno numérico nuevo. Se recuperaron ambos contextos con su entorno histórico, sin cambiar fuente, parámetros ni tolerancia.'}],
        'evidence': 'Desarrollo sobre las mismas 138 etiquetas; sin otra campaña validada.'}
    atomic_json(ROOT/'registry/final-integrity-receipt.json', receipt)
    atomic_json(audit/'final-summary.json', {**historical, 'optional_contexts_pending': [],
                 'optional_contexts_recovered': optional['contexts'], 'all_original_hashes_intact': True})
    print('Cierre verificado: 12 ejecuciones nuevas; 12 versiones históricas × 2 rutas + 2 contextos; 47 pruebas', flush=True)


if __name__ == '__main__':
    main()
