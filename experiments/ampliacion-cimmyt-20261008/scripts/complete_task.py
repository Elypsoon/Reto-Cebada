"""Actualiza una sola tarea comprobada y confirma el avance devuelto por OpenSpec."""
import json
import subprocess
import shutil
import sys
from pathlib import Path

NAME = 'ampliacion-entrenamiento-cebada-con-cimmyt'
def instructions():
    executable = shutil.which('openspec.cmd')
    if executable is None:
        raise ValueError('OpenSpec no encontrado')
    result = subprocess.run([executable, 'instructions', 'apply', '--change', NAME, '--json'],
        capture_output=True, text=True, encoding='utf-8', check=True)
    return json.loads(result.stdout)

key = sys.argv[1]
before = instructions()
task = next(t for t in before['tasks'] if t['description'].startswith(key + ' '))
if task['done']:
    raise ValueError('Tarea ya completada; no sobrescribir')
path = Path(before['contextFiles']['tasks'][0])
lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
indices = [i for i, line in enumerate(lines) if line.strip() == '- [ ] ' + task['description']]
if len(indices) != 1:
    raise ValueError('La tarea cambió: volver a leer instrucciones')
line = indices[0]
lines[line] = lines[line].replace('- [ ] ', '- [x] ', 1)
path.write_text(''.join(lines), encoding='utf-8')
after = instructions()
assert next(t for t in after['tasks'] if t['id'] == task['id'])['done']
assert after['progress']['complete'] == before['progress']['complete'] + 1
print(json.dumps({'task': key, 'progress': after['progress']}))
