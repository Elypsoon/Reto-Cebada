"""Marca únicamente tareas verificadas, usando la ubicación actual del CLI."""
import json
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
cli=root/"node_modules/.bin/openspec.cmd"
def state():
    result=subprocess.run([str(cli),"instructions","apply","--change","prediccion-cebada-con-datos-verificados","--json"],cwd=root,capture_output=True,text=True,encoding="utf-8",check=True)
    return json.loads(result.stdout)
for description_id in sys.argv[1:]:
    before=state();task=next(t for t in before["tasks"] if t["description"].startswith(description_id+" "))
    if task["done"]:continue
    path=Path(task["sourcePath"]);lines=path.read_text(encoding="utf-8-sig").splitlines(keepends=True);i=task["line"]-1
    if lines[i].strip()!="- [ ] "+task["description"]:raise RuntimeError("La ubicación de la tarea cambió")
    lines[i]=lines[i].replace("- [ ]","- [x]",1);path.write_text("".join(lines),encoding="utf-8")
    after=state()
    assert next(t for t in after["tasks"] if t["id"]==task["id"])["done"]
    assert after["progress"]["complete"]==before["progress"]["complete"]+1
    print(description_id,json.dumps(after["progress"]),flush=True)
