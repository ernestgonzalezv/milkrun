/**
 * Brand mark.
 *
 * The glyph is the product: a route that leaves an origin node, turns, and
 * lands on a destination. It also happens to trace an "L". Drawn on a 32-unit
 * grid so it stays crisp at favicon size, the stroke widths are chosen to
 * survive 16px, which is where most marks fall apart.
 */

import { useId } from 'react'

interface MarkProps {
  size?: number
  /** Flat single-colour version for tight or monochrome contexts. */
  flat?: boolean
}

export function LogoMark({ size = 32, flat = false }: MarkProps) {
  const id = `lt-grad-${useId().replace(/:/g, '')}`

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      {!flat && (
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop stopColor="var(--brand-from)" />
            <stop offset="1" stopColor="var(--brand-to)" />
          </linearGradient>
        </defs>
      )}

      <rect width="32" height="32" rx="9" fill={flat ? 'currentColor' : `url(#${id})`} />

      {/* The leg of the route. Starts clear of the origin node so the stroke
          never cuts through it. */}
      <path
        d="M9.6 12.8 V17.6 a4.6 4.6 0 0 0 4.6 4.6 H18.3"
        stroke="var(--brand-ink)"
        strokeWidth="2.3"
        strokeLinecap="round"
      />

      {/* Origin: hollow, because nothing has happened there yet. */}
      <circle cx="9.6" cy="9.2" r="3" stroke="var(--brand-ink)" strokeWidth="2.3" />

      {/* Destination: solid. The whole product exists to fill this in. */}
      <circle cx="22" cy="22.2" r="3.7" fill="var(--brand-ink)" />
    </svg>
  )
}

interface LogoProps {
  size?: number
  /** Small caption after the word mark, e.g. the current surface. */
  suffix?: string
}

export function Logo({ size = 28, suffix }: LogoProps) {
  return (
    <span className="logo">
      <LogoMark size={size} />
      <span className="logo__word">
        milk<span className="logo__word-accent">run</span>
      </span>
      {suffix && <span className="logo__suffix">{suffix}</span>}
    </span>
  )
}
