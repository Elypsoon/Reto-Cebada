import sys
from pathlib import Path
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
import pandas as pd
import numpy as np
from hydric.common import ROOT,ID,TARGET,SCHEMES,read,save,digest,now
from hydric.registry import protocol,state
from hydric.validation import eligibility

p=protocol();runs=['W00','W01-O','W01-E','W02','W03-M','W03-I','W04','W05']
entries={r:state(r) for r in runs};save(ROOT/'registry/summary.json',{'at':now(),'runs':entries})
complete=[r for r in runs if entries[r]['status']=='completed']
paired={};controls={'W01-O':('W00','official'),'W01-E':('W01-O','prediction'),'W02':('W01-E','prediction'),
  'W03-M':('W01-E','prediction'),'W03-I':('W03-M','prediction'),'W04':('W01-E','prediction'),'W05':('W01-E','prediction')}
for run in complete:
    if run=='W00':continue
    control,column=controls[run]
    if control not in complete:continue
    paired[run]={}
    for scheme in SCHEMES:
        a=pd.read_csv(ROOT/f'runs/{run}/oof-{scheme}.csv',float_precision='round_trip').set_index(ID).sort_index()
        b=pd.read_csv(ROOT/f'runs/{control}/oof-{scheme}.csv',float_precision='round_trip').set_index(ID).sort_index()
        assert a.index.equals(b.index) and np.array_equal(a[TARGET],b[TARGET]) and np.array_equal(a.spatial_group,b.spatial_group)
        frame=pd.DataFrame({TARGET:a[TARGET],'candidate':a.prediction,'control':b[column],
          'candidate_absolute_error':abs(a.prediction-a[TARGET]),'control_absolute_error':abs(b[column]-b[TARGET])})
        frame['absolute_error_difference']=frame.candidate_absolute_error-frame.control_absolute_error
        frame.to_csv(ROOT/f'docs/paired-{run}-{scheme}.csv',float_format='%.17g')
        paired[run][scheme]={'control':control,'n':len(frame),'mean_absolute_error_difference':float(frame.absolute_error_difference.mean())}
save(ROOT/'registry/paired-comparisons.json',paired)
if 'W05' in complete and 'W00' in complete:
    frames={s:pd.read_csv(ROOT/f'runs/W05/oof-{s}.csv',float_precision='round_trip') for s in SCHEMES}
    active={s:pd.read_csv(ROOT/f'runs/W00/oof-{s}.csv',float_precision='round_trip') for s in SCHEMES}
    contract=read(ROOT/'runs/W05/contract.json')
    decision=eligibility(frames,active,contract['new_block_admitted'],read(ROOT/'runs/W05/fresh-process-check.json')['passed'],read(ROOT/'runs/W00/fresh-process-check.json')['passed'])
    save(ROOT/'registry/W05-eligibility.json',decision)
else:decision={'eligible':False,'reason':'Comparaciones requeridas pendientes'}
lines=['# Resultados de disponibilidad hídrica y estrés agroclimático','',
  'Estimación retrospectiva de abril–octubre de 2025. Las comparaciones reutilizan 138 etiquetas; las 59 consultas ocultas no tienen rendimiento conocido.','',
  '| Ejecución | Estado | RMSE principal | RMSE balanceado | RMSE rotado |','| --- | --- | ---: | ---: | ---: |']
for run in runs:
    entry=entries[run];values=[]
    for scheme in SCHEMES:
        if entry['status']=='completed':
            metrics=entry['metrics'][scheme]
            values.append(f"{metrics['selected' if run=='W00' else 'prediction']['rmse']:.6f}")
        else:values.append('—')
    lines.append(f"| {run} | {entry['status']} | {' | '.join(values)} |")
lines+=['','RMSE en t/ha; menor es mejor. W00 muestra su ruta seleccionada; ambas rutas históricas se conservaron y recuperaron.',
  '',f"Elegibilidad W05: **{'sí' if decision['eligible'] else 'no'}**. Activación, despliegue y envío permanecen en falso.",
  '', 'La cartografía de suelo G quedó no viable por integridad insuficiente del recorte/servicio; el intento y sus metadatos se conservan en la auditoría. Esto no prueba que el suelo carezca de utilidad predictiva.',
  'El bloque S quedó excluido porque los originales no especifican fórmula/bandas del NDWI. Las funciones fueron probadas con datos sintéticos, sin atribuirles métricas de estrés vegetal observado.',
  'Variedad, fecha de siembra y heladas locales permanecen desconocidas en los IDs oficiales. La radiación representa contexto regional y la nubosidad de captura representa soporte observacional.',
  '', 'La receta común cambia familias/selección respecto a la activa. Los pares W04–W01-E y W05–W01-E aíslan mejor el aporte nuevo que una comparación única con W00. Los CSV pareados conservan diferencias por parcela.',
  '', 'No hay intervalos nuevos para W05 ni validación de otra campaña. Repetir esquemas no crea 414 etiquetas independientes.',
  '', '## Fuentes y software',
  '', '- ISRIC SoilGrids: https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html y https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_02.html. Admisión local negativa documentada.',
  '- NASA POWER: https://power.larc.nasa.gov/docs/methodology/. Datos locales verificados; VPD y radiación regionales.',
  '- Habilidades Scientific Agent Skills de scikit-learn/GeoPandas, Kassis et al. (2026): https://doi.org/10.48550/arXiv.2609.00065. Versiones y fuentes comprobadas en preparación.']
(ROOT/'docs/results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Resumen actualizado;',len(complete),'ejecuciones verificadas; elegibilidad W05:',decision['eligible'])

if len(complete)==5 and all(entries[r]['status']=='not_viable' for r in ['W02','W03-M','W03-I']):
    protected=read(ROOT/'registry/protected-files.json')
    changed=[path for path,expected in protected.items() if not Path(path).is_file() or digest(path)!=expected]
    assert not changed
    for run in complete:
        assert read(ROOT/f'runs/{run}/fresh-process-check.json')['passed']
        if run!='W00':
            package=read(ROOT/f'runs/{run}/recovery-package.json')
            for name,expected in package['artifacts'].items(): assert digest(ROOT/f'runs/{run}/{name}')==expected
    save(ROOT/'registry/final-integrity.json',{'at':now(),'passed':True,'protected_files':len(protected),
      'changed_files':changed,'completed_runs':complete,'nonviable_runs':['W02','W03-M','W03-I'],'protocol_valid':True,
      'hidden_queries':59,'labeled':138,'total':197,'activated':False,'deployed':False,'sent':False})
