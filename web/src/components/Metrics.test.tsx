import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { OptimizerMetrics, Route, RouteStop, Vehicle } from '../api/types'

import { Metrics } from './Metrics'

const BASE: OptimizerMetrics = {
  total_km: 273.4,
  stops_served: 100,
  km_per_stop: 2.734,
  baseline_sequential_km: 1281,
  baseline_sequential_stops: 100,
  baseline_nearest_neighbor_km: 349,
  baseline_nearest_neighbor_stops: 100,
  improvement_vs_sequential_pct: 78.6,
  improvement_vs_nearest_neighbor_pct: 21.6,
  solve_ms: 32,
}

function vehicle(id: number, capacity: number, shift: number): Vehicle {
  return {
    id,
    depot: 1,
    depot_name: 'Depot',
    code: `VAN-${id}`,
    plate: `P-${id}`,
    capacity,
    max_shift_minutes: shift,
    avg_speed_kmh: 22,
    is_active: true,
  }
}

const NO_STOPS: RouteStop[] = []

function route(id: number, vehicleId: number, minutes: number, load: number): Route {
  return {
    id,
    depot: 1,
    date: '2026-09-15',
    status: 'dispatched',
    vehicle: vehicleId,
    vehicle_code: `VAN-${vehicleId}`,
    driver: null,
    driver_name: '',
    planned_distance_km: 40,
    planned_duration_minutes: minutes,
    planned_load: load,
    optimizer_metrics: BASE,
    stops: NO_STOPS,
  }
}

const FLEET = [vehicle(1, 100, 480), vehicle(2, 100, 480), vehicle(3, 100, 480)]

describe('metrics panel', () => {
  it('leads with the kilometres the plan saved', () => {
    render(<Metrics metrics={BASE} routes={[route(1, 1, 200, 50)]} vehicles={FLEET} unassigned={0} />)

    // 349 manual - 273.4 planned = 75.6, truncated to 75: the tile that
    // justifies the product rounds against itself, never in its favour.
    expect(screen.getByText('75 km')).toBeInTheDocument()
    expect(screen.getByText('−21.6% vs manual routing')).toBeInTheDocument()
    expect(screen.getByText('273.4 km')).toBeInTheDocument()
  })

  it('shows a worse-than-manual plan without dressing it up', () => {
    // A panel that only renders good numbers is useless for deciding anything:
    // if the plan came out worse than manual routing, it has to be visible.
    render(
      <Metrics
        metrics={{ ...BASE, improvement_vs_nearest_neighbor_pct: -3.4, total_km: 361 }}
        routes={[route(1, 1, 200, 50)]}
        vehicles={FLEET}
        unassigned={0}
      />,
    )

    expect(screen.getByText('+3.4% vs manual routing')).toBeInTheDocument()
    expect(screen.getByText('+12 km')).toBeInTheDocument()
  })

  it('counts stops left out of the plan against the total', () => {
    render(<Metrics metrics={BASE} routes={[route(1, 1, 200, 50)]} vehicles={FLEET} unassigned={6} />)

    expect(screen.getByText('100 / 106')).toBeInTheDocument()
    expect(screen.getByText('6 left out of the plan')).toBeInTheDocument()
  })

  it('says how many vehicles can stay parked', () => {
    render(<Metrics metrics={BASE} routes={[route(1, 1, 200, 50)]} vehicles={FLEET} unassigned={0} />)

    expect(screen.getByText('1 of 3')).toBeInTheDocument()
    expect(screen.getByText('2 can stay parked')).toBeInTheDocument()
  })

  it('reports the longest shift, not the average one', () => {
    // An average would hide the single route that breaks the day.
    render(
      <Metrics
        metrics={BASE}
        routes={[route(1, 1, 120, 10), route(2, 2, 400, 10)]}
        vehicles={FLEET}
        unassigned={0}
      />,
    )

    expect(screen.getByText('6.7 h')).toBeInTheDocument()
    expect(screen.getByText('VAN-2 · 8.0 h limit')).toBeInTheDocument()
  })

  it('flags a driver who is nearly out of shift', () => {
    const { container } = render(
      <Metrics
        metrics={BASE}
        routes={[route(1, 1, 460, 10)]}
        vehicles={FLEET}
        unassigned={0}
      />,
    )

    // 460 of 480 minutes: under half an hour of slack left.
    expect(container.querySelectorAll('.metric--alert')).toHaveLength(1)
  })

  it('warns when the fullest van has no room for another order', () => {
    render(
      <Metrics
        metrics={BASE}
        routes={[route(1, 1, 200, 98)]}
        vehicles={FLEET}
        unassigned={0}
      />,
    )

    expect(screen.getByText('98%')).toBeInTheDocument()
    expect(screen.getByText('VAN-1 · no room for add-ons')).toBeInTheDocument()
  })

  it('never rounds a nearly full van up to 100%', () => {
    // 99.7% displayed as 100% would say the van is full when an order still
    // fits, which is the exact question this tile exists to answer.
    render(
      <Metrics
        metrics={BASE}
        routes={[route(1, 1, 200, 99.7)]}
        vehicles={FLEET}
        unassigned={0}
      />,
    )

    expect(screen.getByText('99%')).toBeInTheDocument()
    expect(screen.queryByText('100%')).not.toBeInTheDocument()
  })

  it('does not break before a plan exists', () => {
    render(<Metrics metrics={null} routes={[]} vehicles={[]} unassigned={0} />)

    expect(screen.getAllByText('—')).toHaveLength(2)
  })
})
