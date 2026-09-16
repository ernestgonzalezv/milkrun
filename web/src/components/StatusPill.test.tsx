import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { StopStatus } from '../api/types'

import { StatusPill } from './StatusPill'

const EVERY: StopStatus[] = ['pending', 'planned', 'in_transit', 'delivered', 'failed', 'cancelled']

describe('status pill', () => {
  it.each(EVERY)('renders a label and a modifier class for %s', (status) => {
    const { container } = render(<StatusPill status={status} />)

    expect(container.querySelector(`.pill--${status}`)).toBeInTheDocument()
    expect(screen.getByText(/\w/)).toBeInTheDocument()
  })

  it('never shows a raw status code to the user', () => {
    for (const status of EVERY) {
      const { container, unmount } = render(<StatusPill status={status} />)
      expect(container.textContent).not.toBe(status)
      unmount()
    }
  })
})
