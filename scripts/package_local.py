"""Empaqueta archivos autorizados y comprueba una extracción limpia."""
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime,timezone
from pathlib import Path
from agrocebada.common import ROOT,ARTIFACTS,sha256,write_json

dist=ROOT/"dist";dist.mkdir(exist_ok=True)
archive=dist/"agrocebada-local-2025-10-31.zip"
files=[]
excluded_directories={".git","__pycache__",".pytest_cache","node_modules","dist",".wrangler","versions"}
for folder in ["src","tests","scripts","docs","data","artifacts","openspec","frontend","experiments/estratificacion-pyr-20261018","experiments/fisiologia-siniestros-20261018","output/pdf","output/audit"]:
    for base,directories,names in os.walk(ROOT/folder):
        directories[:]=[name for name in directories if name not in excluded_directories
            and (Path(base)/name).relative_to(ROOT).parts[:2] not in [("docs","clips"),("docs","deployments")]]
        for name in names:
            p=Path(base)/name
            rel=p.relative_to(ROOT)
            if rel.parts[:2] in [("docs", "clips"), ("docs", "deployments")]:continue
            if p.suffix == '.tsbuildinfo' or p.name == 'voice_record.mp4':continue
            if p.name.startswith("app-server.") or p.name=="package-check.json":continue
            files.append(p)
for name in ["pyproject.toml","requirements.txt","requirements.lock","README.md","package.json","package-lock.json",".gitignore",".gitattributes"]:
    p=ROOT/name
    if p.exists():files.append(p)
with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(files):z.write(p,p.relative_to(ROOT).as_posix())
clean=ROOT/"verification"/("package-run-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"))
clean.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(archive) as z:
    for member in z.infolist():
        if not (clean/member.filename).resolve().is_relative_to(clean.resolve()):raise ValueError("Ruta de paquete fuera de la extracción autorizada")
    z.extractall(clean)
env=os.environ.copy();env["PYTHONPATH"]=str(clean/"src");env["PYTHONIOENCODING"]="utf-8"
verification=subprocess.run([sys.executable,"-c","from pathlib import Path;from agrocebada.common import ROOT;from agrocebada.inference import verify_artifacts;assert ROOT==Path.cwd();print(verify_artifacts())"],cwd=clean,env=env,capture_output=True,text=True,encoding="utf-8",check=True)
tests=subprocess.run([sys.executable,"-m","pytest","-q"],cwd=clean,env=env,capture_output=True,text=True,encoding="utf-8",check=True)
check={"clean_directory":str(clean.relative_to(ROOT)),"fresh_process":True,"existing_pinned_environment":True,"reinstalled_dependencies":False,"source_loaded_from_package":True,"files":len(files),"verification":verification.stdout.strip(),"tests":tests.stdout.strip(),"official_delivery":"Interfaz oficial publicada en Cloudflare; este paquete no publica ni realiza el envío al organizador"}
write_json(ARTIFACTS/"package-check.json",check)
with zipfile.ZipFile(archive,"a",compression=zipfile.ZIP_DEFLATED) as z:z.write(ARTIFACTS/"package-check.json","artifacts/package-check.json")
write_json(dist/"manifest.json",{"file":archive.name,"sha256":sha256(archive),"bytes":archive.stat().st_size,"files":len(files)+1,"created_utc":datetime.now(timezone.utc).isoformat(),"model_hash":json.loads((ARTIFACTS/"contract_selected.json").read_text(encoding="utf-8"))["model_hash"]})
print(verification.stdout,tests.stdout,archive,flush=True)
