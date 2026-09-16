import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { depot, route } from '../test/fixtures'
import { renderWithProviders } from '../test/utils'

import { MapPanel } from './MapPanel'

/**
 * jsdom has no WebGL, so this file can only exercise the path where the map
 * cannot start. That path is worth testing on its own: a panel that renders
 * nothing looks identical to a panel with no data, and the whole point of the
 * failure card is that the two are told apart.
 *
 * The rendering path is verified in a browser instead. See docs/img/dashboard.png.
 */
describe('map panel without WebGL', () => {
  it('says why it cannot draw instead of leaving a blank rectangle', () => {
    renderWithProviders(
      <MapPanel depot={depot()} routes={[route(1)]} highlighted={null} focus={null} />,
    )

    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('WebGL 2')
    expect(alert).toHaveTextContent(/hardware acceleration/i)
  })

  it('points the reader at the route list, which is unaffected', () => {
    renderWithProviders(
      <MapPanel depot={depot()} routes={[route(1)]} highlighted={null} focus={null} />,
    )

    expect(screen.getByRole('alert')).toHaveTextContent(/listed on the left/i)
  })

  it('still mounts a container, so a later resize has something to measure', () => {
    renderWithProviders(<MapPanel depot={null} routes={[]} highlighted={null} focus={null} />)

    expect(screen.getByTestId('map')).toBeInTheDocument()
  })
})
