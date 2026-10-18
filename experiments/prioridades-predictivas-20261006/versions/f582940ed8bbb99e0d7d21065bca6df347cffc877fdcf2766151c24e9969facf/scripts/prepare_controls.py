"""Copias exactas de procedimientos históricos con destinos nuevos."""
from pathlib import Path
import json
import os
import subprocess
import sys
from prepare_phase import PHASE, PROJECT, SUPPORT, digest, save, copy_verified, copy_code


def main():
    origins = {}
    protocol = json.loads((SUPPORT / 'runs/E00-v2/protocol.json').read_text(encoding='utf-8'))
    support_version = SUPPORT / 'versions' / protocol['code_hash']
    expected = json.loads((support_version / 'manifest.json').read_text(encoding='utf-8'))
    if any(digest(support_version / n) != h for n, h in expected.items()):
        raise ValueError('Versión congelada de C-soporte alterada')
    definitions = [('C-activa', PROJECT, PROJECT), ('C-soporte', support_version, SUPPORT)]
    resolutions = {}
    for name, code_source, data_source in definitions:
        destination = PHASE / 'controls' / name
        copy_code(code_source, destination, origins)
        for folder in ['data/processed', 'data/external']:
            for path in sorted((data_source / folder).glob('*')):
                if path.is_file():
                    copy_verified(path, destination / folder / path.name, origins)
        for folder in ['artifacts', 'registry', 'runs']:
            (destination / folder).mkdir(exist_ok=True)
        if name == 'C-soporte':
            save(destination / 'workspace.json', {'active_root': str(PROJECT),
                 'legacy_root': str(PROJECT / 'experiments/regional-20261003'),
                 'snapshot': str(PROJECT / 'artifacts/versions/selection-current-20261003'),
                 'run_id': name})
            copy_verified(SUPPORT / 'active-manifest.json', destination / 'active-manifest.json', origins)
            copy_verified(SUPPORT / 'runs/E00-v2/protocol.json', destination / 'provenance/original-protocol.json', origins)
        for name_contract in ['contract_official.json', 'contract_selected.json']:
            source_contract = (PROJECT / 'artifacts' if name == 'C-activa' else
                               SUPPORT / 'runs/E00-v2/artifacts') / name_contract
            copy_verified(source_contract, destination / 'provenance' / name_contract, origins)
        env = {k: v for k, v in os.environ.items() if k not in ['PYTHONPATH', 'AGROCEBADA_ARTIFACTS']}
        env.update(PYTHONPATH=str(destination / 'src'), PYTHONDONTWRITEBYTECODE='1')
        code = ('import json; from agrocebada import common,modeling; '
                'print(json.dumps({"root":str(common.ROOT),"processed":str(common.PROCESSED),'
                '"artifacts":str(common.ARTIFACTS),"module":modeling.__file__,"code_hash":common.code_hash()}))')
        result = subprocess.run([sys.executable, '-c', code], env=env, cwd=destination,
                                capture_output=True, text=True, check=True)
        paths = json.loads(result.stdout)
        if Path(paths['root']) != destination or Path(paths['artifacts']) != destination / 'artifacts':
            raise ValueError('Control resolvió rutas ajenas')
        if not Path(paths['module']).is_relative_to(destination):
            raise ValueError('Importación externa a la versión')
        if name == 'C-soporte' and paths['code_hash'] != protocol['code_hash']:
            raise ValueError('C-soporte no conserva identidad del código congelado')
        resolutions[name] = {**paths, 'source': str(code_source), 'new_results': None,
                             'dependency_lock_sha256': digest(destination / 'requirements.lock')}
    save(PHASE / 'registry/control-copy-origins.json', origins)
    save(PHASE / 'registry/control-resolution.json', resolutions)
    print(json.dumps(resolutions, ensure_ascii=False))


if __name__ == '__main__':
    main()
