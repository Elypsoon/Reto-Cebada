"""Protocolo inmutable y cierre únicamente después de recuperación verificable."""
import re
from pathlib import Path
import hashlib
from .common import ROOT, read, save, digest, now

TERMINAL={'completed','failed','interrupted','non_viable','skipped'}


def semantic_hash(path):
    text=Path(path).read_text(encoding='utf-8-sig')
    # El seguimiento de tareas cambia checkboxes, no el contrato congelado.
    text=re.sub(r'(?m)^- \[[ x]\] ', '- [ ] ',text)
    return hashlib.sha256(text.encode()).hexdigest()


def artifact_manifest(folder):
    return {str(p.relative_to(folder)):digest(p) for p in sorted(Path(folder).rglob('*')) if p.is_file()}


class Registry:
    def __init__(self, root=ROOT): self.root=Path(root)

    def protocol(self):
        path=self.root/'registry/protocol-v2.json';protocol=read(path)
        if digest(path)!=(self.root/'registry/protocol-v2.sha256').read_text(encoding='utf-8').strip():
            raise ValueError('Protocolo alterado bajo el mismo identificador')
        for relative,expected in protocol['inputs'].items():
            p=self.root/relative
            if not p.is_file() or digest(p)!=expected:
                raise ValueError('Entrada congelada alterada: '+relative)
        for item in protocol['planning']:
            if semantic_hash(item['current_path'])!=item['semantic_sha256']:
                raise ValueError('Contrato de planificación alterado; revisar con versión nueva')
            if digest(self.root/item['snapshot'])!=item['sha256']:
                raise ValueError('Antecedente de planificación alterado')
        return protocol

    def state(self,run): return read(self.root/f'runs/{run}/run.json')

    def event(self,run,status,reason=None):
        with (self.root/'registry/events-v2.jsonl').open('a',encoding='utf-8') as file:
            import json
            file.write(json.dumps({'run':run,'status':status,'reason':reason,'at':now()},ensure_ascii=False)+'\n')

    def transition(self,run,status,reason=None,metrics=None):
        self.protocol();folder=self.root/f'runs/{run}';state=self.state(run)
        if state['status'] in TERMINAL: raise ValueError('ID cerrado; no reutilizable')
        if status=='running' and state['status']!='frozen': raise ValueError('No duplicar ejecución')
        if status not in TERMINAL|{'running'}: raise ValueError('Transición desconocida')
        if status=='completed':
            if state['status']!='running':raise ValueError('Solo una ejecución iniciada puede completarse')
            if not (folder/'artifacts/fresh-process-check.json').is_file():
                raise ValueError('Recuperación completa sin red obligatoria antes del cierre')
            receipt=read(folder/'artifacts/fresh-process-check.json')
            if not receipt.get('passed') or not receipt.get('offline') or metrics is None:
                raise ValueError('Recuperación completa sin red obligatoria antes del cierre')
        elif metrics is not None: raise ValueError('Métricas solo para comparación completada')
        state.update(status=status,reason=reason,at=now(),metrics=metrics,
            verified=status=='completed',predictively_tested=status=='completed',
            administratively_closed=status in TERMINAL,activated=False,deployed=False,sent=False)
        if status in TERMINAL:
            save(folder/'artifact-manifest.json',artifact_manifest(folder/'artifacts'))
        save(folder/'run.json',state);self.event(run,status,reason)

    def check_closed(self,run):
        state=self.state(run);folder=self.root/f'runs/{run}'
        if state['status'] not in TERMINAL: return False
        return read(folder/'artifact-manifest.json')==artifact_manifest(folder/'artifacts')
