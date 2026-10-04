"""Marca únicamente la tarea fresca y exacta devuelta por OpenSpec."""
import json
import subprocess
import sys
from pathlib import Path
CHANGE='seleccion-robusta-con-correccion-regional'
ROOT=Path(__file__).resolve().parents[1]
def instructions():
    result=subprocess.run(['openspec.cmd','instructions','apply','--change',CHANGE,'--json'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',check=True)
    return json.loads(result.stdout)
if __name__=='__main__':
    for task_id in sys.argv[1:]:
        fresh=instructions();task=next(t for t in fresh['tasks'] if t['description'].startswith(task_id+' ') or t['id']==task_id)
        if task['done']:continue
        path=Path(fresh['contextFiles']['tasks'][0]);lines=path.read_text(encoding='utf-8').splitlines()
        matches=[i for i,line in enumerate(lines) if line=='- [ ] '+task['description']]
        if len(matches)!=1:raise ValueError('Checkbox no coincide con instrucciones frescas')
        lines[matches[0]]=lines[matches[0]].replace('- [ ]','- [x]',1)
        path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        after=instructions();assert next(t for t in after['tasks'] if t['id']==task['id'])['done']
        assert after['progress']['complete']==fresh['progress']['complete']+1
        print(task_id,after['progress'])
