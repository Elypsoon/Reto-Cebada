"""Adapta rutas de ejecución al checkout; no altera código, datos o modelos."""
from pathlib import Path
import sys,json,hashlib,subprocess,shutil
root=Path(__file__).resolve().parents[1]
raw=root/'DataSet';alias=root/'Reto-Cebada/DataSet'
if not raw.is_dir():raise ValueError('Faltan los originales de DataSet/')
if alias.exists():
    if alias.resolve()!=raw.resolve():raise ValueError('La vista de originales ya existe y apunta a otro destino')
else:
    alias.parent.mkdir(exist_ok=True)
    if sys.platform=='win32':
        def psquote(value):return "'"+str(value).replace("'","''")+"'"
        subprocess.run(['powershell','-NoProfile','-Command',f"New-Item -ItemType Junction -Path {psquote(alias)} -Target {psquote(raw)} | Out-Null"],check=True)
    else:alias.symlink_to(raw,target_is_directory=True)
changes=[]
for phase in ['regional-20261003','soporte-regional-20261003']:
    path=root/'experiments'/phase/'workspace.json'
    original=path.with_name('workspace.origin.json')
    if not original.exists():shutil.copy2(path,original)
    value=json.loads(original.read_text(encoding='utf-8'));previous=Path(value['active_root'])
    revised=dict(value)
    for key in ['active_root','legacy_root','snapshot']:
        if key not in value:continue
        # Los manifiestos originales guardan rutas Windows; se interpreta su raíz
        # declarada, incluso al materializar el checkout desde Linux/macOS.
        old=value[key].replace('\\','/');base=str(previous).replace('\\','/').rstrip('/')
        if old==base:revised[key]=str(root)
        elif old.startswith(base+'/'):revised[key]=str(root/old[len(base)+1:])
        else:raise ValueError('Ruta de procedencia no contenida en su raíz')
    path.write_text(json.dumps(revised,ensure_ascii=False,indent=2),encoding='utf-8')
    changes.append({'phase':phase,'original_workspace_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'runtime_workspace_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'original':str(original.relative_to(root))})
(root/'checkout-relocation.json').write_text(json.dumps({'runtime_root':str(root),'workspace_configuration':changes,'code_data_models_unchanged':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('Rutas de ejecución configuradas; metadatos originales conservados en workspace.origin.json.')
