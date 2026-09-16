import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { tokens } from '../api/tokens'
import { jsonResponse, renderWithProviders } from '../test/utils'

import { useAuth } from './useAuth'

function Probe() {
  const { user, loading, signOut } = useAuth()
  if (loading) return <p>restoring</p>
  return (
    <div>
      <span>{user ? user.username : 'anonymous'}</span>
      <button type="button" onClick={signOut}>
        out
      </button>
    </div>
  )
}

describe('session', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('starts anonymous with no stored token, without waiting on the network', () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')

    renderWithProviders(<Probe />)

    expect(screen.getByText('anonymous')).toBeInTheDocument()
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('restores a session from a stored token', async () => {
    tokens.save({ access: 'a1', refresh: 'r1' })
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ id: 1, username: 'dispatch', role: 'dispatcher', full_name: 'Marta C.' }),
    )

    renderWithProviders(<Probe />)

    expect(await screen.findByText('dispatch')).toBeInTheDocument()
  })

  it('throws away a token the server no longer accepts', async () => {
    tokens.save({ access: 'stale', refresh: 'stale' })
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ detail: 'expired' }, 401))

    renderWithProviders(<Probe />)

    await waitFor(() => expect(tokens.access).toBeNull())
  })

  it('clears the session on sign out', async () => {
    const user = userEvent.setup()
    tokens.save({ access: 'a1', refresh: 'r1' })
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ id: 1, username: 'dispatch', role: 'dispatcher', full_name: 'Marta C.' }),
    )

    renderWithProviders(<Probe />)
    await screen.findByText('dispatch')

    await user.click(screen.getByRole('button', { name: 'out' }))

    expect(screen.getByText('anonymous')).toBeInTheDocument()
    expect(tokens.access).toBeNull()
  })

  it('refuses to be used outside the provider instead of failing silently', () => {
    const quiet = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => renderWithProviders(<Probe />, { wrapper: ({ children }) => <>{children}</> })).toThrow(
      /must be used inside/,
    )
    quiet.mockRestore()
  })
})
