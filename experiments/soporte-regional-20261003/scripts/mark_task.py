"""Marca exclusivamente una tarea existente después de comprobar su texto actual."""
from pathlib import Path
import json
import re
import subprocess
import sys

root=Path(__file__).resolve().parents[3]
change='experimentos-trazables-con-soporte-regional'
path=root/'openspec/changes'/change/'tasks.md'
for task in sys.argv[1:]:
    value=path.read_text(encoding='utf-8')
    pattern=rf'^- \[ \] {re.escape(task)} .+$'
    matches=list(re.finditer(pattern,value,re.M))
    if len(matches)!=1:
        raise ValueError(f'La tarea {task} cambió o ya está cerrada; actualizar instrucciones')
    match=matches[0]
    print('Completa:',match.group(),flush=True)
    value=value[:match.start()]+match.group().replace('- [ ]','- [x]',1)+value[match.end():]
    path.write_text(value,encoding='utf-8')
    result=subprocess.run(['openspec.cmd','instructions','apply','--change',change,'--json'],cwd=root,capture_output=True,text=True,encoding='utf-8',check=True)
    state=json.loads(result.stdout)
    assert next(t for t in state['tasks'] if t['description'].startswith(task+' '))['done']
    print(state['progress'])
