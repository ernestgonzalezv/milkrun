import { useEffect, useRef, useState } from 'react'
import {
  LngLatBounds,
  MapLibreMap,
  Marker,
  NavigationControl,
  Popup,
  type ErrorEvent,
  type LngLatBoundsLike,
  type StyleSpecification,
} from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

import type { Depot, Route } from '../api/types'

import { routeColor } from './palette'

/**
 * Base map style.
 *
 * OpenFreeMap: vector, no API key, no rate limit, and — the reason it is the
 * default rather than Carto — it serves the style, the tiles, the sprite and
 * the glyphs from a single origin. Carto splits them across
 * `basemaps.cartocdn.com` and `tiles.basemaps.cartocdn.com`, and `cartocdn.com`
 * appears in several ad-blocking filter lists because Carto also sells
 * analytics. A blocked request there does not fail: it hangs, with no error
 * event, which looks exactly like a map that is simply slow.
 *
 * Kept configurable because the right thing in production is to serve your own
 * tiles instead of depending on a third party for the map to appear at all.
 */
const STYLE = import.meta.env.VITE_MAP_STYLE ?? 'https://tiles.openfreemap.org/styles/positron'

/**
 * How long to wait for the remote style before giving up on it.
 *
 * Short on purpose. A dispatcher planning a day does not care which basemap is
 * underneath; they care that the routes are on screen.
 */
const STYLE_TIMEOUT_MS = 6_000

/**
 * Fallback basemap that needs no network at all.
 *
 * A style with a single background layer and no sources fetches nothing: no
 * tiles, no sprite, no glyph ranges. The routes and markers are GeoJSON and DOM
 * elements, so they draw regardless — which means panning, zooming and clicking
 * a stop all keep working with the connection down. Street context is the only
 * thing lost, and that is worth far less than the plan itself.
 *
 * This is the same bet the driver app makes: degrade, never blank.
 */
const OFFLINE_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: 'offline-background',
      type: 'background',
      paint: { 'background-color': '#e7edf5' },
    },
  ],
}

interface Props {
  depot: Depot | null
  routes: Route[]
  highlighted: number | null
  /** A stop the dispatcher asked to see. Changing it flies the map there. */
  focus: { id: number; latitude: number; longitude: number } | null
}

type Phase =
  | { kind: 'booting' }
  | { kind: 'ready' }
  | { kind: 'failed'; reason: string; detail?: string }

/** Which basemap ended up underneath, and why, when it is not the remote one. */
type Basemap = { kind: 'remote' } | { kind: 'offline'; reason: string }

function markerElement(color: string, text: string, depot = false): HTMLElement {
  const node = document.createElement('div')
  node.className = depot ? 'marker marker--depot' : 'marker'
  node.style.setProperty('--route-color', color)
  node.textContent = text
  return node
}

/**
 * Returns why WebGL 2 is unavailable, or null when it works.
 *
 * MapLibre 5+ requires WebGL 2 and throws from the constructor without it.
 * Checking first turns a blank panel into a sentence the user can act on —
 * a map area that renders nothing looks identical to a map area that is
 * simply empty, which is the worst possible failure mode.
 */
let webglAnswer: string | null | undefined

function webglProblem(): string | null {
  if (webglAnswer !== undefined) return webglAnswer
  webglAnswer = probeWebgl()
  return webglAnswer
}

function probeWebgl(): string | null {
  try {
    const probe = document.createElement('canvas')
    const gl = probe.getContext('webgl2')
    if (!gl) {
      return 'This browser did not give us a WebGL 2 context. It is usually hardware acceleration being switched off.'
    }
    return null
  } catch (error) {
    return error instanceof Error ? error.message : String(error)
  }
}

export function MapPanel({ depot, routes, highlighted, focus }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const map = useRef<MapLibreMap | null>(null)
  const markers = useRef<Marker[]>([])
  // The WebGL probe is a pure question about the environment, so it is
  // answered once while initialising state instead of from an effect.
  const [phase, setPhase] = useState<Phase>(() => {
    const problem = webglProblem()
    return problem
      ? { kind: 'failed', reason: 'The map needs WebGL 2', detail: problem }
      : { kind: 'booting' }
  })
  const [basemap, setBasemap] = useState<Basemap>({ kind: 'remote' })
  const [redraws, setRedraws] = useState(0)

  // The map is created once. Recreating it on every render is the number one
  // cause of memory leaks with MapLibre in React.
  useEffect(() => {
    if (!container.current || map.current) return
    if (webglProblem()) return

    let instance: MapLibreMap
    try {
      instance = new MapLibreMap({
        container: container.current,
        style: STYLE,
        center: [-82.3666, 23.1136], // Havana
        zoom: 10.5,
        attributionControl: { compact: true },
      })
    } catch (error) {
      // Reporting a failure of the external system this effect exists to set
      // up is precisely what the rule carves out; there is no render-time
      // value to derive from a constructor that threw.
      // oxlint-disable-next-line react/set-state-in-effect
      setPhase({
        kind: 'failed',
        reason: 'The map could not start',
        detail: error instanceof Error ? error.message : String(error),
      })
      return
    }

    instance.addControl(new NavigationControl({ showCompass: false }), 'top-right')

    let settled = false
    const ready = () => {
      settled = true
      setPhase({ kind: 'ready' })
    }

    // Swapping the style wipes every source and layer, so the draw effect has
    // to run again afterwards. Flipping `phase` back through 'ready' is what
    // retriggers it.
    const fallBackToOffline = (reason: string) => {
      if (settled) return
      settled = true
      setBasemap({ kind: 'offline', reason })
      // `styledata` fires while the new style is still settling, and
      // getStyle() throws on a style that is not done loading. Waiting for
      // isStyleLoaded() is what makes the redraw safe.
      const whenLoaded = () => {
        if (!instance.isStyleLoaded()) return
        instance.off('styledata', whenLoaded)
        setPhase({ kind: 'ready' })
      }
      instance.on('styledata', whenLoaded)
      instance.setStyle(OFFLINE_STYLE)
    }

    instance.on('load', ready)

    // A WebGL context can be lost after it was created: the GPU process
    // restarts, the driver resets, or the browser reclaims it. Every network
    // request still succeeds and the canvas simply goes blank — which is
    // indistinguishable from a map with no data unless it is reported.
    const canvas = instance.getCanvas()
    const onContextLost = (event: Event) => {
      event.preventDefault()
      setPhase({
        kind: 'failed',
        reason: 'The graphics context was lost',
        detail:
          'The browser dropped the WebGL context this map draws into. Hardware acceleration ' +
          'restarting is the usual cause. Reloading the page normally brings it back.',
      })
    }
    canvas.addEventListener('webglcontextlost', onContextLost)

    instance.on('error', (event: ErrorEvent) => {
      const message = String(event.error?.message ?? 'unknown error')
      // Individual tiles fail all the time; that must never blank a map that
      // is already drawing. Only a failure before first load is fatal.
      if (settled) return
      fallBackToOffline(message)
    })

    // A style request that never resolves fires no error event at all, which is
    // exactly the case that used to leave the panel blank with nothing to say.
    const timer = window.setTimeout(
      () => fallBackToOffline(`no response in ${STYLE_TIMEOUT_MS / 1000}s`),
      STYLE_TIMEOUT_MS,
    )

    // MapLibre measures its container once, on construction. This component is
    // loaded lazily inside a Suspense boundary, so that measurement can land
    // while the panel is still 0x0 — and a zero-sized canvas paints nothing,
    // reports no error, and looks exactly like a map that simply has no data.
    // The observer re-measures whenever the panel actually gets its size.
    const observer = new ResizeObserver(() => instance.resize())
    observer.observe(container.current)

    map.current = instance

    return () => {
      window.clearTimeout(timer)
      observer.disconnect()
      canvas.removeEventListener('webglcontextlost', onContextLost)
      instance.remove()
      map.current = null
    }
  }, [])

  // Redraw routes and markers whenever the data changes.
  useEffect(() => {
    const instance = map.current
    if (!instance || phase.kind !== 'ready') return

    // Belt and braces: any path that reaches here before the style is settled
    // would throw on the first getStyle() below. Retry once the map goes idle.
    if (!instance.isStyleLoaded()) {
      const retry = () => {
        instance.off('idle', retry)
        setRedraws((n) => n + 1)
      }
      instance.on('idle', retry)
      // Braces matter: `off` returns the map, and an effect cleanup must
      // return nothing.
      return () => {
        instance.off('idle', retry)
      }
    }

    markers.current.forEach((m) => m.remove())
    markers.current = []

    for (const layer of instance.getStyle().layers ?? []) {
      if (layer.id.startsWith('route-')) instance.removeLayer(layer.id)
    }
    for (const source of Object.keys(instance.getStyle().sources ?? {})) {
      if (source.startsWith('route-')) instance.removeSource(source)
    }

    const bounds = new LngLatBounds()

    if (depot) {
      const point: [number, number] = [depot.longitude, depot.latitude]
      new Marker({ element: markerElement('', 'D', true) })
        .setLngLat(point)
        .setPopup(
          new Popup({ offset: 20 }).setHTML(
            `<div class="popup__title">${depot.name}</div>` +
              `<div class="popup__line">Depot</div>`,
          ),
        )
        .addTo(instance)
        .getElement()
        .setAttribute('aria-label', `Depot ${depot.name}`)
      bounds.extend(point)
    }

    routes.forEach((route, index) => {
      const color = routeColor(index)
      const dimmed = highlighted !== null && highlighted !== route.id
      const points: [number, number][] = route.stops.map((leg) => [
        leg.stop.longitude,
        leg.stop.latitude,
      ])
      if (points.length === 0) return

      // The route leaves the depot and comes back, which is why the line closes there.
      const line: [number, number][] = depot
        ? [[depot.longitude, depot.latitude], ...points, [depot.longitude, depot.latitude]]
        : points

      const id = `route-${route.id}`
      instance.addSource(id, {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: { type: 'LineString', coordinates: line },
        },
      })
      instance.addLayer({
        id,
        type: 'line',
        source: id,
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': color,
          'line-width': dimmed ? 1.5 : 3.2,
          'line-opacity': dimmed ? 0.22 : 0.9,
        },
      })

      route.stops.forEach((leg) => {
        const point: [number, number] = [leg.stop.longitude, leg.stop.latitude]
        const marker = new Marker({
          element: markerElement(color, String(leg.sequence)),
          opacity: dimmed ? '0.3' : '1',
        })
          .setLngLat(point)
          .setPopup(
            new Popup({ offset: 15 }).setHTML(
              `<div class="popup__title">${leg.sequence}. ${leg.stop.customer_name}</div>` +
                `<div class="popup__line">${leg.stop.address}</div>` +
                `<div class="popup__line">${route.vehicle_code} · ETA ~${Math.round(
                  leg.eta_minutes,
                )} min</div>`,
            ),
          )
          .addTo(instance)
        markers.current.push(marker)
        bounds.extend(point)
      })
    })

    if (!bounds.isEmpty()) {
      instance.fitBounds(bounds as LngLatBoundsLike, { padding: 70, maxZoom: 14, duration: 450 })
    }
  }, [depot, routes, highlighted, phase, redraws])

  useEffect(() => {
    const instance = map.current
    if (!instance || phase.kind !== 'ready' || !focus) return

    instance.flyTo({
      center: [focus.longitude, focus.latitude],
      // Not a fixed zoom: yanking the dispatcher from a city overview down to
      // street level loses all context. Only zoom in if we are further out.
      zoom: Math.max(instance.getZoom(), 15),
      duration: 700,
      essential: true,
    })

    const marker = markers.current.find((m) => {
      const at = m.getLngLat()
      return (
        Math.abs(at.lng - focus.longitude) < 1e-9 && Math.abs(at.lat - focus.latitude) < 1e-9
      )
    })
    marker?.togglePopup()
  }, [focus, phase])

  return (
    <div className="map">
      <div ref={container} className="map__canvas" data-testid="map" />

      {phase.kind === 'booting' && (
        <div className="map__status">
          <div className="card map__status-card map__status-card--centred">
            <span className="map__spinner" aria-hidden="true" />
            <p>Loading the base map…</p>
          </div>
        </div>
      )}

      {phase.kind === 'failed' && (
        <div className="map__status" role="alert">
          <div className="card map__status-card">
            <h3>{phase.reason}</h3>
            <p>
              The routes are listed on the left and the plan is unaffected. This panel only draws
              them on a map.
            </p>
            {phase.detail && <code>{phase.detail}</code>}
          </div>
        </div>
      )}

      {/* Not an error state. The plan is fully usable without street context,
          so this is a note, not a blocker. */}
      {phase.kind === 'ready' && basemap.kind === 'offline' && (
        <div className="map__note" title={`${STYLE} — ${basemap.reason}`}>
          <span className="map__note-dot" aria-hidden="true" />
          Offline basemap · streets unavailable
        </div>
      )}

      {phase.kind === 'ready' && routes.length > 0 && (
        <div className="map__legend">
          <h3>Routes</h3>
          {routes.map((route, index) => (
            <div
              key={route.id}
              className="legend__row"
              style={{ ['--route-color' as string]: routeColor(index) }}
            >
              <span className="legend__swatch" aria-hidden="true" />
              <span>{route.vehicle_code}</span>
              <span>{route.planned_distance_km.toFixed(1)} km</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
