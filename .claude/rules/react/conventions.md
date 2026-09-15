---
paths:
  - "web/**/*.ts"
  - "web/**/*.tsx"
---

# Dashboard — React conventions

React 19 + TypeScript + Vite + TanStack Query + MapLibre. `npm run lint`, `npm run typecheck`
and `npm run test:run` must all be clean.

## Layout

```
src/api/         types (mirror of the OpenAPI contract), HTTP client, query hooks
src/auth/        session context — the provider and the context live in separate files
src/components/  presentational pieces
src/pages/       screens
```

## Invariants

- **One HTTP client.** `api/client.ts` attaches the token, renews it on 401 and turns DRF errors
  into a message. No component calls `fetch`.
- **Only one token renewal in flight.** The backend rotates refresh tokens, so three concurrent
  401s must await the same promise or the last two invalidate each other.
- **Query keys are centralized** in `keys`. Invalidating after a mutation is then one line
  instead of a hunt for whoever wrote `['routes']`.
- **Never retry a 4xx.** Insisting will not change the answer. Network failures, yes.
- **Colours come from CSS custom properties** defined once on `:root` and redefined under
  `prefers-color-scheme: dark`. No component writes a literal colour — that is how a dark theme
  ends up forgetting one border.
- **Route colours use the Okabe-Ito palette.** The map encodes route identity *only* by colour,
  and one in twelve people with a Y chromosome cannot separate red from green.
- **Heavy dependencies load lazily.** MapLibre is ~1 MB and is not needed until there is
  something to draw; `React.lazy` keeps it out of the login bundle.

## Tests

Vitest + Testing Library. Cover the client's behaviour (header attachment, refresh, error
translation, 204) and each screen's states, including the failure ones. A metrics panel that only
renders good numbers is not tested until a negative improvement renders too.
