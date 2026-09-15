import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { App } from './App'
import { ApiError } from './api/client'
import { AuthProvider } from './auth/AuthProvider'
import './styles.css'

const cliente = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // No tiene sentido reintentar un 401 o un 403: el resultado no va a
      // cambiar por insistir. Los fallos de red si.
      retry: (intentos, error) =>
        error instanceof ApiError && error.status < 500 ? false : intentos < 2,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={cliente}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
)
