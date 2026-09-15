import { useAuth } from './auth/useAuth'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'

export function App() {
  const { user, loading } = useAuth()

  // Without this, reloading with a valid session flashes the sign-in screen
  // for an instant before /auth/me/ answers. It looks broken.
  if (loading) return <p className="loading">Restoring your session…</p>

  return user ? <DashboardPage /> : <LoginPage />
}
