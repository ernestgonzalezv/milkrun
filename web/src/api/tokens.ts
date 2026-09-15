/**
 * Guardado de tokens JWT.
 *
 * Se usa localStorage sabiendo lo que implica: es accesible desde JavaScript,
 * asi que un XSS los roba. La alternativa correcta en produccion es una
 * cookie httpOnly + SameSite emitida por el backend, que este proyecto no
 * implementa porque el backend esta pensado tambien para la app movil, donde
 * las cookies no aplican. Queda documentado en el README como limitacion
 * conocida, no como descuido.
 */

const ACCESS = 'milkrun.access'
const REFRESH = 'milkrun.refresh'

export const tokens = {
  get access(): string | null {
    return localStorage.getItem(ACCESS)
  },
  get refresh(): string | null {
    return localStorage.getItem(REFRESH)
  },
  save(pair: { access: string; refresh?: string }): void {
    localStorage.setItem(ACCESS, pair.access)
    if (pair.refresh) localStorage.setItem(REFRESH, pair.refresh)
  },
  clear(): void {
    localStorage.removeItem(ACCESS)
    localStorage.removeItem(REFRESH)
  },
}
