/**
 * User session.
 *
 * The context exposes the minimum: who is signed in, whether we are still
 * finding out, and how to get in and out. All token mechanics live in
 * api/client.ts; this only decides which screen shows.
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { api, ApiError } from '../api/client'
import { tokens } from '../api/tokens'
import type { TokenPair, User } from '../api/types'

import { AuthContext, type AuthState } from './context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => Boolean(tokens.access))

  useEffect(() => {
    if (!tokens.access) return
    let alive = true
    api
      .get<User>('/api/v1/auth/me/')
      .then((u) => alive && setUser(u))
      .catch(() => tokens.clear())
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [])

  const signIn = useCallback(async (username: string, password: string) => {
    const pair = await api.post<TokenPair>('/api/v1/auth/token/', { username, password })
    tokens.save(pair)
    try {
      setUser(await api.get<User>('/api/v1/auth/me/'))
    } catch (error) {
      tokens.clear()
      throw error instanceof ApiError ? error : new Error('Could not sign in.')
    }
  }, [])

  const signOut = useCallback(() => {
    tokens.clear()
    setUser(null)
  }, [])

  const value = useMemo<AuthState>(
    () => ({ user, loading, signIn, signOut }),
    [user, loading, signIn, signOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
