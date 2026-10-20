import { lazy, Suspense, useEffect, useState, type ReactNode } from 'react'
import { useReducedMotion } from 'motion/react'
import { ArrowLeft, ArrowUp, Mountain, Satellite } from 'lucide-react'
import type { Parcel } from './types'
import type { BaseMap } from './GeographicMap'

const GeographicMap = lazy(() => import('./GeographicMap'))

export default function ParcelMap({ parcels, selected, onSelect, onReset, children }: {
  parcels: Parcel[]; selected: Parcel | null; onSelect: (id: string) => void; onReset: () => void; children?: ReactNode;
}) {
  const reduced = useReducedMotion()
  const [baseMap, setBaseMap] = useState<BaseMap>('satellite')
  const [hovered, setHovered] = useState<Parcel | null>(null)
  useEffect(() => setHovered(null), [selected?.id])
  return <section className={`map-card ${selected ? 'is-selected' : ''}`} aria-label="Mapa de parcelas">
    <div className="map-stage">
      <div className="map-surface">
        <Suspense fallback={<div className="map-loading" role="status">Preparando el mapa…</div>}><GeographicMap parcels={parcels} selected={selected} baseMap={baseMap} reduced={!!reduced} onSelect={onSelect} onHover={setHovered} /></Suspense>
      </div>
      <div className="map-shade" aria-hidden="true" />
      <div className="map-view-tools">
        {selected && <button className="map-pill territory-back" onClick={onReset}><ArrowLeft size={16} aria-hidden="true" /> Ver territorio</button>}
        <div className="map-base-selector" role="group" aria-label="Vista del mapa">
          <button aria-label="Satélite" aria-pressed={baseMap === 'satellite'} onClick={() => setBaseMap('satellite')}><Satellite size={15} aria-hidden="true" /><span>Satélite</span></button>
          <button aria-label="Relieve" aria-pressed={baseMap === 'relief'} onClick={() => setBaseMap('relief')}><Mountain size={15} aria-hidden="true" /><span>Relieve</span></button>
        </div>
      </div>
      {hovered && <div className="map-hover" role="status"><strong>{hovered.id}</strong><span>{hovered.municipality} · {hovered.state}</span></div>}
      <div className="map-compass" aria-label="Norte hacia arriba">N<ArrowUp size={25} /><span>S</span></div>
      {selected && <div className="map-selection-caption"><span className="live-dot" /><strong>{selected.id}</strong><span>{selected.municipality} · {selected.state}</span></div>}
    </div>
    {children}
  </section>
}
