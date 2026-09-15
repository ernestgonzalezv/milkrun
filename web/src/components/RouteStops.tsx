import { useRoute } from '../api/queries'
import type { Stop } from '../api/types'

import { StatusPill } from './StatusPill'

const DONE = new Set(['delivered'])
const PROBLEM = new Set(['failed', 'cancelled'])

interface Props {
  id: number
  onFocus: (stop: Stop) => void
}

/** Stops of a route, in the order the optimizer chose. */
export function RouteStops({ id, onFocus }: Props) {
  const { data: route, isPending, error } = useRoute(id)

  if (isPending) {
    return (
      <div className="stack">
        <div className="skeleton" />
        <div className="skeleton" />
      </div>
    )
  }

  if (error) {
    return (
      <p className="alert alert--error" role="alert">
        <span className="alert__dot" aria-hidden="true" />
        This route could not be loaded.
      </p>
    )
  }

  return (
    <div className="card timeline">
      <ul>
        {route.stops.map((leg) => {
          const status = leg.stop.status
          const tone = DONE.has(status) ? ' stop--done' : PROBLEM.has(status) ? ' stop--problem' : ''
          return (
            <li key={leg.id}>
              <button
                type="button"
                className={`stop stop--clickable${tone}`}
                onClick={() => onFocus(leg.stop)}
                title="Show on the map"
              >
                <span className="stop__seq">{leg.sequence}</span>
                <span className="stop__who">
                  <span className="stop__customer">{leg.stop.customer_name}</span>
                  <p className="stop__address">{leg.stop.address}</p>
                  <StatusPill status={status} />
                </span>
                <span className="stop__figures">
                  <div className="stop__km">{leg.leg_distance_km.toFixed(1)} km</div>
                  <div className="stop__eta">ETA ~{Math.round(leg.eta_minutes)} min</div>
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
