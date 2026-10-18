"""Lectura de resultados congelados; no selecciona ni activa una nueva receta."""
from pathlib import Path
import geopandas as gpd
import pandas as pd
from cimmyt.common import ROOT,ID,TARGET,SCHEMES,read,save,digest,now
from cimmyt.selection import metric
from cimmyt.registry import Registry,artifact_manifest

registry=Registry();registry.protocol()
states={name:read(ROOT/f'runs/{name}/run.json') for name in ['A00','A01','A02','A03','A04']}
assert states['A01']['status']=='completed' and states['A02']['status']=='completed'
for name in ['A01','A02','A03']:
    if states[name]['status']=='completed':assert registry.check_closed(name)
    assert states[name]['status'] in ['completed','skipped','non_viable']
frames={};comparisons={};used={};rows=[]
for scheme in SCHEMES:
    a00=pd.read_csv(ROOT/f'runs/A00/artifacts/oof-{scheme}.csv',float_precision='round_trip').set_index(ID)
    a01=pd.read_csv(ROOT/f'runs/A01/artifacts/oof-{scheme}.csv',float_precision='round_trip').set_index(ID)
    a02=pd.read_csv(ROOT/f'runs/A02/artifacts/oof-{scheme}.csv',float_precision='round_trip').set_index(ID)
    assert set(a00.index)==set(a01.index)==set(a02.index) and len(a02)==138
    frame=a02[['Estado','AREA_HA',TARGET,'fold']].copy()
    frame['A00']=a00.loc[frame.index,'official'];frame['A01']=a01.loc[frame.index,'prediction']
    frame['A02']=a02.prediction;frame['regional_mean']=a01.loc[frame.index,'regional_mean']
    for name in ['A00','A01','regional_mean']:
        frame[f'squared_error_delta_{name}']=(frame.A02-frame[TARGET])**2-(frame[name]-frame[TARGET])**2
    frame.to_csv(ROOT/f'docs/paired-{scheme}.csv',float_format='%.17g')
    frames[scheme]=frame
    comparison={name:metric(frame[TARGET],frame[name]) for name in ['A00','A01','A02','regional_mean']}
    comparisons[scheme]=comparison
    records=read(ROOT/f'runs/A02/artifacts/folds-{scheme}.json')
    used[scheme]={'outer_fits':len(records),'donor_fits':sum(r['selection']['used_donors'] for r in records),
        'fallback_fits':sum(not r['selection']['used_donors'] for r in records),
        'support_by_fit':[{'fold':r['fold'],'chosen':r['selection']['chosen_id'],
            'donor_labels':r['contract']['donor_count'],'donor_groups':r['contract']['donor_groups'],
            'admission':r['contract']['admission'].get('support'),
            'viable_augmented_candidates':r['selection']['augmented_candidates_viable'],
            'decision':r['selection']['decision']} for r in records]}
    rows.append(f"| {scheme} | {comparison['A00']['rmse']:.6f} | {comparison['A01']['rmse']:.6f} | {comparison['A02']['rmse']:.6f} | {comparison['regional_mean']['rmse']:.6f} | {used[scheme]['donor_fits']}/{len(records)} |")

def stable(reference,require_donors=False):
    ratios={s:comparisons[s]['A02']['rmse']/comparisons[s][reference]['rmse'] for s in SCHEMES}
    state_checks=[]
    for scheme,frame in frames.items():
        for state,part in frame.groupby('Estado'):
            if len(part)<10:continue
            old=metric(part[TARGET],part[reference])['mae'];new=metric(part[TARGET],part.A02)['mae']
            state_checks.append({'scheme':scheme,'state':state,'n':len(part),'reference_mae':old,
                'candidate_mae':new,'passed':new<=old*1.1})
    checks={'principal_gain':ratios[SCHEMES[0]]<=.98,'at_least_two_schemes':sum(r<=.98 for r in ratios.values())>=2,
        'mean_ratio':sum(ratios.values())/3<=.98,'no_scheme_above_1_05':max(ratios.values())<=1.05,
        'state_mae':all(x['passed'] for x in state_checks),
        'donors_in_every_scheme':all(x['donor_fits']>0 for x in used.values()) if require_donors else True}
    return {'passed':all(checks.values()),'checks':checks,'rmse_ratios':ratios,'state_checks':state_checks}

conclusions={'label_contribution_conditioned_on_point_assumption':stable('A01',True),
    'competitiveness_against_active':stable('A00'),'comparison_against_regional_mean':stable('regional_mean')}
spatial=read(ROOT/'registry/spatial-admission.json');audit=read(ROOT/'registry/label-audit-v2.json')
aux=pd.read_parquet(ROOT/'data/processed/cimmyt-admitted.parquet')
size={'labels':len(aux),'plots':int(aux['plot'].nunique()),'known_farmers':int(aux.farmer.nunique()),
    'campaigns':int(aux.year.nunique()),'groups':int(aux.dependence_group.nunique()),
    'cells':len(aux[['cell_lon','cell_lat']].drop_duplicates())}
result={'at':now(),'protocol':'cimmyt-point-assumption-v2','comparisons':comparisons,'donor_usage':used,
    'conclusions':conclusions,'auxiliary_population':size,'geographic_sensitivity':spatial['geographic_sensitivity'],
    'development_labels':138,'hidden_unlabeled_queries':59,'independent_validation_campaign':False,
    'A03_status':states['A03']['status'],'A04_status':states['A04']['status'],
    'limits':['unknown source CRS, point semantics and effective precision',
        'spatial policy sensitivity tested only for admission, not predictive sensitivity',
        'heterogeneous external measurements; official moisture and water regime unknown',
        'technical assistance and campaign shift; auxiliary weights do not remove all domain bias'],
    'activated':False,'deployed':False,'sent':False}
save(ROOT/'docs/conclusions.json',result)
lines=['# Resultado de la ampliación de entrenamiento con CIMMYT','',
    'Estudio diagnóstico sobre las mismas 138 etiquetas oficiales de 2025. Las 59 consultas ocultas siguen sin etiquetas.','',
    f"Aporte estable de etiquetas bajo el supuesto de puntos: **{'sí' if conclusions['label_contribution_conditioned_on_point_assumption']['passed'] else 'no'}**.",
    f"Competitividad frente a la versión activa: **{'sí' if conclusions['competitiveness_against_active']['passed'] else 'no'}**.",'',
    '| Esquema | RMSE A00 activa | RMSE A01 común | RMSE A02 procedimiento ampliado | RMSE media regional | Ajustes A02 con donantes |',
    '| --- | ---: | ---: | ---: | ---: | ---: |',*rows,'',
    'RMSE en t/ha. A01 y A02 comparten columnas, algoritmo y selección interna. A02 conserva respaldos oficiales cuando no se admite ampliación; las predicciones de respaldo no se atribuyen a donantes.','',
    f"Disponibilidad: 48 candidatos agronómicos; {size['labels']} registros con celda única y clima completo, {size['plots']} parcelas, {size['known_farmers']} productores conocidos, {size['campaigns']} campañas, {size['groups']} grupos y {size['cells']} celdas meteorológicas. Por ajuste principal quedan 40–43 candidatos mexicanos. No sumar los tres esquemas como 414 etiquetas independientes.",'',
    'Los 29 candidatos locales no superan el mínimo de 30; A04 permanece no viable y no recibió métricas del experimento TabPFN anterior.','',
    f"Curva A03: **{states['A03']['status']}**. Consultar `runs/A03/artifacts/curve-status.json` para las fracciones 25/50/100%, soportes e inviabilidades. El 100% reutiliza A02; no se elige retrospectivamente el tamaño más favorable.",'',
    f"Sensibilidad geográfica de admisión: **{spatial['geographic_sensitivity']}**, con {spatial['changed_fit_populations']} poblaciones distintas entre márgenes examinados. WGS84 es un supuesto; datum de origen, semántica del punto y precisión efectiva no están verificados. La política principal usa ±0,01° y 2.000 m. La separación ECEF es un límite inferior conservador, no la distancia exacta ni una garantía de separación parcelaria.",'',
    'Las diferencias pareadas por parcela se conservan en los tres CSV de `docs/paired-*`. Las métricas RMSE, MAE, R², sesgo, estado, fold y tercil de área, y las decisiones internas completas se conservan por ejecución. `conclusions.json` contiene cada comprobación de los umbrales congelados, sin significación estadística inferida de errores correlacionados.','',
    'Recuperación: cada comparación completada reprodujo modelos, pesos, contextos, contratos, predicciones y métricas en otro proceso sin red, con tolerancia absoluta 1e−10 y relativa 0. El protocolo y sus entradas quedaron congelados antes del primer ajuste real.','',
    'Las métricas describen evidencia de desarrollo, no validación independiente en otra campaña. El sesgo de asistencia técnica, cambio temporal, medición externa heterogénea y modalidad/humedad oficial desconocidas limitan la transferencia. No se activó, desplegó ni envió ningún modelo; E08/P06 conserva sus decisiones.','',
    'Más registros compatibles pueden seguir siendo útiles, pero esta fase no prueba otras fuentes ni todas las combinaciones posibles. Cualquier ampliación de proveedores, ventanas, modelos o criterios requiere otro protocolo previo a sus resultados.','',
    'Referencias y software:','',
    '- [CIMMYT, Historical Agronomic Dataset, V6](https://hdl.handle.net/11529/10548986). Originales y contextos locales bajo sus condiciones de uso; no redistribuidos.',
    '- [Descriptor del dataset](https://www.nature.com/articles/s41597-025-06143-w) y [revisión del código de autores](https://github.com/gmonpr/Historical-Agronomic-Dataset/tree/bcc359c2323284def49521dbb5d4fe8538350ae2).',
    '- [NASA POWER: fuentes](https://power.larc.nasa.gov/docs/methodology/data/sources/) y [API diaria](https://power.larc.nasa.gov/docs/services/api/temporal/daily/).',
    '- Kassis, T., Agarwal, V., He, Y., Patel, D. y Brueckner, A. M. (2026). [Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://doi.org/10.48550/arXiv.2609.00065). Versión actual verificada el 9 de octubre de 2026; guías GeoPandas/scikit-learn empleadas en el procedimiento.']
(ROOT/'docs/conclusions.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
protected=read(ROOT/'registry/protected-files.json')
changed=[name for name,expected in protected.items() if not Path(name).is_file() or digest(name)!=expected]
save(ROOT/'registry/final-integrity.json',{'at':now(),'files_checked':len(protected),'passed':not changed,'changed_files':changed})
if changed:raise ValueError('Archivos protegidos alterados; no cerrar cobertura')
save(ROOT/'runs/A00/artifact-manifest.json',artifact_manifest(ROOT/'runs/A00/artifacts'))
save(ROOT/'runs/A04/artifact-manifest.json',artifact_manifest(ROOT/'runs/A04/artifacts'))
save(ROOT/'registry/coverage-v2.json',{'at':now(),'protocol':'cimmyt-point-assumption-v2',
    'runs':{name:{'status':state['status'],'verified':state.get('verified',False),
        'predictively_tested':state.get('predictively_tested',state.get('historical_control',False)),
        'historical_control':state.get('historical_control',False),'metrics_present':state.get('metrics') is not None}
        for name,state in states.items()},'audit_status':audit['status'],'pending_dependencies':[],
    'protected_files_verified':len(protected),'activated':False,'deployed':False,'sent':False})
print('Conclusión:',{k:v['passed'] for k,v in conclusions.items()},'integridad:',len(protected),'archivos')
