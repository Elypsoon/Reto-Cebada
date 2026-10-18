"""Registro local verificable con estados, eventos y comparaciones pareadas."""
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import json
import os
import shutil
import uuid
import numpy as np
import pandas as pd
from .common import ID,TARGET,SEED,CUTOFF,sha256,dependencies,code_hash

LIMITATION='Desarrollo sobre las mismas 138 etiquetas; sin campaña nueva ni evaluación oficial.'

def now():return datetime.now(timezone.utc).isoformat()
def default(value):
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,Path):return str(value)
    raise TypeError(type(value).__name__)
def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=default),encoding='utf-8');os.replace(temp,path)
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def manifest(root):
    root=Path(root)
    return {p.relative_to(root).as_posix():sha256(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.tmp')}
def check_manifest(root,values):
    return all((Path(root)/name).is_file() and sha256(Path(root)/name)==digest for name,digest in values.items())

def compare_frames(candidate,control,column='selected'):
    required=[ID,TARGET,'spatial_group']
    for frame in [candidate,control]:
        if len(frame)!=138 or not frame[ID].is_unique or not np.isfinite(frame[TARGET]).all():raise ValueError('Población no comparable')
    a=candidate.set_index(ID).sort_index();b=control.set_index(ID).sort_index()
    if not a.index.equals(b.index) or not np.array_equal(a[TARGET],b[TARGET]) or not np.array_equal(a.spatial_group,b.spatial_group) or not np.array_equal(a.Estado,b.Estado):raise ValueError('Identificadores, etiquetas, estados o folds incompatibles')
    if not np.isfinite(a[column]).all() or not np.isfinite(b[column]).all():raise ValueError('OOF incompleta')
    result=a[[TARGET,'Estado','spatial_group']].copy();result['candidate']=a[column];result['control']=b[column]
    result['squared_error_delta']=(a[column]-a[TARGET])**2-(b[column]-b[TARGET])**2
    result['absolute_error_delta']=abs(a[column]-a[TARGET])-abs(b[column]-b[TARGET]);return result.reset_index()

class Registry:
    def __init__(self,root):
        self.root=Path(root);self.folder=self.root/'registry';self.folder.mkdir(parents=True,exist_ok=True);(self.root/'runs').mkdir(exist_ok=True)
    @contextmanager
    def lock(self):
        path=self.folder/'writer.lock'
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        try:
            os.write(fd,str(os.getpid()).encode());os.close(fd);yield
        finally:
            if path.exists():path.unlink()
    def event(self,run_id,state,reason=None):
        path=self.folder/'events.jsonl';existing=path.read_text(encoding='utf-8').splitlines() if path.exists() else []
        # An interrupted trailing write is preserved, then recovered explicitly.
        parsed=[]
        for i,line in enumerate(existing):
            try:parsed.append(json.loads(line))
            except json.JSONDecodeError:
                if i!=len(existing)-1:raise ValueError('Historial corrupto')
                shutil.copy2(path,self.folder/f'events-interrupted-{uuid.uuid4().hex}.jsonl')
                path.write_text('\n'.join(existing[:i])+('\n' if i else ''),encoding='utf-8')
                parsed.append({'sequence':len(parsed)+1,'run_id':run_id,'state':'recovered','at':now(),'reason':'Se conserva y recupera la línea interrumpida'})
                with path.open('a',encoding='utf-8') as f:f.write(json.dumps(parsed[-1],ensure_ascii=False)+'\n')
        row={'sequence':len(parsed)+1,'run_id':run_id,'state':state,'at':now(),'reason':reason}
        with path.open('a',encoding='utf-8') as f:
            f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
    def create(self,experiment,protocol,control=None,parent=None,run_id=None,retry_of=None):
        run_id=run_id or f'{experiment}-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")}-{uuid.uuid4().hex[:6]}'
        folder=self.root/'runs'/run_id
        with self.lock():
            folder.mkdir(exist_ok=False);(folder/'artifacts').mkdir()
            atomic_json(folder/'protocol.json',protocol)
            state={'schema_version':1,'phase_id':self.root.name,'experiment_id':experiment,'run_id':run_id,'control_run_id':control,'parent_run_id':parent,'retry_of':retry_of,'hypothesis':protocol.get('hypothesis'),'status':'frozen','started_at':None,'finished_at':None,'cutoff':CUTOFF,'seed':SEED,'protocol_hash':sha256(folder/'protocol.json'),'metrics':None,'verification':None,'decision':None,'limitations':[LIMITATION]}
            for field in ['data_hashes','code_hash','dependency_manifest','scheme_hash','feature_manifest']:state[field]=protocol.get(field)
            atomic_json(folder/'run.json',state);self.event(run_id,'planned');self.event(run_id,'frozen');self.publish()
        return folder
    def transition(self,run_id,status,reason=None):
        with self.lock():
            path=self.root/'runs'/run_id/'run.json';state=read(path)
            if state['status'] in ['completed','failed','skipped']:raise ValueError('Una ejecución cerrada no se modifica; crear reintento')
            if status not in ['running','failed','interrupted','skipped']:raise ValueError('Transición no permitida')
            state.update(status=status,reason=reason)
            if status=='running':
                self.validate_protocol(run_id);state['started_at']=state['started_at'] or now();state['pid']=os.getpid()
            else:state['finished_at']=now()
            if status in ['failed','skipped']:
                changes={'model_absent':not (path.parent/'artifacts/model_official.joblib').exists(),'reason':reason,'procedure':read(path.parent/'protocol.json')}
                atomic_json(path.parent/'changes.json',changes);state['changes']=changes
                atomic_json(path.parent/'artifact-manifest.json',manifest(path.parent/'artifacts'));state['artifact_manifest']=sha256(path.parent/'artifact-manifest.json')
            atomic_json(path,state);self.event(run_id,status,reason);self.publish()
    def validate_protocol(self,run_id,expected=None):
        folder=self.root/'runs'/run_id;state=read(folder/'run.json')
        if sha256(folder/'protocol.json')!=state['protocol_hash']:raise ValueError('Protocolo alterado')
        p=read(folder/'protocol.json')
        if expected is not None and p!=expected:raise ValueError('Checkpoint incompatible')
        if p.get('code_hash') and p['code_hash']!=code_hash():raise ValueError('Código alterado después de congelar')
        for field in ['data_hashes','feature_manifest','external_manifest']:
            for name,digest in p.get(field,{}).items():
                filename=f'features_{name}.parquet' if field=='feature_manifest' else f'external_{name}.parquet' if field=='external_manifest' else name
                if sha256(self.root/'data/processed'/filename)!=digest:raise ValueError('Datos alterados después de congelar')
        if p.get('scheme_hash') and sha256(self.folder/'schemes.csv')!=p['scheme_hash']:raise ValueError('Particiones alteradas')
        if p.get('dependency_manifest') and dependencies()!=p['dependency_manifest']:raise ValueError('Dependencias incompatibles')
        return p
    def recover(self,run_id,expected):
        self.validate_protocol(run_id,expected)
        folder=self.root/'runs'/run_id;state=read(folder/'run.json')
        if state['status'] not in ['running','interrupted']:raise ValueError('No es una ejecución reanudable')
        checkpoint=folder/'artifacts/checkpoint.json'
        if not checkpoint.exists() or not check_manifest(folder/'artifacts',read(checkpoint)['manifest']):raise ValueError('Checkpoint no verificable')
        if read(checkpoint).get('protocol_hash')!=read(folder/'run.json')['protocol_hash']:raise ValueError('Checkpoint de otra política')
        self.transition(run_id,'interrupted','Recuperación explícita de proceso anterior')
        self.transition(run_id,'running','Checkpoint y protocolo verificados')
    def finish(self,run_id,metrics,verification,changes,decision):
        folder=self.root/'runs'/run_id
        with self.lock():
            state=read(folder/'run.json')
            if state['status']!='running':raise ValueError('Solo se completa una ejecución en marcha')
            self.validate_protocol(run_id)
            if not verification.get('passed'):raise ValueError('Verificaciones incompletas')
            atomic_json(folder/'changes.json',changes);atomic_json(folder/'artifacts/metrics.json',metrics);atomic_json(folder/'artifacts/verification.json',verification)
            atomic_json(folder/'artifact-manifest.json',manifest(folder/'artifacts'))
            if not check_manifest(folder/'artifacts',read(folder/'artifact-manifest.json')):raise ValueError('Artefactos incompatibles')
            state.update(status='completed',finished_at=now(),metrics=metrics,verification=verification,changes=changes,decision=decision,artifact_manifest=sha256(folder/'artifact-manifest.json'))
            atomic_json(folder/'run.json',state);self.event(run_id,'completed',decision.get('reason'));self.publish()
    def revise_interpretation(self,run_id,text,supersedes=None):
        with self.lock():
            folder=self.root/'runs'/run_id/'interpretations';folder.mkdir(exist_ok=True)
            if supersedes is not None and not (folder/f'{supersedes}.json').exists():raise ValueError('Revisión anterior inexistente')
            revision=uuid.uuid4().hex
            atomic_json(folder/f'{revision}.json',{'revision':revision,'supersedes':supersedes,'at':now(),'text':text})
            self.event(run_id,'interpretation_revision',revision);return revision
    def import_history(self,experiment,metrics,origin):
        folder=self.create(experiment,{'hypothesis':'Antecedente verificado','origin':origin},run_id=experiment)
        state=read(folder/'run.json');state.update(status='completed',origin='historical',imported_at=now(),metrics=metrics,verification={'passed':True,'kind':'source_hashes'},decision={'activated':experiment=='H00-vigente','eligible':False,'reason':'Antecedente; no resultado nuevo'},finished_at=now())
        atomic_json(folder/'run.json',state);self.event(experiment,'imported','Antecedente con procedencia');self.publish()
    def publish(self):
        rows=[]
        for folder in sorted((self.root/'runs').iterdir()):
            if not (folder/'run.json').exists():continue
            state=read(folder/'run.json');status=state['status']
            if status in ['completed','failed','skipped'] and state.get('origin')!='historical':
                if not check_manifest(folder/'artifacts',read(folder/'artifact-manifest.json')):status='integrity_error'
            metrics=state.get('metrics') or {}
            if not metrics:rows.append({'run_id':folder.name,'experiment':state['experiment_id'],'status':status,'route':None,'scheme':None,'rmse':None,'mae':None,'bias':None,'control_delta_rmse':None,'reason':state.get('reason')})
            for route,schemes in metrics.items():
                for scheme,values in schemes.items():rows.append({'run_id':folder.name,'experiment':state['experiment_id'],'status':status,'route':route,'scheme':scheme,**values})
        frame=pd.DataFrame(rows)
        temp=self.folder/'summary.csv.tmp';frame.to_csv(temp,index=False);os.replace(temp,self.folder/'summary.csv')
        docs=self.root/'docs';docs.mkdir(exist_ok=True)
        lines=['# Historial de experimentos','',LIMITATION,'','Horarios de presentación: America/Mexico_City; marcas del registro en UTC.','', '| experimento | estado | ruta | esquema | RMSE | MAE | sesgo | cambio RMSE | ejecución |','| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        def fmt(v):return 'pendiente' if pd.isna(v) else f'{v:.6f}' if isinstance(v,(float,np.floating)) else str(v)
        for row in rows:
            cells=[row.get(k) for k in ['experiment','status','route','scheme','rmse','mae','bias','control_delta_rmse']]
            lines.append('| '+' | '.join(fmt(v) for v in cells)+f" | [{row['run_id']}](../runs/{row['run_id']}/run.json) |")
        lines+=['','Los resultados negativos y omitidos permanecen registrados. Elegibilidad y activación se consultan por ejecución.','', '## Recursos metodológicos','', '- scikit-learn: ajuste de transformaciones dentro de cada entrenamiento y validación por grupos.', '- GeoPandas: geometría oficial, distancias entre polígonos en UTM 14N y uniones verificadas.', '- [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), Kassis et al., 2026: procedimientos de scikit-learn y GeoPandas consultados para esta implementación.', '- Referencias primarias: https://scikit-learn.org/stable/modules/gaussian_process.html y https://arxiv.org/abs/2511.08667.']
        temp=docs/'experiment-history.md.tmp';temp.write_text('\n'.join(lines)+'\n',encoding='utf-8');os.replace(temp,docs/'experiment-history.md')

def snapshot_code(root):
    root=Path(root);digest=code_hash();destination=root/'versions'/digest
    if not destination.exists():
        shutil.copytree(root/'src',destination/'src',ignore=shutil.ignore_patterns('__pycache__'))
        for name in ['requirements.lock','pyproject.toml']:shutil.copy2(root/name,destination/name)
        atomic_json(destination/'manifest.json',manifest(destination))
    elif not check_manifest(destination,read(destination/'manifest.json')):raise ValueError('Versión de código alterada')
    return digest
