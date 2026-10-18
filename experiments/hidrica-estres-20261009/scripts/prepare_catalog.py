import sys
from pathlib import Path
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.registry import write_catalog
record=write_catalog()
print('Catálogo efectivo:',record['common_count'],'máximo W05:',record['W05_count'],'bloques:',record['available_blocks'])
