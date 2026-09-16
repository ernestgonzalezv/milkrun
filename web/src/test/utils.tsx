/** Test helpers: mount components with the real providers. */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'
import type { ReactElement, ReactNode } from 'react'

import { AuthProvider } from '../auth/AuthProvider'

export function testClient(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 0 } },
  })
}

export function renderWithProviders(ui: ReactElement, options?: RenderOptions) {
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={testClient()}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    )
  }
  return render(ui, { wrapper: Wrapper, ...options })
}

/** Fake JSON response, so `fetch` boilerplate is not repeated everywhere. */
export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}
