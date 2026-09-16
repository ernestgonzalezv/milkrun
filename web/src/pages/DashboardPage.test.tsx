import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { depot, page, route, stop, summary, vehicle } from '../test/fixtures'
import { jsonResponse, renderWithProviders } from '../test/utils'

vi.mock('../components/MapPanel', () => ({
  MapPanel: ({ focus }: { focus: { id: number } | null }) => (
    <div data-testid="map-stub">{focus ? `focus:${focus.id}` : 'no-focus'}</div>
  ),
}))

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({
    user: { id: 1, username: 'dispatch', full_name: 'Marta Cabrera', role: 'dispatcher' },
    loading: false,
    signIn: vi.fn(),
    signOut: vi.fn(),
  }),
}))

const { DashboardPage } = await import('./DashboardPage')

function api({ routes = [summary(1), summary(2)], stops = [stop(1)] } = {}) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) => {
    const u = String(url)
    if (u.includes('/depots/')) return jsonResponse(page([depot(1), depot(2, 'Pilsen Freight Terminal')]))
    if (u.includes('/vehicles/')) return jsonResponse(page([vehicle(1), vehicle(2), vehicle(3)]))
    if (u.includes('/stops/')) return jsonResponse(page(stops))
    const single = u.match(/\/routes\/(\d+)\//)
    if (single) return jsonResponse(route(Number(single[1])))
    if (u.includes('expand=stops')) return jsonResponse(page([route(1), route(2)]))
    if (u.includes('/routes/')) return jsonResponse(page(routes))
    return jsonResponse({})
  })
}

describe('dispatcher dashboard', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('shows the routes of the selected depot', async () => {
    api()
    renderWithProviders(<DashboardPage />)

    expect(await screen.findByText('NYC-VAN-01')).toBeInTheDocument()
    expect(screen.getByText('NYC-VAN-02')).toBeInTheDocument()
  })

  it('remembers the depot across reloads', async () => {
    const user = userEvent.setup()
    api()
    const { unmount } = renderWithProviders(<DashboardPage />)

    await screen.findByText('NYC-VAN-01')
    await user.selectOptions(screen.getByRole('combobox'), '2')
    await waitFor(() => expect(localStorage.getItem('milkrun.depot')).toBe('2'))

    unmount()
    renderWithProviders(<DashboardPage />)
    await waitFor(() =>
      expect(screen.getByRole('combobox')).toHaveValue('2'),
    )
  })

  it('offers to plan the day when nothing is planned yet', async () => {
    api({ routes: [] })
    renderWithProviders(<DashboardPage />)

    expect(await screen.findByRole('button', { name: 'Plan the day' })).toBeInTheDocument()
  })

  it('offers to re-plan once routes exist', async () => {
    api()
    renderWithProviders(<DashboardPage />)

    expect(await screen.findByRole('button', { name: 'Re-plan day' })).toBeInTheDocument()
  })

  it('lists stops that did not fit the fleet', async () => {
    api({ stops: [stop(1, { status: 'pending' }), stop(2, { status: 'planned' })] })
    renderWithProviders(<DashboardPage />)

    expect(await screen.findByText('Unassigned')).toBeInTheDocument()
    expect(screen.getByText('no room in the fleet')).toBeInTheDocument()
  })

  it('opens the stops of a route when it is selected', async () => {
    const user = userEvent.setup()
    api()
    renderWithProviders(<DashboardPage />)

    await user.click(await screen.findByText('NYC-VAN-01'))
    expect(await screen.findByText('Stops on this route')).toBeInTheDocument()
  })

  it('clears the selection with Escape', async () => {
    const user = userEvent.setup()
    api()
    renderWithProviders(<DashboardPage />)

    await user.click(await screen.findByText('NYC-VAN-01'))
    await screen.findByText('Stops on this route')

    await user.keyboard('{Escape}')
    await waitFor(() =>
      expect(screen.queryByText('Stops on this route')).not.toBeInTheDocument(),
    )
  })

  it('shows the dispatcher initials rather than a broken avatar', async () => {
    api()
    renderWithProviders(<DashboardPage />)

    expect(await screen.findByText('MC')).toBeInTheDocument()
  })
})
