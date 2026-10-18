"""Vincula la evidencia consultada con hipótesis; no produce métricas."""
import re
from prepare_phase import PHASE, PROJECT, save, digest

DESIGN = PROJECT / 'openspec/changes/evaluacion-predictiva-prioritaria-con-evidencia/design.md'
LINK = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def main():
    text = DESIGN.read_text(encoding='utf-8')
    evidence = []
    for line in text.splitlines():
        if not re.match(r'^\| L0[1-8] \|', line):
            continue
        columns = [part.strip() for part in line.strip('|').split('|')]
        links = []
        for title, url in LINK.findall(columns[1]):
            if not url.startswith('http'):
                path = (DESIGN.parent / url).resolve()
                if not path.is_file():
                    raise ValueError(f'Evidencia local ausente: {path}')
                links.append({'title': title, 'path': str(path), 'sha256': digest(path)})
            else:
                links.append({'title': title, 'url': url})
        evidence.append({'id': columns[0], 'title_and_source': columns[1], 'sources': links,
                         'consulted_at': '2026-10-06', 'reading_scope_and_limitation': columns[2],
                         'application': columns[3], 'local_predictive_metrics': None})
    if {r['id'] for r in evidence} != {f'L{i:02d}' for i in range(1, 9)}:
        raise ValueError('Inventario L01–L08 incompleto')
    hypotheses = []
    linkage = {'P00': ['L01', 'L08'], 'P01': ['L01', 'L08'], 'P02': ['L02', 'L08'],
               'P03': ['L04', 'L05', 'L08'], 'P04': ['L03', 'L05', 'L08'],
               'P05': ['L03', 'L08'], 'P06': ['L01', 'L03', 'L04', 'L05', 'L08'],
               'P07': ['L06', 'L08'], 'P08': ['L07', 'L08']}
    for line in text.splitlines():
        if not re.match(r'^\| P0[0-8] \|', line):
            continue
        cols = [part.strip() for part in line.strip('|').split('|')]
        hypotheses.append({'id': cols[0], 'hypothesis_and_control': cols[1],
                           'families_and_representations': cols[2], 'planned_grid': cols[3],
                           'evidence_ids': linkage[cols[0]], 'status': 'pending', 'metrics': None,
                           'protocol': None, 'run_id': None, 'optional': cols[0] in ['P07', 'P08'],
                           'interpretation': 'Hipótesis de diseño; sin resultado predictivo nuevo.'})
    if len(hypotheses) != 9:
        raise ValueError('Matriz P00–P08 incompleta')
    deferred = [{'name': name, 'status': 'deferred', 'predictively_tested': False,
                 'reason': reason} for name, reason in [
        ('BART, TabM y NGBoost', 'Prioridad secundaria; no ampliar familias sobre las mismas 138 etiquetas.'),
        ('Radar e imágenes originales nuevas', 'Nueva adquisición y procesamiento fuera de esta fase.'),
        ('ERA5, SoilGrids y AlphaEarth', 'Proveedores nuevos fuera del alcance aprobado.'),
        ('Simulación completa de cultivo', 'No se observan fechas de siembra ni parámetros de cultivo suficientes.'),
        ('Pendientes estatales, kernels anisotrópicos y muchas interacciones', 'Complejidad excesiva con tres estados y 138 etiquetas.')]]
    save(PHASE / 'registry/evidence.json', {'sources': evidence, 'hypotheses': hypotheses,
         'deferred': deferred, 'design_sha256': digest(DESIGN), 'training_started': False})
    lines = ['# Evidencia y cobertura prioritaria', '',
             'Estado de preparación: no hay métricas nuevas ni entrenamiento iniciado.', '',
             'Las 138 etiquetas son evidencia de desarrollo; no constituyen otra campaña.', '',
             '| Comparación | Estado | Evidencia | Hipótesis y control |',
             '| --- | --- | --- | --- |']
    lines += [f"| {r['id']} | pendiente | {', '.join(r['evidence_ids'])} | {r['hypothesis_and_control']} |"
              for r in hypotheses]
    lines += ['', '## Fuentes', '']
    def render_source(value):
        def absolute_local(match):
            title, url = match.groups()
            return match.group(0) if url.startswith('http') else f'[{title}](<{(DESIGN.parent/url).resolve().as_posix()}>)'
        return LINK.sub(absolute_local, value)
    lines += [f"- {r['id']}: {render_source(r['title_and_source'])}. {r['reading_scope_and_limitation']}"
              for r in evidence]
    lines += ['', '## Alternativas diferidas', '']
    lines += [f"- {r['name']}: {r['reason']} No evaluada en esta fase." for r in deferred]
    (PHASE / 'docs/evidence-and-coverage.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('L01–L08 y P00–P08 registrados; todas las métricas nuevas pendientes.')


if __name__ == '__main__':
    main()
