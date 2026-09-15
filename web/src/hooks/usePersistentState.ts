import { useCallback, useState } from 'react'

/**
 * State that survives a reload.
 *
 * Used for the dispatcher's depot: they work the same warehouse every morning,
 * and making them pick it again after every refresh is the kind of small
 * friction that makes a tool feel unfinished.
 *
 * Reads and writes are guarded because Safari throws from localStorage in
 * private mode rather than returning null, and losing the whole dashboard over
 * a remembered preference would be a bad trade.
 */
export function usePersistentState<T>(
  key: string,
  initial: T,
  parse: (raw: string) => T | null,
): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = window.localStorage.getItem(key)
      if (raw === null) return initial
      return parse(raw) ?? initial
    } catch {
      return initial
    }
  })

  const store = useCallback(
    (next: T) => {
      setValue(next)
      try {
        window.localStorage.setItem(key, String(next))
      } catch {
        // Not being able to remember is not a reason to fail the interaction.
      }
    },
    [key],
  )

  return [value, store]
}
