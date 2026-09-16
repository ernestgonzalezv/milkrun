/**
 * Hooks de datos. Un archivo por capa, no por pantalla: si manana el
 * dashboard cambia de forma, las claves de cache no se mueven.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from './client'
import type {
  Depot,
  Paginated,
  PlanResult,
  Route,
  RouteSummary,
  Stop,
  User,
  Vehicle,
} from './types'

/**
 * Claves de cache centralizadas.
 *
 * Tenerlas en un objeto y no como literales sueltos es lo que hace que
 * invalidar despues de planificar sea una linea y no una caceria por el
 * codigo buscando quien uso `['routes']`.
 */
export const keys = {
  me: ['me'] as const,
  depots: ['depots'] as const,
  vehicles: (depot?: number) => ['vehicles', depot ?? null] as const,
  stops: (fecha: string, depot?: number) => ['stops', fecha, depot ?? null] as const,
  routes: (fecha: string, depot?: number) => ['routes', fecha, depot ?? null] as const,
  route: (id: number) => ['route', id] as const,
}

export function useMe() {
  return useQuery({
    queryKey: keys.me,
    queryFn: () => api.get<User>('/api/v1/auth/me/'),
    staleTime: Infinity,
  })
}

export function useDepots() {
  return useQuery({
    queryKey: keys.depots,
    queryFn: async () => (await api.get<Paginated<Depot>>('/api/v1/depots/')).results,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * The fleet of a depot.
 *
 * The panel needs it to answer two questions a route list cannot: how many
 * vehicles stayed parked, and how close to full the busiest one is.
 */
export function useVehicles(depot?: number) {
  return useQuery({
    queryKey: keys.vehicles(depot),
    queryFn: async () => {
      const params = new URLSearchParams({ is_active: 'true', limit: '200' })
      if (depot) params.set('depot', String(depot))
      return (await api.get<Paginated<Vehicle>>(`/api/v1/vehicles/?${params}`)).results
    },
    enabled: Boolean(depot),
    staleTime: 5 * 60 * 1000,
  })
}

export function useStops(fecha: string, depot?: number) {
  return useQuery({
    queryKey: keys.stops(fecha, depot),
    queryFn: async () => {
      const params = new URLSearchParams({ scheduled_date: fecha, limit: '500' })
      if (depot) params.set('depot', String(depot))
      return (await api.get<Paginated<Stop>>(`/api/v1/stops/?${params}`)).results
    },
    enabled: Boolean(fecha),
  })
}

export function useRoutes(fecha: string, depot?: number) {
  return useQuery({
    queryKey: keys.routes(fecha, depot),
    queryFn: async () => {
      const params = new URLSearchParams({ date: fecha, limit: '100' })
      if (depot) params.set('depot', String(depot))
      return (await api.get<Paginated<RouteSummary>>(`/api/v1/routes/?${params}`)).results
    },
    enabled: Boolean(fecha),
  })
}

/**
 * Rutas del dia con sus paradas, para el mapa.
 *
 * Va contra `?expand=stops` en vez de pedir el detalle ruta por ruta: son
 * hasta 26 vehiculos, y 26 peticiones para pintar un mapa es exactamente el
 * N+1 que el backend ya resuelve con un prefetch.
 */
export function useRoutesWithStops(fecha: string, depot?: number) {
  return useQuery({
    queryKey: [...keys.routes(fecha, depot), 'expandidas'] as const,
    queryFn: async () => {
      const params = new URLSearchParams({ date: fecha, limit: '100', expand: 'stops' })
      if (depot) params.set('depot', String(depot))
      return (await api.get<Paginated<Route>>(`/api/v1/routes/?${params}`)).results
    },
    enabled: Boolean(fecha),
  })
}

/** Detalle completo de una ruta, con sus paradas. Se pide solo al abrirla. */
export function useRoute(id: number | null) {
  return useQuery({
    queryKey: keys.route(id ?? 0),
    queryFn: () => api.get<Route>(`/api/v1/routes/${id}/`),
    enabled: id !== null,
  })
}

export function usePlanDay(fecha: string, depot?: number) {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (replan: boolean) =>
      api.post<PlanResult>('/api/v1/routes/plan/', { depot, date: fecha, replan }),
    onSuccess: () => {
      void cliente.invalidateQueries({ queryKey: keys.routes(fecha, depot) })
      void cliente.invalidateQueries({ queryKey: keys.stops(fecha, depot) })
    },
  })
}
