from pathlib import Path
import sys
PHASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PHASE/'src'))
from signalclima.registry import freeze
value=freeze()
print('Protocolo congelado:',len(value['hashes']),'entradas;',value['available'],'bloques viables',flush=True)
