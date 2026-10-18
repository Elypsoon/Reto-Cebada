import sys
from pathlib import Path
PHASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PHASE/'src'))
from hydric.common import ROOT,read
from hydric.registry import freeze
assert read(ROOT/'registry/resource-preflight.json')['passed']
record=freeze()
print('Protocolo congelado:',len(record['hashes']),'entradas;',record['catalog']['common_count'],'candidatos comunes efectivos')
