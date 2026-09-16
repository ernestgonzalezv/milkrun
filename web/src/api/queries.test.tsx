import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { depot, page, route, summary, vehicle } from '../test/fixtures'
import { jsonResponse } from '../test/utils'

import { keys, useDepots, usePlanDay, useRoute, useRoutes, useVehicles } from './queries'

function wrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  })
  return {
    client,
    wrap: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    ),
  }
}

describe('query keys', () => {
  it('separate one date and depot from another, so a switch does not show stale data', () => {
    expect(keys.routes('2026-09-16', 1)).not.toEqual(keys.routes('2026-09-16', 2))
    expect(keys.routes('2026-09-16', 1)).not.toEqual(keys.routes('2026-09-17', 1))
    expect(keys.stops('2026-09-16', undefined)).toEqual(['stops', '2026-09-16', null])
  })
})

describe('data hooks', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('unwraps the paginated envelope so components see a plain list', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(page([depot(1), depot(2)])))
    const { wrap } = wrapper()

    const { result } = renderHook(() => useDepots(), { wrapper: wrap })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(2)
  })

  it('does not ask for vehicles until a depot is chosen', () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    const { wrap } = wrapper()

    renderHook(() => useVehicles(undefined), { wrapper: wrap })

    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('asks for the expanded route list only when the map needs the stops', async () => {
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(jsonResponse(page([summary(1)])))
    const { wrap } = wrapper()

    renderHook(() => useRoutes('2026-09-16', 1), { wrapper: wrap })

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled())
    expect(String(fetchSpy.mock.calls[0]?.[0])).not.toContain('expand=stops')
  })

  it('skips the single route query while nothing is selected', () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    const { wrap } = wrapper()

    renderHook(() => useRoute(null), { wrapper: wrap })

    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('invalidates the day after planning so the panel redraws', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse([route(1)], 201))
    const { client, wrap } = wrapper()
    const invalidate = vi.spyOn(client, 'invalidateQueries')

    const { result } = renderHook(() => usePlanDay('2026-09-16', 1), { wrapper: wrap })
    result.current.mutate(false)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(invalidate).toHaveBeenCalled()
  })
})
