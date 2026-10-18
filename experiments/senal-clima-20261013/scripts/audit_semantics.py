from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET
PHASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE / 'src'))
from signalclima.common import ROOT, PROJECT, save, read, digest, now
previous = read(ROOT / 'registry/previous-spectral-audit.json')
originals = []
for entry in previous['sources']:
    p = Path(entry['path'])
    if digest(p) != entry['sha256']:
        raise ValueError('Original espectral diferente del auditado; revisar evidencia')
    originals.append({'path': str(p), 'sha256': digest(p)})
doc = PROJECT / 'Reto-Cebada/DataSet/Diccionario_de_indices_satelitales.docx'
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with zipfile.ZipFile(doc) as archive:
    xml = ET.fromstring(archive.read('word/document.xml'))
paragraphs = [''.join(t.text or '' for t in q.findall('.//w:t', ns)) for q in xml.findall('.//w:p', ns)]
contexts = [paragraphs[i:i+3] for i,v in enumerate(paragraphs) if v.strip() == 'NDWI']
if contexts != [previous['definition']]:
    raise ValueError('La definición original cambió; revisar semántica antes de admitir')
save(ROOT / 'registry/spectral-audit.json', {'at': now(), 'labels_used': False, 'originals_verified': originals,
     'original_definition': contexts[0], 'formula': None, 'bands': None, 'orientation': None,
     'original_semantic_admitted': False, 'reason': 'Originales íntegros: descripción genérica sin bandas, ecuación ni código productor identificable.',
     'new_extraction_identity': 'ndmi_b8a_b11', 'new_extraction_admitted': False})
print('Original NDWI: identidad conservada; definición vegetal no comprobada')
