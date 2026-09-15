# Workspace: web

React 19 + TypeScript dashboard for the dispatcher. TanStack Query for server state, MapLibre for
the map, Vitest for tests.

`src/api/` is the only place that speaks HTTP. `src/api/types.ts` mirrors the OpenAPI contract the
backend publishes at `/api/schema/` — when the contract changes, that file changes first.

Rules: `.claude/rules/react/`.
