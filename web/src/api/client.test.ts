import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse } from '../test/utils'

import { ApiError, api } from './client'
import { tokens } from './tokens'

describe('cliente de la API', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    tokens.clear()
  })

  it('adjunta el token de acceso si hay sesion', async () => {
    tokens.save({ access: 'abc123' })
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ ok: true }))

    await api.get('/api/v1/auth/me/')

    const [, opciones] = fetchSpy.mock.calls[0]
    const cabeceras = (opciones as RequestInit).headers as Record<string, string>
    expect(cabeceras.Authorization).toBe('Bearer abc123')
  })

  it('no manda cabecera de autorizacion si no hay token', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ ok: true }))

    await api.get('/api/v1/track/ABC123/')

    const [, opciones] = fetchSpy.mock.calls[0]
    const cabeceras = (opciones as RequestInit).headers as Record<string, string>
    expect(cabeceras.Authorization).toBeUndefined()
  })

  it('renueva el token cuando la peticion devuelve 401 y reintenta', async () => {
    tokens.save({ access: 'vencido', refresh: 'refresh-bueno' })
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse({ detail: 'expirado' }, 401))
      .mockResolvedValueOnce(jsonResponse({ access: 'nuevo', refresh: 'refresh-2' }))
      .mockResolvedValueOnce(jsonResponse({ username: 'marta' }))

    const resultado = await api.get<{ username: string }>('/api/v1/auth/me/')

    expect(resultado.username).toBe('marta')
    expect(tokens.access).toBe('nuevo')
    expect(fetchSpy).toHaveBeenCalledTimes(3)
    // El reintento tiene que llevar el token nuevo, no el vencido.
    const [, ultima] = fetchSpy.mock.calls[2]
    const cabecerasReintento = (ultima as RequestInit).headers as Record<string, string>
    expect(cabecerasReintento.Authorization).toBe('Bearer nuevo')
  })

  it('no entra en bucle si el refresh tambien falla', async () => {
    tokens.save({ access: 'vencido', refresh: 'refresh-malo' })
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse({ detail: 'expirado' }, 401))
      .mockResolvedValueOnce(jsonResponse({ detail: 'invalido' }, 401))

    await expect(api.get('/api/v1/auth/me/')).rejects.toBeInstanceOf(ApiError)
    expect(tokens.access).toBeNull()
  })

  it('renueva una sola vez aunque varias peticiones fallen a la vez', async () => {
    // Es el caso real: el dashboard dispara tres consultas al cargar y las
    // tres reciben 401. Como el backend rota el refresh token, tres refresh
    // simultaneos invalidarian los dos ultimos.
    tokens.save({ access: 'vencido', refresh: 'refresh-bueno' })
    let refrescos = 0
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, opciones) => {
      const ruta = String(url)
      if (ruta.includes('/token/refresh/')) {
        refrescos += 1
        return jsonResponse({ access: 'nuevo', refresh: 'r2' })
      }
      const cabeceras = (opciones?.headers ?? {}) as Record<string, string>
      return cabeceras.Authorization === 'Bearer nuevo'
        ? jsonResponse({ ok: true })
        : jsonResponse({ detail: 'expirado' }, 401)
    })

    await Promise.all([
      api.get('/api/v1/stops/'),
      api.get('/api/v1/routes/'),
      api.get('/api/v1/depots/'),
    ])

    expect(refrescos).toBe(1)
  })

  it('traduce el detalle de DRF a un mensaje mostrable', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ detail: 'Solo un despachador puede hacer esta operacion.' }, 403),
    )

    await expect(api.post('/api/v1/routes/plan/')).rejects.toThrow(
      'Solo un despachador puede hacer esta operacion.',
    )
  })

  it('traduce los errores de validacion por campo', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ reason: ['Una entrega fallida necesita motivo.'] }, 400),
    )

    await expect(api.post('/api/v1/me/events/')).rejects.toThrow(
      'reason: Una entrega fallida necesita motivo.',
    )
  })

  it('devuelve null en un 204 sin romper el parseo', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(null, 204))

    await expect(api.get('/api/v1/me/route/')).resolves.toBeNull()
  })

  it('marca los 401 para que la interfaz pueda cerrar la sesion', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({}, 401))

    const fallo = await api.get('/api/v1/stops/').catch((e: unknown) => e)

    expect(fallo).toBeInstanceOf(ApiError)
    expect((fallo as ApiError).isAuth).toBe(true)
  })
})
