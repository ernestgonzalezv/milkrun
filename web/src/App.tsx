import { useAuth } from './auth/useAuth'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'

export function App() {
  const { user, loading } = useAuth()

  if (loading) return <p className="loading">Restoring your session…</p>

  return user ? <DashboardPage /> : <LoginPage />
}
