import { screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from './test/utils'

const auth = vi.hoisted(() => ({ value: { user: null, loading: false } }))
vi.mock('./auth/useAuth', () => ({ useAuth: () => auth.value }))
vi.mock('./pages/DashboardPage', () => ({ DashboardPage: () => <p>dashboard</p> }))
vi.mock('./pages/LoginPage', () => ({ LoginPage: () => <p>sign in</p> }))

const { App } = await import('./App')

describe('app shell', () => {
  it('waits while the stored session is being checked', () => {
    auth.value = { user: null, loading: true }
    renderWithProviders(<App />)
    expect(screen.getByText(/restoring/i)).toBeInTheDocument()
  })

  it('shows sign in when nobody is signed in', () => {
    auth.value = { user: null, loading: false }
    renderWithProviders(<App />)
    expect(screen.getByText('sign in')).toBeInTheDocument()
  })

  it('shows the dashboard once there is a user', () => {
    auth.value = { user: { id: 1, username: 'dispatch' }, loading: false } as never
    renderWithProviders(<App />)
    expect(screen.getByText('dashboard')).toBeInTheDocument()
  })
})
