/**
 * Tipos del contrato con la API.
 *
 * Son un espejo a mano del esquema OpenAPI que publica el backend en
 * /api/schema/. Se escriben a mano y no se generan porque son pocos y el
 * generador mete mucho ruido; si el contrato creciera, la linea de comando
 * `npx openapi-typescript` los saca de la misma fuente sin cambiar nada mas.
 */

export type StopStatus =
  | 'pending'
  | 'planned'
  | 'in_transit'
  | 'delivered'
  | 'failed'
  | 'cancelled'

export type RouteStatus = 'draft' | 'dispatched' | 'in_progress' | 'completed'

export interface User {
  id: number
  username: string
  full_name: string
  email: string
  phone: string
  role: 'dispatcher' | 'driver'
}

export interface Depot {
  id: number
  name: string
  address: string
  latitude: number
  longitude: number
  is_active: boolean
}

export interface Vehicle {
  id: number
  depot: number
  depot_name: string
  code: string
  plate: string
  capacity: number
  max_shift_minutes: number
  avg_speed_kmh: number
  is_active: boolean
}

export interface Stop {
  id: number
  tracking_code: string
  depot: number
  customer_name: string
  phone: string
  address: string
  latitude: number
  longitude: number
  demand: number
  service_minutes: number
  scheduled_date: string
  status: StopStatus
  status_display: string
  notes: string
  created_at: string
}

export interface RouteStop {
  id: number
  sequence: number
  leg_distance_km: number
  eta_minutes: number
  stop: Stop
}

/** Metricas que deja el optimizador, para poder auditar el plan. */
export interface OptimizerMetrics {
  total_km: number
  stops_served: number
  km_per_stop: number
  baseline_sequential_km: number
  baseline_sequential_stops: number
  baseline_nearest_neighbor_km: number
  baseline_nearest_neighbor_stops: number
  improvement_vs_sequential_pct: number
  improvement_vs_nearest_neighbor_pct: number
  solve_ms: number
}

export interface Route {
  id: number
  depot: number
  date: string
  status: RouteStatus
  vehicle: number
  vehicle_code: string
  driver: number | null
  driver_name: string
  planned_distance_km: number
  planned_duration_minutes: number
  planned_load: number
  optimizer_metrics: OptimizerMetrics
  stops: RouteStop[]
}

export interface RouteSummary {
  id: number
  date: string
  status: RouteStatus
  vehicle_code: string
  driver_name: string
  planned_distance_km: number
  planned_duration_minutes: number
  stop_count: number
}

export interface PlanResult {
  routes: Route[]
  unassigned: Stop[]
  metrics: OptimizerMetrics
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface TokenPair {
  access: string
  refresh: string
}
