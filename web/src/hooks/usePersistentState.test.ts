import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { usePersistentState } from './usePersistentState'

const asNumber = (raw: string) => {
  const parsed = Number(raw)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null
}

describe('persistent state', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('starts from the fallback when nothing was stored', () => {
    const { result } = renderHook(() => usePersistentState('depot', 0, asNumber))

    expect(result.current[0]).toBe(0)
  })

  it('reads back what a previous session stored', () => {
    localStorage.setItem('depot', '7')

    const { result } = renderHook(() => usePersistentState('depot', 0, asNumber))

    expect(result.current[0]).toBe(7)
  })

  it('falls back when the stored value no longer parses', () => {
    localStorage.setItem('depot', 'not-a-number')

    const { result } = renderHook(() => usePersistentState('depot', 0, asNumber))

    expect(result.current[0]).toBe(0)
  })

  it('writes through so the next reload sees it', () => {
    const { result } = renderHook(() => usePersistentState('depot', 0, asNumber))

    act(() => result.current[1](12))

    expect(result.current[0]).toBe(12)
    expect(localStorage.getItem('depot')).toBe('12')
  })

  it('keeps working when storage throws, as Safari does in private mode', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('denied')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('denied')
    })

    const { result } = renderHook(() => usePersistentState('depot', 3, asNumber))
    expect(result.current[0]).toBe(3)

    act(() => result.current[1](9))
    expect(result.current[0]).toBe(9)
  })
})
