from dataclasses import asdict
from .common import ROOT,read,save,digest,now
from .modeling import catalog

def input_hashes():
    roots=[ROOT/'src',ROOT/'scripts',ROOT/'tests',ROOT/'data',ROOT/'controls']
    paths=[]
    for root in roots:
        paths.extend(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pending','.log'])
    paths.extend(ROOT/'registry'/name for name in ['schemes.csv','scheme-validation.json','population-check.json',
      'spectral-audit.json','soil-admission.json','agronomic-metadata-audit.json','table-check.json','catalog.json'])
    paths.append(ROOT/'requirements.lock')
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}

def write_catalog():
    available=['R']
    if read(ROOT/'registry/spectral-audit.json')['S_admitted']: available.append('S')
    if read(ROOT/'registry/soil-admission.json')['G_admitted']: available.append('G')
    variants,omitted,subsets=catalog(available)
    save(ROOT/'registry/catalog.json',{'available_blocks':available,'controls':{'W00':{'routes':['official','selected'],'new_training':False}},'variants':{k:[asdict(r) for r in v] for k,v in variants.items()},
       'omitted':omitted,'declared_subsets':subsets,'common_count':sum(map(len,variants.values())),
       'W05_count':len(variants['W05']),'common_max':84,'W05_max':42})
    return read(ROOT/'registry/catalog.json')

def freeze():
    target=ROOT/'registry/frozen-protocol.json'
    if target.exists(): raise ValueError('Protocolo ya congelado; no sobrescribir')
    write_catalog()
    assert not any((ROOT/'runs').glob('*/model.joblib'))
    save(target,{'at':now(),'catalog':read(ROOT/'registry/catalog.json'),'hashes':input_hashes(),
      'cutoff':'2025-10-31','seed':2026,'memory_mb':4096,'seconds_per_block':7200,'atol':1e-10,'rtol':0,
      'source_hashes':read(ROOT/'registry/copy-origins.json'),'training_started':False})
    return read(target)

def protocol():
    record=read(ROOT/'registry/frozen-protocol.json')
    actual=input_hashes()
    if actual!=record['hashes']: raise ValueError('Entradas/código del protocolo congelado alterados')
    return record

def state(run):
    p=ROOT/f'runs/{run}/run.json'
    return read(p) if p.exists() else {'status':'planned'}

def transition(run,status,**kwargs):
    old=state(run)['status']
    allowed={'planned':['running','not_viable'],'running':['completed','failed','interrupted']}
    if status not in allowed.get(old,[]): raise ValueError(f'Transición no permitida: {old} -> {status}')
    obj={**state(run),**kwargs,'id':run,'status':status,'at':now(),'activated':False,'deployed':False,'sent':False}
    save(ROOT/f'runs/{run}/run.json',obj)
    event={'run':run,'previous':old,'status':status,'at':obj['at']}
    p=ROOT/'registry/events.jsonl'
    import json
    with p.open('a',encoding='utf-8') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
