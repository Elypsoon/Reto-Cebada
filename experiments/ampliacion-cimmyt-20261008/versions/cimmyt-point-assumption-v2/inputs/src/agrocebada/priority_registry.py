"""Registro inmutable de protocolo y cobertura predictiva distinta del cierre."""
from datetime import datetime, timezone
from pathlib import Path
import json
from .common import ROOT, sha256
from .tracking import atomic_json, manifest, check_manifest

TERMINAL = {'completed', 'failed', 'interrupted', 'non_viable', 'skipped'}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class PriorityRegistry:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        (self.root/'registry').mkdir(parents=True, exist_ok=True)
        (self.root/'runs').mkdir(exist_ok=True)

    def create(self, run_id, protocol):
        folder = self.root/'runs'/run_id
        folder.mkdir(exist_ok=False)
        (folder/'artifacts').mkdir()
        atomic_json(folder/'protocol.json', protocol)
        state = {'run_id': run_id, 'block': protocol['block'], 'status': 'frozen',
                 'protocol_hash': sha256(folder/'protocol.json'), 'created_at': timestamp(),
                 'metrics': None, 'verified': False, 'predictively_tested': False,
                 'administratively_closed': False, 'activated': False, 'deployed': False, 'sent': False}
        atomic_json(folder/'run.json', state)
        self.event(run_id, 'frozen')
        return folder

    def state(self, run_id):
        return json.loads((self.root/'runs'/run_id/'run.json').read_text(encoding='utf-8'))

    def event(self, run_id, status, reason=None):
        with (self.root/'registry/priority-events.jsonl').open('a', encoding='utf-8') as output:
            output.write(json.dumps({'run_id': run_id, 'status': status, 'at': timestamp(), 'reason': reason}, ensure_ascii=False)+'\n')

    def validate(self, run_id):
        state = self.state(run_id)
        folder = self.root/'runs'/run_id
        if sha256(folder/'protocol.json') != state['protocol_hash']:
            raise ValueError('Protocolo alterado; ID de ejecución no reutilizable')
        protocol = json.loads((folder/'protocol.json').read_text(encoding='utf-8'))
        for path, digest in protocol.get('input_manifest', {}).items():
            if not (self.root/path).is_file() or sha256(self.root/path) != digest:
                raise ValueError('Código, datos, checkpoint o dependencia alterados: '+path)
        return protocol

    def transition(self, run_id, status, reason=None, metrics=None, verified=False):
        state = self.state(run_id)
        if state['status'] in TERMINAL:
            raise ValueError('Ejecución cerrada; crear un reintento con ID nuevo')
        if status not in TERMINAL | {'running'} or (status == 'completed' and not verified):
            raise ValueError('Transición no válida o verificación incompleta')
        self.validate(run_id)
        if status == 'running' and state['status'] != 'frozen':
            raise ValueError('Una ejecución en marcha no se duplica')
        state.update(status=status, reason=reason)
        if status == 'running':
            state['started_at'] = timestamp()
        else:
            state.update(finished_at=timestamp(), administratively_closed=True,
                         predictively_tested=status == 'completed' and bool(verified), verified=bool(verified), metrics=metrics)
            atomic_json(self.root/'runs'/run_id/'artifact-manifest.json', manifest(self.root/'runs'/run_id/'artifacts'))
        atomic_json(self.root/'runs'/run_id/'run.json', state)
        self.event(run_id, status, reason)
        self.publish()

    def publish(self):
        states = []
        for folder in sorted((self.root/'runs').iterdir()):
            if not (folder/'run.json').is_file():
                continue
            state = self.state(folder.name)
            if state['status'] in TERMINAL and not check_manifest(folder/'artifacts', json.loads((folder/'artifact-manifest.json').read_text(encoding='utf-8'))):
                state = {**state, 'status': 'integrity_error', 'predictively_tested': False, 'verified': False}
            states.append(state)
        atomic_json(self.root/'registry/priority-summary.json', states)
        docs = self.root/'docs'
        docs.mkdir(exist_ok=True)
        lines = ['# Ejecuciones prioritarias', '', 'Evidencia de desarrollo sobre las mismas 138 etiquetas; no valida otra campaña.', '',
                 '| Ejecución | Estado | Evaluación predictiva verificada | Motivo |', '| --- | --- | --- | --- |']
        lines += [f"| {s['run_id']} | {s['status']} | {s['predictively_tested']} | {s.get('reason') or 'pendiente'} |" for s in states]
        (docs/'priority-runs.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
