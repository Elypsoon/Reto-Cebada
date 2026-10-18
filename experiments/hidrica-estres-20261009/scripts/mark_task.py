"""Actualiza exactamente una tarea tras comprobar su texto y ubicación."""
import sys,json,subprocess
from pathlib import Path
project=Path(__file__).resolve().parents[3]
change='disponibilidad-hidrica-y-estres-agroclimatico'
cli=project/'node_modules/@fission-ai/openspec/bin/openspec.js'
raw=subprocess.check_output(['node',str(cli),'instructions','apply','--change',change,'--json'],cwd=project)
info=json.loads(raw)
task=next(t for t in info['tasks'] if t['description'].startswith(sys.argv[1]+' '))
assert not task['done']
p=Path(task['sourcePath']);lines=p.read_text(encoding='utf-8').splitlines()
index=task['line']-1
assert lines[index]=='- [ ] '+task['description']
lines[index]='- [x] '+task['description']
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
updated=json.loads(subprocess.check_output(['node',str(cli),'instructions','apply','--change',change,'--json'],cwd=project))
assert next(t for t in updated['tasks'] if t['id']==task['id'])['done']
assert updated['progress']['complete']==info['progress']['complete']+1
print(sys.argv[1],updated['progress'])
