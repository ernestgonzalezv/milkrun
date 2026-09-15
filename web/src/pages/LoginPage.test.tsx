import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { tokens } from '../api/tokens'
import { renderWithProviders, jsonResponse } from '../test/utils'

import { LoginPage } from './LoginPage'

describe('sign-in screen', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('stores the tokens when the credentials are good', async () => {
    const user = userEvent.setup()
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) =>
      String(url).includes('/token/')
        ? jsonResponse({ access: 'a1', refresh: 'r1' })
        : jsonResponse({ id: 1, username: 'marta', role: 'dispatcher', full_name: 'Marta C.' }),
    )

    renderWithProviders(<LoginPage />)
    await user.type(screen.getByLabelText('Username'), 'marta')
    await user.type(screen.getByLabelText('Password'), 'secret')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => expect(tokens.access).toBe('a1'))
    expect(tokens.refresh).toBe('r1')
  })

  it('shows the server message when the credentials fail', async () => {
    const user = userEvent.setup()
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ detail: 'No active account found with the given credentials' }, 401),
    )

    renderWithProviders(<LoginPage />)
    await user.type(screen.getByLabelText('Username'), 'marta')
    await user.type(screen.getByLabelText('Password'), 'wrong')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No active account')
    expect(tokens.access).toBeNull()
  })

  it('says something when the server is unreachable instead of going quiet', async () => {
    const user = userEvent.setup()
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'))

    renderWithProviders(<LoginPage />)
    await user.type(screen.getByLabelText('Username'), 'marta')
    await user.type(screen.getByLabelText('Password'), 'secret')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach the server')
  })

  it('leaves no half-written token when sign-in works but /me fails', async () => {
    const user = userEvent.setup()
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) =>
      String(url).includes('/token/')
        ? jsonResponse({ access: 'a1', refresh: 'r1' })
        : jsonResponse({ detail: 'user is inactive' }, 403),
    )

    renderWithProviders(<LoginPage />)
    await user.type(screen.getByLabelText('Username'), 'marta')
    await user.type(screen.getByLabelText('Password'), 'secret')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    await screen.findByRole('alert')
    expect(tokens.access).toBeNull()
  })

  it('disables the button while sending so the request is not duplicated', async () => {
    const user = userEvent.setup()
    let resolve: (r: Response) => void = () => {}
    vi.spyOn(globalThis, 'fetch').mockReturnValue(
      new Promise<Response>((r) => {
        resolve = r
      }),
    )

    renderWithProviders(<LoginPage />)
    await user.type(screen.getByLabelText('Username'), 'marta')
    await user.type(screen.getByLabelText('Password'), 'secret')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('button', { name: 'Signing in…' })).toBeDisabled()
    resolve(jsonResponse({ access: 'a', refresh: 'r' }))
  })
})
