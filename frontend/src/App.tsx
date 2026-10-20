import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, animate, motion, useReducedMotion } from 'motion/react'
import { ArrowDown, ArrowDownToLine, ArrowUpRight, Check, ChevronDown, CircleHelp, FlaskConical, Globe2, Leaf, Search, Sprout, Waves, X } from 'lucide-react'
import ParcelMap from './ParcelMap'
import type { Curve, Model, Parcel } from './types'
import { format } from './types'

const EvolutionChart = lazy(() => import('./Charts').then(m => ({ default: m.EvolutionChart })))
const ValidationChart = lazy(() => import('./Charts').then(m => ({ default: m.ValidationChart })))
type Page = 'explorar' | 'modelo' | 'fuentes'
const navigation: { id: Page; label: string }[] = [{ id: 'explorar', label: 'Explorar parcelas' }, { id: 'modelo', label: 'Modelo y validación' }, { id: 'fuentes', label: 'Fuentes y metodología' }]

function Reveal({ text }: { text: string }) {
  const reduced = useReducedMotion()
  return <span aria-label={text}>{text.split(' ').map((word, i) => <motion.span aria-hidden="true" key={i} className="reveal-word" initial={{ opacity: reduced ? 1 : .15, y: reduced ? 0 : 5 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: reduced ? 0 : .4, delay: reduced ? 0 : Math.min(i * .035, .65) }}>{word}{' '}</motion.span>)}</span>
}

function Count({ value, digits = 2 }: { value: number; digits?: number }) {
  const ref = useRef<HTMLSpanElement>(null)
  const reduced = useReducedMotion()
  useEffect(() => {
    if (reduced || !ref.current) return
    const controls = animate(0, value, { duration: .8, ease: 'easeOut', onUpdate: v => { if (ref.current) ref.current.textContent = format(v, digits) } })
    return () => controls.stop()
  }, [value, digits, reduced])
  return <><span aria-hidden="true" ref={ref}>{format(value, digits)}</span><span className="sr-only">{format(value, digits)}</span></>
}

async function json<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal })
  if (!response.ok || !response.headers.get('content-type')?.includes('json')) throw new Error('No se pudieron leer los datos verificados.')
  return response.json() as Promise<T>
}

function ParcelResults({ parcel, model, onValidation }: { parcel: Parcel; model: Model; onValidation: () => void }) {
  const [tab, setTab] = useState<'evolution' | 'factors'>('evolution')
  const [curves, setCurves] = useState<Curve[] | null>(null)
  const [sensor, setSensor] = useState('Sentinel-2')
  const [error, setError] = useState(false)
  const [retry, setRetry] = useState(0)
  const reduced = useReducedMotion()
  useEffect(() => {
    const controller = new AbortController()
    setError(false); setCurves(null)
    json<Curve[]>(`/data/curves/${parcel.id}.json`, controller.signal).then(result => {
      setCurves(result)
      setSensor(result.find(c => c.points.some(p => p.value !== null))?.sensor ?? 'Sentinel-2')
    }).catch(e => { if (e.name !== 'AbortError') setError(true) })
    return () => controller.abort()
  }, [parcel.id, retry])
  const curve = curves?.find(c => c.sensor === sensor)
  return <motion.div className="parcel-analysis" initial={{ opacity: 0, y: reduced ? 0 : 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: reduced ? 0 : .45 }}>
    <section className="panel evidence-panel" aria-labelledby="evidence-title">
      <div className="panel-heading"><div><span className="eyebrow">SEÑALES DE {parcel.id} / {parcel.state}</span><h2 id="evidence-title">La campaña, en perspectiva.</h2></div><span className="mini-label">ABR — OCT 2025</span></div>
      <div className="evidence-tabs" aria-label="Evidencia de la parcela"><button aria-pressed={tab === 'evolution'} onClick={() => setTab('evolution')}><Waves size={16} /> Evolución del cultivo</button><button aria-pressed={tab === 'factors'} onClick={() => setTab('factors')}><FlaskConical size={16} /> Factores de la estimación</button></div>
      {tab === 'evolution' ? <>
        <div className="chart-heading"><div><strong>Actividad de la vegetación</strong><span>NDVI · índice sin unidades</span></div><label className="sensor-label"><span className="sr-only">Sensor satelital</span><select value={sensor} onChange={e => setSensor(e.target.value)}><option>Sentinel-2</option><option>Planet</option></select></label></div>
        {error ? <div className="empty-chart" role="alert">No se pudo cargar la curva.<button className="text-button" onClick={() => setRetry(v => v + 1)}>Reintentar</button></div> : !curves ? <div className="chart-skeleton" role="status">Cargando la evolución de {parcel.id}…</div> : curve ? <Suspense fallback={<div className="chart-skeleton">Preparando gráfica…</div>}><EvolutionChart key={sensor} curve={curve} /></Suspense> : <div className="empty-chart">No hay datos para este sensor.</div>}
        <div className="chart-note"><span className="legend-line" /> Curva reconstruida <span>{curve?.quality ? `${curve.quality.usable} de ${curve.quality.observations} observaciones utilizables` : 'Consulta satelital de la campaña'}</span></div>
        <p className="fineprint">{model.curveMethod.label}. La curva describe la señal satelital; no representa mediciones directas del rendimiento.</p>

      </> : <div className="factors-state"><div className="round-icon"><FlaskConical size={24} /></div><h3>Una estimación con alcance claro.</h3><p>{model.explanation.interpretation}</p><p>Las señales satelitales y la metodología están disponibles para explorar el contexto. No se presentan como una explicación causal de la estimación.</p><button className="text-button" onClick={onValidation}>Revisar cómo se evaluó el modelo <ArrowUpRight size={15} /></button></div>}
    </section>

        {curve && <section className="panel values-panel" aria-labelledby="values-title"><div className="panel-heading"><div><span className="eyebrow">LOS DATOS DE LA CAMPAÑA</span><h2 id="values-title">Consultar valores y método</h2></div><span className="mini-label">{parcel.id} · {sensor}</span></div><p>Reconstrucción Whittaker con λ=10 y filtro de nubosidad ≤20%. Los puntos se conectan sin rellenar periodos sin datos. “Con observación” indica que el intervalo temporal contiene alguna captura utilizable.</p><div className="table-scroll" tabIndex={0} role="region" aria-label="Valores de vegetación por fecha"><table><caption className="sr-only">Valores del NDVI reconstruido para {parcel.id}</caption><thead><tr><th>Fecha</th><th>NDVI</th><th>Con observación</th></tr></thead><tbody>{curve.points.map(p => <tr key={p.date}><td>{p.date}</td><td>{p.value === null ? 'Sin dato' : format(p.value, 3)}</td><td>{p.hasObservation ? 'Sí' : 'No'}</td></tr>)}</tbody></table></div></section>}
  </motion.div>
}

function ParcelEstimate({ parcel, model, onValidation, onClose }: { parcel: Parcel; model: Model; onValidation: () => void; onClose: () => void }) {
  const reduced = useReducedMotion()
  return <motion.aside className="estimate-panel" aria-labelledby="estimate-title" initial={{ opacity: 0, x: reduced ? 0 : 80 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: reduced ? 0 : 80 }} transition={{ duration: reduced ? 0 : .65, ease: [.22, 1, .36, 1], delay: reduced ? 0 : .2 }}>
      <div className="estimate-identity"><span>{parcel.id} / {parcel.state}</span><button aria-label="Cerrar detalle de parcela" onClick={onClose}><X size={20} /></button></div>
      <h1 id="estimate-title"><Reveal text="Lo que nos dice esta parcela." /></h1><div className="estimate-number"><Count value={parcel.estimate} /><span>t/ha</span></div><p className="estimate-description">Rendimiento estimado · campaña 2025</p>
      {parcel.low !== null && parcel.high !== null ? <div className="interval-card"><div><span>Intervalo nominal del {format(model.interval.nominal * 100, 0)}%</span><CircleHelp size={15} aria-hidden="true" /></div><strong>{format(parcel.low)} <span>—</span> {format(parcel.high)} <small>t/ha</small></strong><div className="interval-line"><i /><span /><i /></div><p>Calibrado con residuos fuera de pliegue, por estado.</p></div> : <p className="notice">Este artefacto no dispone de intervalo admitido.</p>}
      <dl className="parcel-facts"><div><dt>Superficie</dt><dd>{format(parcel.area)} ha</dd></div><div><dt>Producción estimada</dt><dd>{format(parcel.production)} t</dd></div><div><dt>Rendimiento observado</dt><dd>{parcel.observed === null ? 'Etiqueta oculta' : `${format(parcel.observed)} t/ha`}</dd></div></dl>
      <details className="details"><summary>Cómo interpretar esta estimación <ChevronDown size={15} /></summary><p>{model.scope} El intervalo nominal no garantiza cobertura individual ni valida campañas futuras. Cuando hay un valor observado, la comparación de esta ficha no sustituye la evaluación fuera de pliegue.</p><button className="text-button" onClick={onValidation}>Ver validación completa <ArrowUpRight size={15} /></button></details>
      <a className="analysis-link" href="#parcel-analysis" onClick={e => { e.preventDefault(); document.getElementById('parcel-analysis')?.scrollIntoView({ behavior: reduced ? 'instant' : 'smooth', block: 'start' }) }}>Explorar la campaña <ArrowDown size={16} aria-hidden="true" /></a>
    </motion.aside>
}

function Validation({ model }: { model: Model }) {
  return <section className="page-section"><div className="section-intro"><span className="eyebrow">MODELO Y VALIDACIÓN / EVIDENCIA</span><h1>Decisiones que se<br />sostienen en <em>datos.</em></h1><p>Una mirada al desempeño del {model.name} sobre {model.oof.length} parcelas con rendimiento conocido.</p></div>
    <div className="metric-grid"><div className="metric-panel"><span>Error absoluto medio</span><strong><Count value={model.metrics.mae} digits={3} /><small> t/ha</small></strong><p>Distancia media entre estimación y observación.</p></div><div className="metric-panel"><span>Raíz del error cuadrático medio</span><strong><Count value={model.metrics.rmse} digits={3} /><small> t/ha</small></strong><p>Da mayor peso a los errores de mayor magnitud.</p></div><div className="metric-panel"><span>Coeficiente de determinación</span><strong><Count value={model.metrics.r2} digits={3} /><small> R²</small></strong><p>Capacidad de explicar la variación observada.</p></div></div>
    <div className="validation-grid"><section className="panel"><span className="eyebrow">138 PARCELAS / FUERA DE PLIEGUE</span><h2>Observado frente a estimado</h2><div className="chart-note">La línea diagonal indica coincidencia exacta.</div><Suspense fallback={<div className="chart-skeleton">Preparando comparación…</div>}><ValidationChart model={model} /></Suspense><div className="scatter-legend">{['Hidalgo', 'Puebla', 'Tlaxcala'].map((s, i) => <span key={s}><i className={`legend-dot state-${i}`} />{s}</span>)}</div></section>
      <section className="panel"><span className="eyebrow">LECTURA DEL RESULTADO</span><h2>El método también importa.</h2><p>{model.validationScheme}. Cada estimación de validación se obtiene sin entrenar con la etiqueta de esa parcela.</p><div className="method-stat"><strong>{format(model.interval.coverage * 100, 1)}%</strong><span>cobertura empírica de los intervalos<br />Nominal: {format(model.interval.nominal * 100, 0)}%</span></div><p>Las 59 etiquetas del conjunto de predicción están ocultas. Sus estimaciones no son una validación adicional.</p><details className="details"><summary>Límites de la investigación <ChevronDown size={15} /></summary><p>{model.method} La estratificación por estado no equivale a una evaluación espacial estricta. Esta evaluación acompañó el desarrollo del modelo y no constituye un test independiente. Los resultados no garantizan generalización a nuevas regiones o campañas. La discretización de etiquetas en Tlaxcala y las diferencias entre estados también afectan la interpretación.</p></details></section></div>
    <section className="panel regional-panel"><div className="panel-heading"><div><span className="eyebrow">EL DESEMPEÑO POR TERRITORIO</span><h2>Una lectura regional</h2></div><span className="mini-label">{model.id} · t/ha</span></div><div className="table-scroll"><table><thead><tr><th>Estado</th><th>Parcelas</th><th>MAE (t/ha)</th><th>RMSE (t/ha)</th><th>R²</th></tr></thead><tbody>{Object.entries(model.byState).map(([state, metric]) => <tr key={state}><td>{state}</td><td>{model.oof.filter(p => p.state === state).length}</td><td>{format(metric.mae, 3)}</td><td>{format(metric.rmse, 3)}</td><td>{format(metric.r2, 3)}</td></tr>)}</tbody></table></div><details className="details"><summary>Consultar los 138 resultados <ChevronDown size={15} /></summary><div className="table-scroll"><table><thead><tr><th>Parcela</th><th>Estado</th><th>Observado</th><th>Estimado OOF</th></tr></thead><tbody>{model.oof.map(p => <tr key={p.id}><td>{p.id}</td><td>{p.state}</td><td>{format(p.observed)} t/ha</td><td>{format(p.estimated)} t/ha</td></tr>)}</tbody></table></div></details></section>
  </section>
}

function Sources({ model }: { model: Model }) {
  return <section className="page-section"><div className="section-intro"><span className="eyebrow">FUENTES Y METODOLOGÍA / TRAZABILIDAD</span><h1>Cada señal tiene<br /><em>un origen.</em></h1><p>Del satélite al rendimiento: datos del reto, fuentes de contexto y artefactos verificados para una consulta reproducible.</p></div>
    <div className="source-grid">{[
      { icon: Leaf, title: 'La señal del cultivo', note: 'ÓPTICA SATELITAL', text: 'Sentinel-2 y Planet aportan índices ópticos; Landsat aporta VI6T. La vista de evolución muestra NDVI reconstruido y distingue los periodos con observaciones.' },
      { icon: Waves, title: 'El contexto del terreno', note: 'CLIMA Y RELIEVE', text: 'CHIRPS y CHIRTS aportan contexto mensual. E12 incorpora clima diario de Open-Meteo y microtopografía para describir temperatura, relieve y drenaje local.' },
      { icon: Globe2, title: 'La escala regional', note: 'FUENTES EXTERNAS', text: 'E12 distingue el régimen municipal de reporte y la vecindad entre linderos. Combina señales fisiológicas y del ciclo completo de 2025 con GPR y CatBoost. NASA POWER y DGSIAP forman parte de la investigación previa.' },
    ].map(item => <article className="panel source-card" key={item.note}><div className="round-icon"><item.icon size={23} /></div><span className="eyebrow">{item.note}</span><h2>{item.title}</h2><p>{item.text}</p></article>)}</div>
    <section className="panel provenance"><div><span className="eyebrow">DEL DATO A LA EVIDENCIA</span><h2>Una consulta que se puede rastrear.</h2><p>{model.name} · señales de la campaña hasta {model.cutoff}. {model.scope}</p><p>{model.method} Contexto: {model.sources.join(', ')}. Esta interfaz consulta una exportación estática verificada de los resultados existentes. No vuelve a entrenar el modelo al seleccionar una parcela.</p><details className="details"><summary>Identificadores de integridad <ChevronDown size={15} /></summary><p>Versión {model.version} · commit de origen <code>{model.sourceCommit}</code></p><p>El contrato base conserva el corte técnico {model.artifactCutoff}; E12 incorpora señales posteriores hasta diciembre de 2025.</p>{Object.entries(model.sourceHashes).map(([key, value]) => <p key={key}><strong>{key}</strong><code>{value}</code></p>)}</details></div><div className="download-card"><Sprout size={32} /><h3>Los resultados,<br />también en tus manos.</h3><p>Descarga las 59 estimaciones del conjunto con etiquetas ocultas.</p><a className="primary-button" href="/downloads/predictions_59.csv" download><ArrowDownToLine size={17} /> Predicciones CSV</a><a className="text-button" href="/downloads/predictions_59_intervals.csv" download>Incluir intervalos <ArrowDown size={15} /></a></div></section>
  </section>
}

export default function App() {
  const [parcels, setParcels] = useState<Parcel[]>([])
  const [model, setModel] = useState<Model | null>(null)
  const [error, setError] = useState(false)
  const [page, setPage] = useState<Page>('explorar')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [state, setState] = useState('Todos')
  const [query, setQuery] = useState('')
  const [focusedSearch, setFocusedSearch] = useState(false)
  const reduced = useReducedMotion()
  useEffect(() => {
    const controller = new AbortController()
    Promise.all([json<Parcel[]>('/data/parcels.json', controller.signal), json<Model>('/data/model.json', controller.signal)]).then(([p, m]) => { setParcels(p); setModel(m) }).catch(e => { if (e.name !== 'AbortError') setError(true) })
    return () => controller.abort()
  }, [])
  useEffect(() => {
    const readHash = () => {
      const [section, id] = window.location.hash.replace('#', '').split('/')
      setPage(navigation.some(n => n.id === section) ? section as Page : 'explorar')
      setSelectedId(/^AGC_\d{3}$/.test(id ?? '') ? id : null)
    }
    readHash(); window.addEventListener('hashchange', readHash)
    return () => window.removeEventListener('hashchange', readHash)
  }, [])
  const navigate = (next: Page, id = selectedId) => { window.location.hash = `${next}${id ? `/${id}` : ''}` }
  const selected = parcels.find(p => p.id === selectedId) ?? null
  const filtered = useMemo(() => parcels.filter(p => state === 'Todos' || p.state === state), [parcels, state])
  const normalized = /^\d{1,3}$/.test(query.trim()) ? `AGC_${query.trim().padStart(3, '0')}` : query.trim().toUpperCase()
  const matches = filtered.filter(p => p.id.includes(normalized) || `${p.municipality} ${p.state}`.toUpperCase().includes(normalized))
  const select = (id: string) => { const p = parcels.find(p => p.id === id); if (p && state !== 'Todos' && state !== p.state) setState('Todos'); setQuery(''); setFocusedSearch(false); navigate('explorar', id) }
  return <>
    <a className="skip-link" href="#main-content" onClick={e => { e.preventDefault(); document.getElementById('main-content')?.focus() }}>Saltar al contenido</a>
    <header className={`site-header ${page === 'explorar' ? 'over-map' : ''}`}><a className="brand" href="#explorar" aria-label="AgroCebada, inicio"><span className="brand-icon"><Sprout size={27} strokeWidth={1.6} /></span><span>AgroCebada<small>INTELIGENCIA DEL TERRITORIO</small></span></a><form role="search" className="search-box header-search" onBlur={e => { if (!e.currentTarget.contains(e.relatedTarget)) setFocusedSearch(false) }} onSubmit={e => { e.preventDefault(); if (matches[0]) select(matches[0].id) }}><label className="sr-only" htmlFor="parcel-search">Buscar parcela por ID, municipio o estado</label><div className="search-input"><Search size={18} aria-hidden="true" /><input id="parcel-search" placeholder="Buscar parcela…" value={query} onChange={e => { setQuery(e.target.value); setFocusedSearch(true) }} onFocus={() => setFocusedSearch(true)} onKeyDown={e => { if (e.key === 'Escape') setFocusedSearch(false) }} autoComplete="off" aria-controls={query && focusedSearch ? "parcel-search-results" : undefined} />{query && <button type="button" aria-label="Limpiar búsqueda" onClick={() => setQuery('')}><X size={15} /></button>}</div>{query && focusedSearch && <div id="parcel-search-results" className="search-results"><div role="status" className="search-status">{matches.length ? `${matches.length} coincidencias` : 'No hay parcelas con estos filtros.'}</div>{matches.slice(0, 8).map(p => <button key={p.id} type="button" onClick={() => select(p.id)}><strong>{p.id}</strong><span>{p.municipality}, {p.state}</span><ArrowUpRight size={15} /></button>)}{!matches.length && <button type="button" onClick={() => { setQuery(''); setState('Todos') }}>Restablecer búsqueda y estado</button>}</div>}</form><nav aria-label="Navegación principal">{navigation.map(n => <button key={n.id} aria-current={page === n.id ? 'page' : undefined} onClick={() => navigate(n.id)}>{n.label}{page === n.id && <motion.span layoutId="nav-indicator" className="nav-indicator" transition={{ duration: reduced ? 0 : .25 }} />}</button>)}</nav></header>
    <main id="main-content" className={`main-shell ${page === 'explorar' ? 'explore-shell' : ''}`} tabIndex={-1}>
      {error ? <section className="load-state" role="alert"><CircleHelp size={32} /><h1>No se pudieron cargar los datos.</h1><p>Comprueba que la exportación del dashboard esté disponible.</p><button className="primary-button" onClick={() => window.location.reload()}>Volver a intentar</button></section> : !model || !parcels.length ? <section className="load-state" role="status"><Sprout size={36} /><p>Preparando el territorio y sus datos…</p></section> : page === 'explorar' ? <>
        <ParcelMap parcels={filtered} selected={selected} onSelect={select} onReset={() => navigate('explorar', null)}>
          {!selected && <section className="explore-intro"><div className="eyebrow"><span className="tiny-line" /> AGROCEBADA 2026 <span className="eyebrow-divider">/</span> CAMPAÑA 2025</div><h1><Reveal text="El territorio, en perspectiva." /></h1><p>Explora el campo. Sigue las señales.<br />Descubre lo que los datos tienen que contar.</p></section>}
          <div className={`territory-filter ${selected ? 'has-selection' : ''}`}><label className="sr-only" htmlFor="state-filter">Filtrar parcelas por estado</label><select id="state-filter" value={state} onChange={e => { setState(e.target.value); if (selected && e.target.value !== 'Todos' && selected.state !== e.target.value) navigate('explorar', null) }}><option value="Todos">Todos los estados</option><option>Hidalgo</option><option>Puebla</option><option>Tlaxcala</option></select><span>{filtered.length} parcelas</span></div>
          <AnimatePresence mode="wait">{selected && <ParcelEstimate key={selected.id} parcel={selected} model={model} onClose={() => navigate('explorar', null)} onValidation={() => navigate('modelo')} />}</AnimatePresence>

        </ParcelMap>
        {selected && <div id="parcel-analysis"><ParcelResults key={selected.id} parcel={selected} model={model} onValidation={() => navigate('modelo')} /></div>}
      </> : page === 'modelo' ? <Validation model={model} /> : <Sources model={model} />}
    </main><footer className={`site-footer ${page === 'explorar' && !selected ? 'is-hidden' : ''}`}><span><Sprout size={17} /> AgroCebada 2026 <span className="footer-divider">/</span> Inteligencia del territorio</span><span>Consulta retrospectiva · Campaña completa 2025</span><span><Check size={13} /> Datos verificados{model ? ` · ${model.version}` : ''}</span></footer>
  </>
}
