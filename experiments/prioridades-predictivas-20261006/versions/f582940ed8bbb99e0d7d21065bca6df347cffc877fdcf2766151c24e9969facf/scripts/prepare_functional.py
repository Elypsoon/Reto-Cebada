"""Coeficientes individuales; la base compartida queda pendiente para cada fold."""
import pandas as pd
from agrocebada.common import ROOT, PROCESSED, write_json
from agrocebada.priority_curves import supported_branches
from agrocebada.priority_functional import coefficient_table

master = pd.read_parquet(PROCESSED / 'parcels.parquet')
branches, _ = supported_branches(master, pd.read_parquet(PROCESSED / 'satellite.parquet'))
table, report = coefficient_table(master, branches, pd.read_parquet(PROCESSED / 'priority-covariates.parquet'))
table.to_parquet(PROCESSED / 'priority-functional-coefficients.parquet')
write_json(PROCESSED / 'priority-functional-support.json', report)
write_json(ROOT / 'registry/functional-preparation.json', {'population': len(table), 'branches': 5,
           'coefficients_per_branch': 6, 'shared_bases_fit': False, 'new_metrics': None,
           'available_individuals': {branch: sum(r['available'] for r in report if r['branch'] == branch)
                                     for branch in sorted({r['branch'] for r in report})}})
print('Coeficientes individuales preparados; ninguna PCA ajustada sobre población completa.')
