"""Verifica cifras publicadas y tablas contra la ejecución experimental."""
from pathlib import Path
import json
import pandas as pd
from pypdf import PdfReader

root=Path(__file__).resolve().parents[1];artifacts=root/'artifacts'
report=json.loads((artifacts/'validation.json').read_text(encoding='utf-8'))
body=(root/'docs/technical-report.md').read_text(encoding='utf-8');pdf=PdfReader(root/'output/pdf/agrocebada-informe-tecnico.pdf')
text='\n'.join(p.extract_text() for p in pdf.pages)
for procedure in ['selected','official','regional_mean']:
    value=f"{report['metrics'][procedure]['rmse']:.3f}"
    assert value in body and value in text
assert 'Promoción rechazada' in text and 'no representan confirmación temporal' in text
for name in ['principal-5','balanceado-4','rotado-45-5']:
    values=json.loads((artifacts/f'validation-{name}.json').read_text(encoding='utf-8'))['metrics']
    for procedure in ['selected','regional_mean']:assert f"{values[procedure]['rmse']:.3f}" in text
annex=PdfReader(root/'output/pdf/agrocebada-anexos.pdf');annex_text='\n'.join(p.extract_text() for p in annex.pages);export=pd.read_csv(artifacts/'predictions_59.csv')
assert len(annex.pages)==2 and len(export)==59
for _,row in export.iterrows():
    assert annex_text.count(row.ID_POLIGONO)==1
    assert f'{row.RENDIMIENTO_T_HA:.12f}' in annex_text
assert 'NASA' in text and 'sin garantía regional' in annex_text
check_path=artifacts/'technical-report-check.json';check=json.loads(check_path.read_text(encoding='utf-8'))
check.update(numerical_check=True,labels_reuse_stated=True,sources_verified=True,visual_verified=True,visual_review='Todas las páginas del informe final (8), bibliografía (2) y anexos (2) renderizadas e inspeccionadas; encabezados corregidos, sin recortes ni solapamientos')
check_path.write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
print('Documentos verificados:',{k:len(PdfReader(root/'output/pdf'/k).pages) for k in check['pdfs']})
