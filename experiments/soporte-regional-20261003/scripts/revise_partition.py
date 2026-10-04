"""Nueva ejecución para corregir cortes desiguales; no reutiliza IDs ni políticas."""
from pathlib import Path
import sys,shutil,numpy as np,pandas as pd,geopandas as gpd,psutil
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from agrocebada.tracking import Registry,read,atomic_json,snapshot_code
from agrocebada.common import PROCESSED,ID,TARGET,sha256
from agrocebada import robust as r

reason='Defecto de construcción geométrica detectado por tamaños, antes de comparar variantes: intraestado-3 produjo 68/35/35 y train mínimo70; se reemplaza por tres cortes iguales sobre el eje geométrico de mayor extensión, con desempate por ID; E08 y los tres esquemas históricos no cambian.'
registry=Registry(root);old=read(root/'registry/catalog.json')
assert sha256(root/'registry/catalog.json')==read(root/'registry/catalog-receipt.json')['sha256']
for filename in ['catalog.json','catalog-receipt.json','schemes.csv','scheme-validation.json']:
    shutil.copy2(root/'registry'/filename,root/'registry'/('revision-1-'+filename))
for folder in sorted((root/'runs').iterdir()):
    state=read(folder/'run.json')
    if state['status'] in ['completed','failed','skipped']:continue
    if state['status']=='running':
        assert not psutil.pid_exists(state['pid'])
        registry.transition(folder.name,'interrupted','Se conserva el proceso terminado y sus resultados parciales')
    registry.transition(folder.name,'failed',reason+' Sin modelo final; ejecución sustituida por un nuevo ID.')
master=gpd.read_parquet(PROCESSED/'parcels.parquet');labeled=master[master[TARGET].notna()].copy();blocks=pd.Series(index=labeled[ID],dtype=int)
for state,part in labeled.groupby('Estado'):blocks.loc[part[ID]]=r.canonical_groups(part,3)
extra=pd.DataFrame({ID:labeled[ID].to_numpy(),'scheme':'intraestado-3','fold':blocks.reindex(labeled[ID]).to_numpy(dtype=int)})
historical=pd.read_csv(root/'registry/revision-1-schemes.csv');historical=historical[historical.scheme.ne('intraestado-3')]
assignments=pd.concat([historical,extra],ignore_index=True);assignments.to_csv(root/'registry/schemes.csv',index=False)
validation={}
for scheme,g in assignments.groupby('scheme'):
    counts=g.fold.value_counts().sort_index();validation[scheme]={'counts':counts.to_dict(),'valid':bool(counts.min()>=15 and 138-counts.max()>=80),'minimum_train':int(138-counts.max()),'state_counts':{str(f):{'train':labeled.set_index(ID).reindex(g.loc[g.fold.ne(f),ID]).Estado.value_counts().to_dict(),'validation':labeled.set_index(ID).reindex(g.loc[g.fold.eq(f),ID]).Estado.value_counts().to_dict()} for f in counts.index}}
assert all(z['valid'] for z in validation.values());atomic_json(root/'registry/scheme-validation.json',validation)
labeled.to_crs(32614).merge(extra,on=ID,validate='one_to_one').to_parquet(root/'registry/intraestado-zones.parquet',index=False)
digest=snapshot_code(root);catalog={**old,'revision':2,'supersedes':'revision-1-catalog.json','reason':reason,'code_hash':digest,'scheme_hash':sha256(root/'registry/schemes.csv'),'experiments':[]}
for entry in old['experiments']:
    eid=entry['experiment'];rid=eid+'-v2';protocol={**read(root/'runs'/entry['run_id']/'protocol.json'),'code_hash':digest,'scheme_hash':catalog['scheme_hash'],'revision':2,'revision_reason':reason}
    if eid in ['E00','E08']:protocol['intraestado_rule']='tres cortes iguales sobre eje UTM de mayor extensión; desempate por ID; sin magnitudes de y'
    control=entry['control'] if entry['control'].startswith('H') else entry['control']+'-v2'
    folder=registry.create(eid,protocol,control=control,run_id=rid,retry_of=entry['run_id'])
    if eid=='E07' and protocol['optional_preflight']['available']:
        for key in protocol['keys']:registry.create(eid,{**protocol,'keys':[key],'optional_config':key},control='E00-v2',parent=rid,run_id=rid+'-'+key,retry_of='E07-'+key)
    catalog['experiments'].append({**entry,'run_id':rid,'control':control,'protocol_hash':sha256(folder/'protocol.json')})
atomic_json(root/'registry/catalog.json',catalog);atomic_json(root/'registry/catalog-receipt.json',{'sha256':sha256(root/'registry/catalog.json')})
atomic_json(root/'registry/partition-revision.json',{'reason':reason,'prior_catalog_hash':sha256(root/'registry/revision-1-catalog.json'),'current_catalog_hash':sha256(root/'registry/catalog.json'),'no_experiment_outcome_used':True,'historical_schemes_identical':True,'validation':validation})
r.active_intact();registry.publish();print({'revision':2,'code_hash':digest,'intraestado_counts':validation['intraestado-3']['counts']},flush=True)
