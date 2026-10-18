"""Perfil de columnas reales y conteos; evita publicar datos demográficos."""
import json
from pathlib import Path
import openpyxl
import pandas as pd
from cimmyt.common import ROOT, save
from cimmyt.acquisition import FILES

raw = ROOT / 'data/raw'
inventory = {}
tables = {}
for filename, header_row in [(FILES[0], 2), (FILES[1], 1), (FILES[2], 1)]:
    workbook = openpyxl.load_workbook(raw / filename, read_only=True, data_only=True)
    sheet = workbook.worksheets[0]
    iterator = sheet.iter_rows(min_row=header_row, values_only=True)
    header = [str(v).strip() for v in next(iterator)]
    counts = {}
    columns = []
    for value in header:
        counts[value] = counts.get(value, 0) + 1
        columns.append(value if counts[value] == 1 else value + f'__{counts[value]}')
    rows, total, duplicate_logbooks_equal = [], 0, True
    if filename == FILES[0]:
        wanted = [0, 1, 12, 13, 14, 15, 16, 17, 18, 21, 22, 34, 35, 36, 37, 38, 49, 50]
    elif filename == FILES[1]:
        wanted = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 26, 42, 43, 44, 45, 46, 47, 48, 49, 50]
    else:
        wanted = [0, 1]
    for row in iterator:
        if all(value is None for value in row):
            continue
        total += 1
        if filename == FILES[0] and row[0] != row[34]:
            duplicate_logbooks_equal = False
        if filename != FILES[1] or str(row[15]).strip().upper() == 'BARLEY':
            rows.append([row[i] for i in wanted])
    # Las claves originales mezclan enteros y UUID; texto nullable preserva ambos.
    frame = pd.DataFrame(rows, columns=[columns[i] for i in wanted]).astype('string')
    frame.to_parquet(ROOT / 'data/processed' / ('cimmyt-farmer.parquet' if filename == FILES[0] else 'cimmyt-barley.parquet' if filename == FILES[1] else 'cimmyt-glossary.parquet'), index=False)
    inventory[filename] = {'sheet': sheet.title, 'header_row': header_row, 'columns': columns,
        'rows': total, 'retained_rows': len(frame), 'duplicated_logbook_columns_equal': duplicate_logbooks_equal}
    tables[filename] = frame
    workbook.close()
    print(filename, 'filas:', total, 'retenidas:', len(frame), flush=True)
barley = tables[FILES[1]]
profile = {}
for column in ['PRODUCT.OBTAINED', 'UNIT.OF.MEASURE/HA', 'WINTER/SUMER.\u00a0SEASON', 'HYDRIC.REGIME', 'STATE', 'YEAR', 'ACTIVITY.PERFORMED']:
    profile[column] = {str(k): int(v) for k, v in barley[column].value_counts(dropna=False).items()}
inventory['barley_profile'] = profile
inventory['farmer_keys'] = {'unique_logbook': bool(tables[FILES[0]]['LOGBOOK ID'].is_unique),
    'unique_combined': not tables[FILES[0]].duplicated(['LOGBOOK ID', 'INNOVATION/CONVENTIONAL_PRACTICES_ID']).any()}
save(ROOT / 'registry/cimmyt-schema.json', inventory)
print(json.dumps(profile, ensure_ascii=False))
