"""Obtiene solo el checkpoint predeclarado y documenta su identidad."""
from pathlib import Path
import json,hashlib,requests
root=Path(__file__).resolve().parents[1]/'optional/tabpfn-2.5'
root.mkdir(parents=True,exist_ok=True)
name='tabpfn-v2.5-regressor-v2.5_default.ckpt'
base='https://huggingface.co/Prior-Labs/tabpfn_2_5'
response=requests.get('https://huggingface.co/api/models/Prior-Labs/tabpfn_2_5?blobs=true',timeout=30);response.raise_for_status()
meta=response.json();file=next(s for s in meta['siblings'] if s['rfilename']==name)
destination=root/name
if not destination.exists():
    with requests.get(base+'/resolve/'+meta['sha']+'/'+name,stream=True,timeout=60) as result:
        result.raise_for_status()
        with destination.open('wb') as output:
            for block in result.iter_content(1024**2):output.write(block)
digest=hashlib.sha256(destination.read_bytes()).hexdigest()
if digest!=file['lfs']['sha256']:raise ValueError('El checkpoint no coincide con el hash publicado')
license_response=requests.get(base+'/resolve/'+meta['sha']+'/LICENSE',timeout=30);license_response.raise_for_status();(root/'LICENSE').write_bytes(license_response.content)
info={'repository':base,'revision':meta['sha'],'checkpoint':name,'sha256':digest,'bytes':destination.stat().st_size,'license_file':'LICENSE','license_sha256':hashlib.sha256(license_response.content).hexdigest(),'model_version':'2.5','synthetic_pretraining':True,'purpose':'evaluación local experimental; sin entrega comercial ni activación','parameters':{'device':'cpu','n_estimators':8,'random_state':2026,'n_preprocessing_jobs':1,'fit_mode':'fit_preprocessors'},'sources':['https://huggingface.co/Prior-Labs/tabpfn_2_5','https://arxiv.org/abs/2511.08667']}
(root/'manifest.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print({'checkpoint_sha256':digest,'bytes':info['bytes'],'revision':meta['sha']},flush=True)
