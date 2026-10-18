from pathlib import Path
from .common import ROOT,SCHEMES,save,read,digest,now,runtime
from .modeling import catalog
from dataclasses import asdict


def input_hashes():
    paths=[]
    for folder in ['src','scripts','data/processed','data/external','controls']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and '.rejected-' not in p.name and not p.name.endswith(('.partial','.new')):
                paths.append(p)
    for name in ['requirements.lock','registry/schemes.csv','registry/viability.json','registry/spectral-audit.json','registry/nasa-audit.json','registry/preflight.json']:
        p=ROOT/name
        if not p.is_file():raise ValueError('Entrada previa ausente: '+name)
        paths.append(p)
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(set(paths))}


def freeze():
    target=ROOT/'registry/frozen-protocol.json'
    if target.exists():raise ValueError('Protocolo ya congelado; no sobrescribir')
    viability=read(ROOT/'registry/viability.json')
    if viability.get('pending_authorization'):raise ValueError('Auditoría pendiente de autorización')
    if not read(ROOT/'runs/F00-ACT/fresh-process-check.json')['passed']:raise ValueError('Control histórico no recuperado')
    preflight=read(ROOT/'registry/preflight.json')
    if not preflight['passed']:raise ValueError('Preflight no completado')
    code={str(p.relative_to(ROOT)):digest(p) for folder in ['src','scripts'] for p in (ROOT/folder).rglob('*.py')}
    if code!=preflight['code_hashes']:raise ValueError('Código cambió después del preflight; repetir prueba sintética')
    dependencies=runtime()
    expected=read(ROOT/'registry/preparation-receipt.json')['runtime']
    if any(dependencies.get(k)!=v for k,v in expected.items()):raise ValueError('Dependencias efectivas incompatibles con preparación')
    variants,omitted=catalog(viability['available'])
    value={'at':now(),'hashes':input_hashes(),'dependencies':dependencies,'schemes':SCHEMES,'seed':2026,'cutoff':'2025-10-31','n':197,'labeled':138,'hidden':59,
           'available':viability['available'],'variants':{k:[asdict(r) for r in v] for k,v in variants.items()},'omitted':omitted,
           'limits':{'acquisition_bytes':4*1024**3,'acquisition_seconds':2700,'run_seconds':21600,'tree_memory_bytes':6*1024**3},
           'atol':1e-10,'rtol':0,'promotion':'Solo F05; reglas completas del requisito Elegibilidad temporal exclusiva del combinado'}
    save(target,value,exclusive=True)
    for run,reason in omitted.items():transition(run,'not_viable',reason=reason)
    return value


def protocol():
    p=read(ROOT/'registry/frozen-protocol.json')
    if p['dependencies']!=runtime():raise ValueError('Dependencias de recuperación incompatibles')
    current=input_hashes()
    changed=[name for name in set(p['hashes'])|set(current) if current.get(name)!=p['hashes'].get(name)]
    if changed:raise ValueError('Entradas/protocolo alterados: '+str(changed[:5]))
    return p


def begin_attempt(run):
    """Reinicio íntegro de un parcial, preservándolo y descontando tiempo consumido."""
    protocol()
    folder=ROOT/'runs'/run;path=folder/'run.json'
    old=read(path) if path.exists() else {'status':'planned','attempt':0}
    if old['status'] not in ['planned','failed','incomplete']:
        raise ValueError('Reinicio/sobrescritura no permitido')
    consumed=sum(read(p).get('seconds',0) for p in folder.rglob('resources-*.json')) if folder.exists() else 0
    remaining=21600-consumed
    if remaining<=0:raise ValueError('Presupuesto acumulado agotado; conservar incompleta')
    attempt=old.get('attempt',0)+1
    if old['status']!='planned':
        from .common import safe
        destination=safe(folder/'partials'/f'attempt-{attempt-1}')
        destination.mkdir(parents=True,exist_ok=False)
        for item in list(folder.iterdir()):
            if item.is_file() and item.name!='run.json':safe(item).rename(destination/item.name)
    transition(run,'running',attempt=attempt,remaining_seconds=remaining,consumed_seconds=consumed)
    return remaining


def transition(run,status,**fields):
    if run not in ['F00-ACT','F00','F01','F02','F03','F04','F05']:raise ValueError('Ejecución no registrada')
    folder=ROOT/'runs'/run;path=folder/'run.json'
    previous=read(path) if path.exists() else {'status':'planned','events':[]}
    old=previous['status']
    allowed={'planned':['running','not_viable'],'running':['fitted','incomplete','failed'],'fitted':['completed','failed'],
             'incomplete':['running'],'failed':['running'],'completed':[],'not_viable':[]}
    if status not in allowed.get(old,[]):raise ValueError('Transición o sobrescritura no permitida')
    value={**previous,**fields,'status':status,'at':now()}
    value['events']=[*previous.get('events',[]),{'from':old,'to':status,'at':now()}]
    save(path,value)
    return value
