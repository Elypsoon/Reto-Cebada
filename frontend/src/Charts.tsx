import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ScatterChart, Scatter, ZAxis, ReferenceLine } from 'recharts'
import type { Curve, Model } from './types'
import { format } from './types'

const month = (value: string) => new Date(value + 'T12:00:00').toLocaleDateString('es-MX', { month: 'short', day: 'numeric' })

export function EvolutionChart({ curve }: { curve: Curve }) {
  const points = curve.points.map(p => ({ ...p, dateLabel: month(p.date) }))
  if (!points.some(p => p.value !== null)) return <div className="empty-chart">No hay una curva reconstruida para este sensor y esta parcela. Prueba el otro sensor.</div>
  return <div className="chart-frame" role="img" aria-label={`Evolución del NDVI reconstruido de ${curve.sensor}, de abril a octubre de 2025. La tabla de valores está disponible debajo.`}>
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={points} margin={{ top: 20, right: 12, left: -24, bottom: 2 }}>
        <defs><linearGradient id="curve-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#79844e" stopOpacity={.27} /><stop offset="100%" stopColor="#79844e" stopOpacity={.015} /></linearGradient></defs>
        <CartesianGrid vertical={false} stroke="#e5e5d9" strokeDasharray="3 5" />
        <XAxis dataKey="dateLabel" axisLine={false} tickLine={false} minTickGap={40} tick={{ fontSize: 12, fill: '#62665b' }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#62665b' }} domain={['auto', 'auto']} tickFormatter={v => format(Number(v), 1)} />
        <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #d9d9ca', fontSize: 13 }} formatter={(v) => [v == null ? 'Sin dato' : format(Number(v), 3), 'NDVI reconstruido']} />
        <Area type="linear" dataKey="value" stroke="#626c3d" strokeWidth={2.5} fill="url(#curve-fill)" connectNulls={false} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  </div>
}

export function ValidationChart({ model }: { model: Model }) {
  const palette = ['#626c3d', '#896129', '#526777']
  const maximum = Math.ceil(Math.max(...model.oof.flatMap(p => [p.observed, p.estimated])) + .2)
  return <div className="validation-chart" role="img" aria-label="Comparación entre rendimiento observado y estimado fuera de pliegue, 138 parcelas. La tabla de datos está disponible debajo.">
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 20, right: 24, left: 0, bottom: 35 }}>
        <CartesianGrid stroke="#e5e5d9" strokeDasharray="3 5" />
        <XAxis type="number" dataKey="observed" domain={[0, maximum]} tick={{ fontSize: 12 }} name="Observado" unit=" t/ha" label={{ value: 'Observado (t/ha)', position: 'bottom', offset: 15 }} />
        <YAxis type="number" dataKey="estimated" domain={[0, maximum]} tick={{ fontSize: 12 }} name="Estimado" unit=" t/ha" />
        <ZAxis range={[40, 40]} />
        <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ active, payload }) => {
          const p = payload?.[0]?.payload as Model['oof'][number] | undefined
          return active && p ? <div className="chart-tooltip"><strong>{p.id}</strong><br />{p.state}<br />Observado: {format(p.observed)} t/ha<br />Estimado: {format(p.estimated)} t/ha</div> : null
        }} />
        <ReferenceLine segment={[{ x: 0, y: 0 }, { x: maximum, y: maximum }]} stroke="#a9ae9b" strokeDasharray="5 5" />
        {['Hidalgo', 'Puebla', 'Tlaxcala'].map((state, i) => <Scatter key={state} name={state} data={model.oof.filter(p => p.state === state)} fill={palette[i]} fillOpacity={.8} isAnimationActive={false} />)}
      </ScatterChart>
    </ResponsiveContainer>
  </div>
}
