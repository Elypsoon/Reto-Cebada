"""Preparación por parcela sin transformaciones compartidas ni etiquetas."""
import pandas as pd
from agrocebada.common import ROOT, PROCESSED, write_json, ID
from agrocebada.priority_curves import supported_branches, common_covariates, audited_thermal_context, summary_table


def main():
    master = pd.read_parquet(PROCESSED / 'parcels.parquet')
    branches, quality = supported_branches(master, pd.read_parquet(PROCESSED / 'satellite.parquet'))
    covariates = common_covariates(pd.read_parquet(PROCESSED / 'features_monthly_20_10.parquet'), quality)
    quality.to_parquet(PROCESSED / 'priority-quality.parquet')
    covariates.to_parquet(PROCESSED / 'priority-covariates.parquet')
    calendar, diagnostics = summary_table(master, branches, covariates)
    calendar.to_parquet(PROCESSED / 'features_priority_calendar.parquet')
    write_json(PROCESSED / 'priority-calendar-support.json', diagnostics)
    axes, total, audit = audited_thermal_context(master)
    enriched = covariates.join(total, validate='one_to_one')
    thermal, diagnostics = summary_table(master, branches, enriched, axes)
    thermal.to_parquet(PROCESSED / 'features_priority_thermal.parquet')
    calendar.join(total, validate='one_to_one').to_parquet(PROCESSED / 'features_priority_calendar_nasa.parquet')
    write_json(PROCESSED / 'priority-thermal-support.json', diagnostics)
    write_json(PROCESSED / 'priority-thermal-audit.json', audit)
    write_json(ROOT / 'registry/curve-preparation.json', {'population': len(master), 'branches': 5,
         'source': 'Observaciones oficiales y respuestas NASA locales auditadas.',
         'learned_shared_transformations': False, 'new_predictive_metrics': None})
    print('Cinco ramas, calidad compartida y ejes calendario/térmico preparados sin etiquetas.')


if __name__ == '__main__':
    main()
