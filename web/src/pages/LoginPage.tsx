import { useState, type FormEvent } from 'react'

import { ApiError } from '../api/client'
import { useAuth } from '../auth/useAuth'
import { Logo } from '../components/Logo'

const DEMO = { username: 'despacho', password: 'milkrun' }

export function LoginPage() {
  const { signIn } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [sending, setSending] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSending(true)
    try {
      await signIn(username.trim(), password)
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : 'Could not reach the server.')
    } finally {
      setSending(false)
    }
  }

  return (
    <main className="signin">
      <aside className="signin__aside">
        <svg className="signin__grid" aria-hidden="true">
          <defs>
            <pattern id="signin-dots" width="26" height="26" patternUnits="userSpaceOnUse">
              <circle cx="1.5" cy="1.5" r="1.5" fill="currentColor" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#signin-dots)" />
        </svg>

        <Logo size={32} />

        <div className="signin__pitch">
          <h2>Every van leaves with the shortest day already planned.</h2>
          <p>
            Four hundred stops across twenty-six vehicles, solved in under half a second — and the
            driver keeps working when the signal drops.
          </p>
        </div>

        <div className="signin__stats">
          <div className="signin__stat">
            <strong>16–22%</strong>
            <span>fewer kilometres than manual routing</span>
          </div>
          <div className="signin__stat">
            <strong>0.45 s</strong>
            <span>to plan 400 stops</span>
          </div>
        </div>
      </aside>

      <section className="signin__main">
        <form className="card signin__form" onSubmit={onSubmit}>
          <div className="signin__head">
            <Logo size={30} suffix="dispatch" />
            <h1>Sign in</h1>
            <p>Plan the day, watch it happen.</p>
          </div>

          <label className="field">
            <span>Username</span>
            <input
              name="username"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>

          {/* role="alert" so a screen reader announces the failure instead of
              leaving the user to go looking for it. */}
          {error && (
            <p className="alert alert--error" role="alert">
              <span className="alert__dot" aria-hidden="true" />
              {error}
            </p>
          )}

          <button className="btn btn--block" type="submit" disabled={sending}>
            {sending ? 'Signing in…' : 'Sign in'}
          </button>

          <div className="signin__demo">
            <span>
              Demo · <code>{DEMO.username}</code> / <code>{DEMO.password}</code>
            </span>
            <button
              type="button"
              className="signin__fill"
              onClick={() => {
                setUsername(DEMO.username)
                setPassword(DEMO.password)
              }}
            >
              Fill
            </button>
          </div>
        </form>
      </section>
    </main>
  )
}
