import type { OptimizerMetrics, Route, Vehicle } from '../api/types'

interface Props {
  metrics: OptimizerMetrics | null
  routes: Route[]
  vehicles: Vehicle[]
  unassigned: number
}

type Tone = 'neutral' | 'good' | 'bad' | 'alert'

function Metric({
  label,
  value,
  note,
  tone = 'neutral',
}: {
  label: string
  value: string
  note?: string
  tone?: Tone
}) {
  return (
    <div className={`card metric${tone === 'neutral' ? '' : ` metric--${tone}`}`}>
      <div className="metric__label">{label}</div>
      <div className="metric__value">{value}</div>
      {note && <div className="metric__note">{note}</div>}
    </div>
  )
}

const hours = (minutes: number) => `${(minutes / 60).toFixed(1)} h`

/**
 * The day's plan, as six numbers.
 *
 * Every tile here answers a question the dispatcher acts on. That is the bar:
 * a figure that changes nothing is decoration, and decoration on an operations
 * panel costs attention that the exceptions need.
 *
 *   Distance / Saved   did the software earn its place today
 *   Coverage           can every customer be promised a delivery
 *   Fleet              which vehicles and drivers can stay home
 *   Longest shift      is the plan actually feasible, or is a driver on the edge
 *   Peak load          is there room to accept one more order this morning
 *
 * Improvement is shown exactly as the backend reports it, negative included: a
 * panel that only renders good numbers is useless for deciding anything.
 */
export function Metrics({ metrics, routes, vehicles, unassigned }: Props) {
  if (!metrics) {
    return (
      <div className="metrics">
        <Metric label="Distance" value="," note="nothing planned yet" />
        <Metric label="Saved" value="," note="run the planner" />
      </div>
    )
  }

  const saved = metrics.baseline_nearest_neighbor_km - metrics.total_km
  const gain = metrics.improvement_vs_nearest_neighbor_pct
  const sign = gain > 0 ? '−' : '+'

  const total = metrics.stops_served + unassigned
  const idle = Math.max(0, vehicles.length - routes.length)

  const byId = new Map(vehicles.map((v) => [v.id, v]))
  const longest = routes.reduce<Route | null>(
    (worst, r) => (!worst || r.planned_duration_minutes > worst.planned_duration_minutes ? r : worst),
    null,
  )
  const shiftLimit = longest ? byId.get(longest.vehicle)?.max_shift_minutes : undefined
  const shiftUse = longest && shiftLimit ? longest.planned_duration_minutes / shiftLimit : 0

  const fullest = routes.reduce<{ route: Route; use: number } | null>((worst, r) => {
    const capacity = byId.get(r.vehicle)?.capacity
    if (!capacity) return worst
    const use = r.planned_load / capacity
    return !worst || use > worst.use ? { route: r, use } : worst
  }, null)

  return (
    <div className="metrics">
      <Metric
        label="Distance"
        value={`${metrics.total_km.toFixed(1)} km`}
        note={`${metrics.km_per_stop.toFixed(2)} km per stop`}
      />
      <Metric
        label="Saved"
        value={`${saved >= 0 ? '' : '+'}${Math.floor(Math.abs(saved))} km`}
        note={`${sign}${Math.abs(gain).toFixed(1)}% vs manual routing`}
        tone={gain > 0 ? 'good' : 'bad'}
      />
      <Metric
        label="Coverage"
        value={`${metrics.stops_served} / ${total}`}
        note={unassigned > 0 ? `${unassigned} left out of the plan` : 'every stop covered'}
        tone={unassigned > 0 ? 'alert' : 'neutral'}
      />
      <Metric
        label="Fleet"
        value={vehicles.length > 0 ? `${routes.length} of ${vehicles.length}` : String(routes.length)}
        note={idle > 0 ? `${idle} can stay parked` : 'every vehicle is out'}
      />
      <Metric
        label="Longest shift"
        value={longest ? hours(longest.planned_duration_minutes) : ','}
        note={
          longest && shiftLimit
            ? `${longest.vehicle_code} · ${hours(shiftLimit)} limit`
            : longest
              ? longest.vehicle_code
              : undefined
        }
        tone={shiftUse >= 0.9 ? 'alert' : 'neutral'}
      />
      <Metric
        label="Fullest van"
        value={fullest ? `${Math.floor(fullest.use * 100)}%` : ','}
        note={
          fullest
            ? fullest.use >= 0.95
              ? `${fullest.route.vehicle_code} · no room for add-ons`
              : `${fullest.route.vehicle_code} · room for more`
            : undefined
        }
        tone={fullest && fullest.use >= 0.95 ? 'alert' : 'neutral'}
      />
    </div>
  )
}
