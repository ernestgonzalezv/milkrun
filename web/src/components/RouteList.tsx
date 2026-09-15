import type { RouteSummary } from '../api/types'

import { routeColor } from './palette'

interface Props {
  routes: RouteSummary[]
  selected: number | null
  onSelect: (id: number | null) => void
}

export function RouteList({ routes, selected, onSelect }: Props) {
  if (routes.length === 0) {
    return (
      <div className="empty">
        <strong>No routes for this day</strong>
        <span>Pick a depot and a date, then run the planner to build the day.</span>
      </div>
    )
  }

  return (
    <ul className="stack">
      {routes.map((route, index) => {
        const active = route.id === selected
        const hours = route.planned_duration_minutes / 60
        return (
          <li key={route.id}>
            <button
              type="button"
              className="route"
              aria-pressed={active}
              style={{ ['--route-color' as string]: routeColor(index) }}
              onClick={() => onSelect(active ? null : route.id)}
            >
              <span className="route__bar" aria-hidden="true" />
              <span className="route__id">
                <span className="route__code">{route.vehicle_code}</span>
                <span className="route__driver">{route.driver_name || 'Unassigned driver'}</span>
              </span>
              <span className="route__figures">
                <span className="route__km">{route.planned_distance_km.toFixed(1)} km</span>
                <span className="route__meta">
                  {route.stop_count} stops · {hours.toFixed(1)} h
                </span>
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
