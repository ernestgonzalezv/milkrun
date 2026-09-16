import type { Depot, OptimizerMetrics, Route, RouteStop, RouteSummary, Stop, Vehicle } from '../api/types'

export const METRICS: OptimizerMetrics = {
  total_km: 160.7,
  stops_served: 80,
  km_per_stop: 2.01,
  baseline_sequential_km: 1120,
  baseline_sequential_stops: 80,
  baseline_nearest_neighbor_km: 226,
  baseline_nearest_neighbor_stops: 80,
  improvement_vs_sequential_pct: 85.6,
  improvement_vs_nearest_neighbor_pct: 29.0,
  solve_ms: 27,
}

export function depot(id = 1, name = 'Maspeth Distribution Center'): Depot {
  return { id, name, address: '58-49 Grand Ave', latitude: 40.722, longitude: -73.909, is_active: true }
}

export function vehicle(id = 1, capacity = 60, shift = 480): Vehicle {
  return {
    id,
    depot: 1,
    depot_name: 'Maspeth Distribution Center',
    code: `NYC-VAN-0${id}`,
    plate: `NYC-A${id}00`,
    capacity,
    max_shift_minutes: shift,
    avg_speed_kmh: 22,
    is_active: true,
  }
}

export function stop(id = 1, overrides: Partial<Stop> = {}): Stop {
  return {
    id,
    tracking_code: `TRACK${id}`,
    depot: 1,
    customer_name: `Customer ${id}`,
    phone: '+1 (212) 555-0100',
    address: `${id} Bedford Ave, Williamsburg, NY`,
    latitude: 40.717,
    longitude: -73.957,
    demand: 2,
    service_minutes: 5,
    scheduled_date: '2026-09-16',
    status: 'planned',
    status_display: 'Planned',
    notes: '',
    created_at: '2026-09-16T08:00:00Z',
    ...overrides,
  }
}

export function leg(sequence: number, overrides: Partial<RouteStop> = {}): RouteStop {
  return {
    id: 100 + sequence,
    sequence,
    stop: stop(sequence),
    leg_distance_km: 2.5,
    eta_minutes: sequence * 12,
    ...overrides,
  }
}

export function summary(id = 1, overrides: Partial<RouteSummary> = {}): RouteSummary {
  return {
    id,
    date: '2026-09-16',
    status: 'dispatched',
    vehicle_code: `NYC-VAN-0${id}`,
    driver_name: `Driver ${id}`,
    planned_distance_km: 42,
    planned_duration_minutes: 240,
    stop_count: 20,
    ...overrides,
  }
}

export function route(id = 1, overrides: Partial<Route> = {}): Route {
  return {
    id,
    depot: 1,
    date: '2026-09-16',
    status: 'dispatched',
    vehicle: id,
    vehicle_code: `NYC-VAN-0${id}`,
    driver: id,
    driver_name: `Driver ${id}`,
    planned_distance_km: 42,
    planned_duration_minutes: 240,
    planned_load: 50,
    optimizer_metrics: METRICS,
    stops: [leg(1), leg(2)],
    ...overrides,
  }
}

export function page<T>(results: T[]) {
  return { count: results.length, next: null, previous: null, results }
}
