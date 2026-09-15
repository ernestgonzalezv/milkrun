import { describe, expect, it } from 'vitest'

import { ROUTE_COLORS, routeColor } from './palette'

describe('route palette', () => {
  it('gives a stable colour for the same index', () => {
    expect(routeColor(3)).toBe(routeColor(3))
  })

  it('does not repeat a colour across a typical fleet', () => {
    const used = Array.from({ length: 8 }, (_, i) => routeColor(i))
    expect(new Set(used).size).toBe(8)
  })

  it('cycles without breaking when there are more routes than colours', () => {
    expect(routeColor(ROUTE_COLORS.length)).toBe(routeColor(0))
    expect(routeColor(99)).toMatch(/^#[0-9A-F]{6}$/i)
  })
})
