import { useEffect, useRef, useState } from 'react'
import { Map, LngLatBounds, MercatorCoordinate, ScaleControl, setWorkerUrl, type ExpressionSpecification, type GeoJSONSource, type FilterSpecification, type StyleSpecification } from 'maplibre-gl'
import mapWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import type { FeatureCollection, Geometry, Position } from 'geojson'
import { Crosshair, Minus, Plus } from 'lucide-react'
import type { Parcel } from './types'
import 'maplibre-gl/dist/maplibre-gl.css'

// Let Vite serve/bundle the ESM worker rather than resolving it inside optimized dependencies.
setWorkerUrl(mapWorkerUrl)

export type BaseMap = 'satellite' | 'relief'
type Properties = { id: string; state: string; municipality: string }
type ParcelsGeoJSON = FeatureCollection<Geometry, Properties>
const COLORS: ExpressionSpecification = ['match', ['get', 'state'], 'Hidalgo', '#f4eed5', 'Puebla', '#d9ebbc', 'Tlaxcala', '#ffd69a', '#ffffff']

function boundsFor(data: ParcelsGeoJSON, ids: Set<string>) {
  const bounds = new LngLatBounds()
  const visit = (coordinates: Position | Position[] | Position[][] | Position[][][]) => {
    if (typeof coordinates[0] === 'number') bounds.extend(coordinates as [number, number])
    else for (const point of coordinates) visit(point as Position)
  }
  for (const feature of data.features) {
    if (ids.has(feature.properties.id) && (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon')) visit(feature.geometry.coordinates)
  }
  return bounds.isEmpty() ? null : bounds
}

function fitGeometry(map: Map, bounds: LngLatBounds, selected: boolean, reduced: boolean, duration = 850) {
  const container = map.getContainer()
  const height = container.clientHeight
  const width = container.clientWidth
  // Keep the parcel in the visible terrain to the left of the incoming detail panel.
  const detailWidth = selected && width > 900 ? container.closest('.map-card')!.querySelector('.estimate-panel')?.getBoundingClientRect().width ?? width * .42 : 0
  const padding = { top: width <= 900 ? 250 : 150, bottom: selected ? 130 : 115, left: width < 600 ? 28 : 65, right: detailWidth + (width < 600 ? 65 : 80) }
  const nw = MercatorCoordinate.fromLngLat(bounds.getNorthWest())
  const se = MercatorCoordinate.fromLngLat(bounds.getSouthEast())
  const zoom = Math.min(selected ? 17.5 : 10,
    Math.log2(Math.max(1, width - padding.left - padding.right) / (512 * Math.max(se.x - nw.x, 1e-10))),
    Math.log2(Math.max(1, height - padding.top - padding.bottom) / (512 * Math.max(se.y - nw.y, 1e-10))))
  const center = new MercatorCoordinate((nw.x + se.x) / 2, (nw.y + se.y) / 2).toLngLat()
  map.easeTo({ center, zoom, bearing: 0, pitch: 0, offset: [(padding.left - padding.right) / 2, (padding.top - padding.bottom) / 2], duration: reduced ? 0 : duration })
}

function style(): StyleSpecification {
  return {
    version: 8,
    sources: {
      satellite: { type: 'raster', tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'], tileSize: 256, maxzoom: 19,
        attribution: 'Source: Esri, Vantor, Earthstar Geographics, and the GIS User Community' },
      relief: { type: 'raster', tiles: ['https://a.tile.opentopomap.org/{z}/{x}/{y}.png'], tileSize: 256, maxzoom: 17,
        attribution: 'Map data: © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>, SRTM | Map style: © <a href="https://opentopomap.org" target="_blank" rel="noopener noreferrer">OpenTopoMap</a> (CC-BY-SA)' },
      parcels: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
      centers: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    },
    layers: [
      { id: 'land', type: 'background', paint: { 'background-color': '#dedfcb' } },
      { id: 'satellite', type: 'raster', source: 'satellite', paint: { 'raster-fade-duration': 250 } },
      { id: 'relief', type: 'raster', source: 'relief', layout: { visibility: 'none' }, paint: { 'raster-fade-duration': 250 } },
      { id: 'parcel-fill', type: 'fill', source: 'parcels', paint: { 'fill-color': COLORS, 'fill-opacity': .23 } },
      { id: 'parcel-line', type: 'line', source: 'parcels', paint: { 'line-color': COLORS, 'line-width': 1.6 } },
      { id: 'parcel-selected', type: 'line', source: 'parcels', filter: ['==', ['get', 'id'], ''], paint: { 'line-color': '#ffffff', 'line-width': 3 } },
      { id: 'parcel-pins', type: 'circle', source: 'centers', paint: { 'circle-color': COLORS, 'circle-radius': 3.5, 'circle-stroke-color': '#303c29', 'circle-stroke-width': 1 } },
    ],
  }
}

export default function GeographicMap({ parcels, selected, baseMap, reduced, onSelect, onHover }: {
  parcels: Parcel[]; selected: Parcel | null; baseMap: BaseMap; reduced: boolean;
  onSelect: (id: string) => void; onHover: (parcel: Parcel | null) => void;
}) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const geometryRef = useRef<ParcelsGeoJSON | null>(null)
  const reducedRef = useRef(reduced)
  reducedRef.current = reduced
  const latest = useRef({ parcels, selected, baseMap, onSelect, onHover })
  latest.current = { parcels, selected, baseMap, onSelect, onHover }
  const [data, setData] = useState<ParcelsGeoJSON | null>(null)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tileError, setTileError] = useState<BaseMap | null>(null)
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setError(null)
    // Refresh cached response metadata after correcting the GeoJSON content type.
    fetch('/data/parcels.geojson', { signal: controller.signal, cache: 'reload' }).then(async response => {
      if (!response.ok || !response.headers.get('content-type')?.includes('json')) throw new Error('geometry')
      const collection = await response.json() as ParcelsGeoJSON
      if (collection.type !== 'FeatureCollection' || !collection.features.length) throw new Error('geometry')
      if (!controller.signal.aborted) { geometryRef.current = collection; setData(collection) }
    }).catch(() => { if (!controller.signal.aborted) setError('No se pudieron cargar los contornos geográficos.') })
    return () => controller.abort()
  }, [retry])

  useEffect(() => {
    if (!container.current) return
    setLoading(true)
    let map: Map
    try {
      map = new Map({ container: container.current, style: style(), center: [-98.5, 19.6], zoom: 8, minZoom: 5, maxZoom: 19,
        attributionControl: { compact: false }, renderWorldCopies: false, dragRotate: false, pitchWithRotate: false,
        touchZoomRotate: true, cooperativeGestures: true, locale: {
          'AttributionControl.ToggleAttribution': 'Mostrar fuentes del mapa', 'Map.Title': 'Mapa geográfico de parcelas',
          'CooperativeGesturesHandler.WindowsHelpText': 'Usa Ctrl + desplazamiento para acercar el mapa',
          'CooperativeGesturesHandler.MacHelpText': 'Usa ⌘ + desplazamiento para acercar el mapa',
          'CooperativeGesturesHandler.MobileHelpText': 'Usa dos dedos para mover el mapa',
        } })
    } catch {
      setError('El navegador no pudo iniciar el mapa. Comprueba que WebGL esté disponible.')
      return
    }
    mapRef.current = map
    map.touchZoomRotate.disableRotation()
    map.keyboard.disableRotation()
    map.addControl(new ScaleControl({ maxWidth: 100, unit: 'metric' }), 'bottom-left')
    map.on('load', () => setReady(true))
    map.on('error', event => {
      if ('sourceId' in event && event.sourceId === latest.current.baseMap) { setTileError(latest.current.baseMap); setLoading(false) }
    })
    map.on('sourcedata', event => {
      if (event.sourceId === latest.current.baseMap && event.sourceDataType === 'content') { setTileError(null); setLoading(false) }
    })
    map.on('idle', () => setLoading(false))
    map.on('click', event => {
      const hit = map.queryRenderedFeatures([[event.point.x - 6, event.point.y - 6], [event.point.x + 6, event.point.y + 6]], { layers: ['parcel-fill', 'parcel-line', 'parcel-pins'] })[0]
      if (hit?.properties?.id) latest.current.onSelect(String(hit.properties.id))
    })
    map.on('mousemove', event => {
      const hit = map.queryRenderedFeatures([[event.point.x - 5, event.point.y - 5], [event.point.x + 5, event.point.y + 5]], { layers: ['parcel-fill', 'parcel-line', 'parcel-pins'] })[0]
      map.getCanvas().style.cursor = hit ? 'pointer' : ''
      latest.current.onHover(latest.current.parcels.find(p => p.id === hit?.properties?.id) ?? null)
    })
    map.getCanvas().addEventListener('mouseleave', () => latest.current.onHover(null))
    let previousWidth = container.current.clientWidth
    let previousHeight = container.current.clientHeight
    const resize = new ResizeObserver(() => {
      map.resize()
      const width = container.current?.clientWidth ?? previousWidth
      const height = container.current?.clientHeight ?? previousHeight
      if ((Math.abs(width - previousWidth) > 1 || Math.abs(height - previousHeight) > 1) && geometryRef.current) {
        const { selected, parcels } = latest.current
        const bounds = boundsFor(geometryRef.current, new Set(selected ? [selected.id] : parcels.map(p => p.id)))
        if (bounds) fitGeometry(map, bounds, !!selected, reducedRef.current, 0)
      }
      previousWidth = width
      previousHeight = height
    })
    resize.observe(container.current)
    return () => { resize.disconnect(); setReady(false); mapRef.current = null; map.remove() }
  }, [retry])

  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map || !data) return
    const ids = new Set(parcels.map(p => p.id))
    const visible = { ...data, features: data.features.filter(f => ids.has(f.properties.id)) }
    ;(map.getSource('parcels') as GeoJSONSource).setData(visible)
    // Centers only help select tiny parcels from the overview; boundaries always use original coordinates.
    const centers: FeatureCollection = { type: 'FeatureCollection', features: visible.features.map(f => {
      const bounds = boundsFor(data, new Set([f.properties.id]))!
      return { type: 'Feature', properties: f.properties, geometry: { type: 'Point', coordinates: bounds.getCenter().toArray() } }
    }) }
    ;(map.getSource('centers') as GeoJSONSource).setData(centers)
    map.setFilter('parcel-selected', ['==', ['get', 'id'], selected?.id ?? ''])
    map.setFilter('parcel-pins', ['!=', ['get', 'id'], selected?.id ?? ''] as FilterSpecification)
  }, [ready, data, parcels, selected?.id])

  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    setTileError(null); setLoading(true)
    map.setLayoutProperty('satellite', 'visibility', baseMap === 'satellite' ? 'visible' : 'none')
    map.setLayoutProperty('relief', 'visibility', baseMap === 'relief' ? 'visible' : 'none')
    map.once('idle', () => setLoading(false))
  }, [ready, baseMap])

  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map || !data) return
    map.stop()
    const target = boundsFor(data, new Set(selected ? [selected.id] : parcels.map(p => p.id)))
    if (!target) return
    fitGeometry(map, target, !!selected, reduced)
    return () => { map.stop() }
  }, [ready, data, selected?.id, parcels, reduced])

  const reset = () => {
    const map = mapRef.current
    if (!map || !data) return
    const bounds = boundsFor(data, new Set(selected ? [selected.id] : parcels.map(p => p.id)))
    if (bounds) fitGeometry(map, bounds, !!selected, reduced, 650)
  }
  return <>
    <div ref={container} className="geographic-map" role="region" aria-label={`Mapa ${baseMap === 'satellite' ? 'satelital' : 'de relieve'} de parcelas`} />
    <div className="map-controls" aria-label="Controles del mapa">
      <button aria-label="Acercar mapa" onClick={() => mapRef.current?.zoomIn({ duration: reduced ? 0 : 250 })}><Plus size={18} /></button>
      <button aria-label="Alejar mapa" onClick={() => mapRef.current?.zoomOut({ duration: reduced ? 0 : 250 })}><Minus size={18} /></button>
      <button aria-label={selected ? 'Restablecer encuadre de la parcela' : 'Restablecer encuadre del territorio'} onClick={reset}><Crosshair size={18} /></button>
    </div>
    {error ? <div className="map-network-notice" role="alert">{error}<button onClick={() => setRetry(v => v + 1)}>Reintentar</button></div> : tileError === baseMap ? <div className="map-network-notice" role="status">No se pudo cargar el fondo. Comprueba tu conexión o cambia de vista. Los contornos siguen disponibles.</div> : loading && <div className="map-loading" role="status">Cargando {baseMap === 'satellite' ? 'imagen satelital' : 'relieve'}…</div>}
  </>
}
