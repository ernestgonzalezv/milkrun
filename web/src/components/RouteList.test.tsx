import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { summary } from '../test/fixtures'

import { RouteList } from './RouteList'

describe('route list', () => {
  it('explains what to do when there are no routes yet', () => {
    render(<RouteList routes={[]} selected={null} onSelect={vi.fn()} />)

    expect(screen.getByText('No routes for this day')).toBeInTheDocument()
    expect(screen.getByText(/run the planner/i)).toBeInTheDocument()
  })

  it('shows the vehicle, driver, distance and duration of each route', () => {
    render(
      <RouteList
        routes={[summary(1, { planned_distance_km: 42.04, planned_duration_minutes: 240 })]}
        selected={null}
        onSelect={vi.fn()}
      />,
    )

    expect(screen.getByText('NYC-VAN-01')).toBeInTheDocument()
    expect(screen.getByText('Driver 1')).toBeInTheDocument()
    expect(screen.getByText('42.0 km')).toBeInTheDocument()
    expect(screen.getByText(/20 stops/)).toBeInTheDocument()
    expect(screen.getByText(/4\.0 h/)).toBeInTheDocument()
  })

  it('says so when a route has nobody assigned', () => {
    render(
      <RouteList routes={[summary(1, { driver_name: '' })]} selected={null} onSelect={vi.fn()} />,
    )

    expect(screen.getByText('Unassigned driver')).toBeInTheDocument()
  })

  it('selects a route on click and clears it on a second click', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    const { rerender } = render(
      <RouteList routes={[summary(7)]} selected={null} onSelect={onSelect} />,
    )

    await user.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenCalledWith(7)

    rerender(<RouteList routes={[summary(7)]} selected={7} onSelect={onSelect} />)
    expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'true')

    await user.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenLastCalledWith(null)
  })

  it('gives each route a different colour so the map legend can be read', () => {
    const { container } = render(
      <RouteList routes={[summary(1), summary(2), summary(3)]} selected={null} onSelect={vi.fn()} />,
    )

    const colours = Array.from(container.querySelectorAll<HTMLElement>('.route')).map((el) =>
      el.style.getPropertyValue('--route-color'),
    )
    expect(new Set(colours).size).toBe(3)
  })
})
