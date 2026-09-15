import { createContext } from 'react'

import type { User } from '../api/types'

export interface AuthState {
  user: User | null
  loading: boolean
  signIn: (username: string, password: string) => Promise<void>
  signOut: () => void
}

/**
 * Lives in its own file, apart from the provider, for two reasons: React fast
 * refresh only works when a module exports components exclusively, and this
 * way `useAuth` does not have to import the whole provider.
 */
export const AuthContext = createContext<AuthState | null>(null)
