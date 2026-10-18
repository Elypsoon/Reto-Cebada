"""Conserva el bloqueo real, la omisión justificada y la integridad durante la pausa."""
from pathlib import Path
from cimmyt.common import ROOT, read, save, digest, now

audit = read(ROOT / 'registry/label-audit.json')
local = audit['before_spatial']['C-local']['rows']
assert local == 29 and local < 30
for run in ['A01', 'A02', 'A03']:
    path = ROOT / 'runs' / run / 'run.json'
    if path.exists() and read(path).get('status') != 'pending':
        raise ValueError('Este recibo parcial no puede sobrescribir una ejecución iniciada: ' + run)
optional_path = ROOT / 'runs/A04/run.json'
if optional_path.exists() and read(optional_path).get('status') != 'non_viable':
    raise ValueError('El recibo parcial no puede sobrescribir A04')
save(ROOT / 'runs/A04/run.json', {'status': 'non_viable', 'verified': False,
     'predictively_tested': False, 'administratively_closed': True,
     'reason': 'C-local tiene como máximo 29 etiquetas candidatas antes de exclusión espacial; el protocolo exige al menos 30 por ajuste',
     'candidate_upper_bound': local, 'required_minimum': 30,
     'cohort_evidence_sha256': digest(ROOT / 'registry/label-audit.json'),
     'configurations': ['official_common', 'official_common_plus_local_cap256'],
     'metrics': None, 'activated': False, 'deployed': False, 'sent': False, 'at': now()})
for run in ['A01', 'A02', 'A03']:
    save(ROOT / 'runs' / run / 'run.json', {'status': 'pending', 'predictively_tested': False,
         'metrics': None, 'reason': 'Preparación y protocolo sin congelar: admisión espacial pendiente',
         'activated': False, 'deployed': False, 'sent': False})
save(ROOT / 'registry/blocker.json', {'status': 'needs_protocol_decision', 'at': now(),
    'issue': 'Los originales entregan puntos sin polígonos ni datum declarado; no permiten aplicar las envolventes espaciales aprobadas',
    'blocked_tasks': ['2.5', '2.6', '3.1', '3.3', '3.4', '4.7', '5.2'],
    'options': ['Metadatos documentados para el protocolo vigente', 'Revisión explícita para diagnóstico por puntos aproximados'],
    'report': 'docs/auditoria-cimmyt.md', 'label_candidates_national': 48,
    'admitted_training_labels': None, 'active_changed': False})
protected = read(ROOT / 'registry/protected-files.json')
changed = [name for name, expected in protected.items() if not Path(name).is_file() or digest(name) != expected]
save(ROOT / 'registry/interim-integrity.json', {'at': now(), 'files_checked': len(protected),
     'passed': not changed, 'changed_files': changed, 'training_with_cimmyt_started': False})
if changed:
    raise ValueError('Se alteraron archivos protegidos; ver recibo')
print(f'Integridad verificada: {len(protected)} archivos previos intactos. A04 no viable; A01-A03 pendientes, sin métricas inventadas.')
