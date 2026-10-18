"""Conservar antecedentes y publicar admisión v2 sin certificar metadatos ausentes."""
import shutil
from cimmyt.common import ROOT, read, save, digest, now
from cimmyt.spatial import PROTOCOL

history=ROOT/'registry/history'; history.mkdir(exist_ok=True)
for name in ['blocker.json','label-audit.json','session-progress.json']:
    source=ROOT/'registry'/name; old=history/('v1-'+name)
    if not old.exists(): shutil.copy2(source,old)
    if name=='label-audit.json': assert digest(source)==digest(old)
audit=read(ROOT/'registry/label-audit.json')
spatial=read(ROOT/'registry/spatial-admission.json')
features=read(ROOT/'registry/common-features.json')
assert features['complete'] and spatial['protocol']==PROTOCOL
report={**audit,'status':'completed_diagnostic_admission_with_explicit_spatial_assumption',
    'spatial_protocol':PROTOCOL,'admitted_training_labels':features['auxiliary_count'],
    'principal_spatial_support':spatial['principal_summary'],
    'coordinate_metadata':{**audit['coordinate_metadata'],'status':'unknown_metadata_retained_analysis_assumption_authorized',
        'source_crs':'unknown','analysis_crs':'EPSG:4326','crs_basis':'explicit_assumption',
        'point_semantics':'unknown','measured_precision':'unknown','polygon_vertices_in_download':False,
        'principal_margin_degrees':.01,'principal_buffer_m':2000,'spatial_separation_certified':False},
    'geographic_sensitivity':spatial['geographic_sensitivity'],
    'antecedent':{'path':'registry/history/v1-label-audit.json','sha256':digest(history/'v1-label-audit.json')},
    'spatial_sha256':digest(ROOT/'registry/spatial-admission.json'),
    'climate_sha256':digest(ROOT/'registry/climate-acquisition.json'),'at':now()}
save(ROOT/'registry/label-audit-v2.json',report)
sources=read(ROOT/'registry/sources.json')
sources['evidence'].update(C06='https://github.com/gmonpr/Historical-Agronomic-Dataset/tree/bcc359c2323284def49521dbb5d4fe8538350ae2',
    C07=['https://www.cimmyt.org/es/noticias/e-agrology-una-herramienta-que-cruza-fronteras/',
        'https://www.cimmyt.org/es/noticias/las-tic-y-el-aumento-de-la-produccion-de-maiz-de-manera-sustentable-en-guerrero/'])
sources['geographic_search']={'at':'2026-10-09','sources':['C01','C02','C06','C07'],
    'findings':'Approximate locations documented; datum, point derivation and effective point precision not resolved in reviewed sources',
    'authors_revision':'bcc359c2323284def49521dbb5d4fe8538350ae2','standardization_lines':568,
    'geography_keyword_matches':0,'reference_18':'yield measurement guide; not geographic API documentation',
    'negative_search_scope_limited':True,'implementation_authorized_by_user':'Aplicar el protocolo revisado'}
sources['audited_barley_records']=audit['downloaded_barley_rows']
sources['admitted_labels_principal_population']=features['auxiliary_count']
save(ROOT/'registry/sources.json',sources)
save(ROOT/'registry/blocker.json',{'status':'resolved_by_authorized_protocol_revision','protocol':PROTOCOL,
    'at':now(),'antecedent':{'path':'registry/history/v1-blocker.json','sha256':digest(history/'v1-blocker.json')},
    'metadata_found':False,'spatial_assumption_implemented':True,'admitted_training_labels':features['auxiliary_count'],
    'predictive_training_completed':False,'remaining_dependencies':['selection','preflight','protocol_freeze','predictive_comparisons']})
lines=['# Auditoría CIMMYT: protocolo espacial revisado','',
    'Actualización del 9 de octubre de 2026. Los antecedentes del 8 de octubre se conservan en `registry/history/` y `docs/auditoria-cimmyt.md`.','',
    '| Etapa | Registros |','| --- | ---: |',
    '| Cebada descargada V6 (todos los productos) | 1.396 |','| Rendimientos únicos de grano antes de filtros | 1.130 |',
    '| Candidatos después de filtros agronómicos | 48 |','| Candidatos locales incluidos en los 48 | 29 |',
    f"| Población mexicana con celda única y clima completo bajo política principal | {features['auxiliary_count']} |",'',
    'La admisión por ajuste externo conserva 42–43 rendimientos mexicanos; los ajustes internos conservan 40–43. Se mantienen los mínimos de 30 etiquetas, diez grupos y dos campañas. La cohorte local y A04 siguen no viables.','',
    'La revisión permite puntos aproximados con WGS84 asumido, caja ±0,01° y buffer de 2.000 m. El origen de la referencia, semántica del punto y precisión permanecen desconocidos. No se reconstruyen polígonos reales ni se certifica independencia espacial.','',
    'La distancia usa un límite inferior: separación entre cajas cartesianas ECEF que contienen toda la caja auxiliar y la envolvente oficial, menor o igual a la cuerda y a la distancia superficial. Puede excluir de más; evita usar distancias angulares o medir únicamente el centro.','',
    f"La sensibilidad de admisión es **{spatial['geographic_sensitivity']}**: {spatial['changed_fit_populations']} poblaciones cambian entre las políticas estrecha, principal y amplia. Las alternativas no consultan clima ni entrenan modelos. No es una comprobación de sensibilidad predictiva.",'',
    'Se verificaron 13 pares celda/año históricos y se reutilizaron las cuatro respuestas originales 2025 sin cambiarlas. Las 197 filas oficiales y 45 auxiliares tienen las mismas 14 características, completas.','',
    'Modalidad y humedad oficial desconocidas; método externo de medición heterogéneo sin identificación por fila. El área auxiliar procede del tratamiento registrado en ha y el área oficial de los polígonos verificados.','',
    'Estado: auditoría de admisión completada; A01–A03 todavía pendientes. No hay mejora predictiva medida ni activación.','',
    'Fuentes: [catálogo CIMMYT](https://hdl.handle.net/11529/10548986), [descriptor](https://www.nature.com/articles/s41597-025-06143-w), [código de autores](https://github.com/gmonpr/Historical-Agronomic-Dataset/tree/bcc359c2323284def49521dbb5d4fe8538350ae2), [e-Agrology](https://www.cimmyt.org/es/noticias/e-agrology-una-herramienta-que-cruza-fronteras/), [NASA POWER](https://power.larc.nasa.gov/docs/methodology/data/sources/).','',
    'Los datos y contextos se conservan localmente bajo los términos de CIMMYT; no se redistribuyen los originales.']
(ROOT/'docs/auditoria-cimmyt-v2.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Antecedentes preservados; auditoría v2 publicada y bloqueo espacial resuelto')
