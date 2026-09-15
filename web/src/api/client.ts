/**
 * Cliente HTTP de la API.
 *
 * Resuelve tres cosas que si se dejan sueltas terminan repetidas en cada
 * componente: adjuntar el token, renovarlo cuando vence, y convertir los
 * errores de DRF en un mensaje que se pueda mostrar.
 */

import { tokens } from './tokens'
import type { TokenPair } from './types'

const BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  readonly status: number
  readonly detail?: unknown

  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }

  /** El servidor rechazo las credenciales o el token vencio sin remedio. */
  get isAuth(): boolean {
    return this.status === 401
  }
}

/**
 * Extrae un mensaje legible de una respuesta de error de DRF.
 *
 * DRF devuelve tres formas distintas segun donde falle: `{detail: "..."}` de
 * los permisos, `{campo: ["error"]}` de la validacion, y a veces una lista
 * suelta. Traducirlas aqui evita que cada pantalla invente su propio parseo.
 */
function messageFrom(status: number, body: unknown): string {
  if (typeof body === 'string' && body) return body
  if (body && typeof body === 'object') {
    const data = body as Record<string, unknown>
    if (typeof data.detail === 'string') return data.detail
    const primero = Object.entries(data)[0]
    if (primero) {
      const [campo, valor] = primero
      const texto = Array.isArray(valor) ? valor.join(' ') : String(valor)
      return campo === 'non_field_errors' ? texto : `${campo}: ${texto}`
    }
  }
  if (status === 401) return 'Usuario o contrasena incorrectos.'
  if (status >= 500) return 'El servidor tuvo un problema. Intenta de nuevo.'
  return `Error ${status}.`
}

async function parse(response: Response): Promise<unknown> {
  if (response.status === 204) return null
  const texto = await response.text()
  if (!texto) return null
  try {
    return JSON.parse(texto)
  } catch {
    return texto
  }
}

/**
 * Renueva el access token. Una sola renovacion en vuelo a la vez: si tres
 * peticiones reciben 401 al mismo tiempo, las tres esperan la misma promesa
 * en vez de disparar tres refresh y invalidarse entre si (el backend rota el
 * refresh token en cada uso).
 */
let renovacionEnCurso: Promise<boolean> | null = null

async function renovar(): Promise<boolean> {
  const refresh = tokens.refresh
  if (!refresh) return false

  renovacionEnCurso ??= (async () => {
    try {
      const r = await fetch(`${BASE}/api/v1/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      })
      if (!r.ok) {
        tokens.clear()
        return false
      }
      tokens.save((await r.json()) as TokenPair)
      return true
    } finally {
      renovacionEnCurso = null
    }
  })()

  return renovacionEnCurso
}

interface RequestOptions {
  method?: string
  body?: unknown
  signal?: AbortSignal
  /** Interno: evita reintentar en bucle si el refresh tambien da 401. */
  reintentado?: boolean
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal, reintentado = false } = options

  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const access = tokens.access
  if (access) headers.Authorization = `Bearer ${access}`

  const response = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  })

  if (response.status === 401 && !reintentado && (await renovar())) {
    return request<T>(path, { ...options, reintentado: true })
  }

  const data = await parse(response)
  if (!response.ok) {
    throw new ApiError(response.status, messageFrom(response.status, data), data)
  }
  return data as T
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { signal }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
