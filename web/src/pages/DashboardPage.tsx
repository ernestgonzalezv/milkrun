import { Suspense, lazy, useEffect, useMemo, useState } from 'react'

import { ApiError } from '../api/client'
import {
  useDepots,
  usePlanDay,
  useRoutes,
  useRoutesWithStops,
  useStops,
  useVehicles,
} from '../api/queries'
import type { Stop } from '../api/types'
import { useAuth } from '../auth/useAuth'
import { usePersistentState } from '../hooks/usePersistentState'
import { Logo } from '../components/Logo'
import { Metrics } from '../components/Metrics'
import { RouteList } from '../components/RouteList'
import { RouteStops } from '../components/RouteStops'
import { StatusPill } from '../components/StatusPill'

/**
 * MapLibre is ~1 MB minified and is not needed until there is something to
 * draw. Loading it lazily keeps it out of the sign-in bundle: the initial
 * download drops from 1.3 MB to ~250 kB.
 */
const MapPanel = lazy(() =>
  import('../components/MapPanel').then((module) => ({ default: module.MapPanel })),
)

/** Today as YYYY-MM-DD in local time, not UTC. */
function today(): string {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60_000
  return new Date(now.getTime() - offset).toISOString().slice(0, 10)
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

export function DashboardPage() {
  const { user, signOut } = useAuth()
  const [date, setDate] = useState(today)
  // Remembered across reloads: a dispatcher works the same warehouse every
  // morning, and re-picking it after every refresh is needless friction.
  const [depotId, setDepotId] = usePersistentState<number>('milkrun.depot', 0, (raw) => {
    const parsed = Number(raw)
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null
  })
  const [selected, setSelected] = useState<number | null>(null)
  const [focus, setFocus] = useState<Stop | null>(null)

  const { data: depots = [] } = useDepots()
  const activeDepot = depots.find((d) => d.id === depotId) ?? depots[0] ?? null
  const depot = activeDepot?.id

  const { data: routes = [], isPending: loadingRoutes } = useRoutes(date, depot)
  const { data: routesWithStops = [] } = useRoutesWithStops(date, depot)
  const { data: stops = [] } = useStops(date, depot)
  const { data: vehicles = [] } = useVehicles(depot)
  const plan = usePlanDay(date, depot)

  const unassigned = useMemo(() => stops.filter((s) => s.status === 'pending'), [stops])

  // Escape backs out one level: first the focused stop, then the selected
  // route. Dispatchers live on the keyboard and expect a way out.
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key !== 'Escape') return
      setFocus((current) => {
        if (current) return null
        setSelected(null)
        return null
      })
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // The optimizer stores identical metrics on every route of the same plan, so
  // reading the first one is enough.
  const metrics = routes.length > 0 ? (routesWithStops[0]?.optimizer_metrics ?? null) : null

  const planned = routes.length > 0
  const displayName = user?.full_name || user?.username || ''

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__brand">
          <Logo suffix="dispatch" />
        </div>

        <div className="topbar__controls">
          <label className="field">
            <span>Depot</span>
            <select
              value={depot ?? ''}
              onChange={(e) => {
                setDepotId(Number(e.target.value))
                setSelected(null)
                setFocus(null)
              }}
            >
              {depots.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Date</span>
            <input
              type="date"
              value={date}
              onChange={(e) => {
                setDate(e.target.value)
                setSelected(null)
                setFocus(null)
              }}
            />
          </label>

          <button
            className="btn"
            type="button"
            disabled={plan.isPending || !depot}
            onClick={() => plan.mutate(planned)}
          >
            {plan.isPending ? 'Solving…' : planned ? 'Re-plan day' : 'Plan the day'}
          </button>
        </div>

        <div className="topbar__user">
          <span className="avatar" aria-hidden="true">
            {initials(displayName)}
          </span>
          <span className="topbar__who">
            <strong>{displayName}</strong>
            <span>{user?.role}</span>
          </span>
          <button className="btn btn--ghost" type="button" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <div className="body">
        <aside className="rail">
          {plan.error && (
            <p className="alert alert--error" role="alert">
              <span className="alert__dot" aria-hidden="true" />
              {plan.error instanceof ApiError ? plan.error.message : 'The day could not be planned.'}
            </p>
          )}

          <Metrics
            metrics={metrics}
            routes={routesWithStops}
            vehicles={vehicles}
            unassigned={unassigned.length}
          />

          <section className="stack">
            <div className="section__head">
              <h2>Routes</h2>
              <span className="section__count">{routes.length}</span>
              {metrics && (
                <span className="section__note">solved in {Math.round(metrics.solve_ms)} ms</span>
              )}
            </div>

            {loadingRoutes ? (
              <div className="stack">
                <div className="skeleton" />
                <div className="skeleton" />
                <div className="skeleton" />
              </div>
            ) : (
              <RouteList
                routes={routes}
                selected={selected}
                onSelect={(id) => {
                  setSelected(id)
                  setFocus(null)
                }}
              />
            )}
          </section>

          {selected !== null && (
            <section className="stack">
              <div className="section__head">
                <h2>Stops on this route</h2>
                <span className="section__note">in the order the solver chose</span>
              </div>
              <RouteStops id={selected} onFocus={setFocus} />
            </section>
          )}

          {unassigned.length > 0 && (
            <section className="stack">
              <div className="section__head">
                <h2>Unassigned</h2>
                <span className="section__count">{unassigned.length}</span>
                <span className="section__note">no room in the fleet</span>
              </div>
              <div className="card timeline">
                <ul>
                  {unassigned.map((stop) => (
                    <li key={stop.id} className="stop stop--problem">
                      <span className="stop__seq">!</span>
                      <span className="stop__who">
                        <span className="stop__customer">{stop.customer_name}</span>
                        <p className="stop__address">{stop.address}</p>
                        <StatusPill status={stop.status} />
                      </span>
                      <span className="stop__figures">
                        <div className="stop__km">{stop.demand.toFixed(1)}</div>
                        <div className="stop__eta">units</div>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          )}
        </aside>

        <Suspense fallback={<div className="map" />}>
          <MapPanel
            depot={activeDepot}
            routes={routesWithStops}
            highlighted={selected}
            focus={focus}
          />
        </Suspense>
      </div>
    </div>
  )
}
