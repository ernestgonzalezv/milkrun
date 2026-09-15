/**
 * Route colours.
 *
 * This is the Okabe-Ito palette, designed to stay distinguishable under the
 * three common forms of colour blindness. It matters more than it looks: the
 * map encodes route identity *only* by colour, and one in twelve people with a
 * Y chromosome cannot separate red from green. The yellow from the original
 * set is dropped because it lacks contrast on a light background.
 */
export const ROUTE_COLORS = [
  '#0072B2', // blue
  '#D55E00', // vermillion
  '#009E73', // bluish green
  '#CC79A7', // reddish purple
  '#56B4E9', // sky blue
  '#8C6D31', // ochre
  '#7B52AB', // violet
  '#00707A', // teal
] as const

/** Stable colour for a route: the same route always gets the same one. */
export function routeColor(index: number): string {
  return ROUTE_COLORS[index % ROUTE_COLORS.length]
}
