import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { leg, route, stop } from '../test/fixtures'
import { jsonResponse, renderWithProviders } from '../test/utils'

import { RouteStops } from './RouteStops'

describe('route stops', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('lists the stops in the order the solver chose', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse(route(1, { stops: [leg(1), leg(2), leg(3)] })),
    )

    renderWithProviders(<RouteStops id={1} onFocus={vi.fn()} />)

    await screen.findByText('Customer 1')
    const order = screen.getAllByText(/^[123]$/).map((el) => el.textContent)
    expect(order).toEqual(['1', '2', '3'])
  })

  it('shows distance and ETA for each leg', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse(route(1, { stops: [leg(1, { leg_distance_km: 3.42, eta_minutes: 41.2 })] })),
    )

    renderWithProviders(<RouteStops id={1} onFocus={vi.fn()} />)

    expect(await screen.findByText('3.4 km')).toBeInTheDocument()
    expect(screen.getByText('ETA ~41 min')).toBeInTheDocument()
  })

  it('marks a delivered stop apart from a failed one', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse(
        route(1, {
          stops: [
            leg(1, { stop: stop(1, { status: 'delivered' }) }),
            leg(2, { stop: stop(2, { status: 'failed' }) }),
          ],
        }),
      ),
    )

    const { container } = renderWithProviders(<RouteStops id={1} onFocus={vi.fn()} />)

    await screen.findByText('Customer 1')
    expect(container.querySelectorAll('.stop--done')).toHaveLength(1)
    expect(container.querySelectorAll('.stop--problem')).toHaveLength(1)
  })

  it('asks the map to focus the stop that was clicked', async () => {
    const user = userEvent.setup()
    const onFocus = vi.fn()
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(route(1, { stops: [leg(1)] })))

    renderWithProviders(<RouteStops id={1} onFocus={onFocus} />)

    await user.click(await screen.findByRole('button'))
    expect(onFocus).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }))
  })

  it('says the route could not be loaded instead of rendering nothing', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ detail: 'gone' }, 404))

    renderWithProviders(<RouteStops id={1} onFocus={vi.fn()} />)

    expect(await screen.findByRole('alert')).toHaveTextContent('could not be loaded')
  })
})
