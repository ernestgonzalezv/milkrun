# milkrun

Delivery route planning and live tracking. Three surfaces over one API: a Django backend that
owns the VRP solver, a React dashboard for the dispatcher, and an Android app for the driver
that works without coverage.

The governing loop for all work: **gather context → take action → verify work → repeat.**

## What matters here

The core is not the CRUD. It is `backend/optimizer/`: a hand-written VRP solver (Clarke-Wright
savings, 2-opt, Or-opt, cheapest insertion) that plans 400 stops across 26 vehicles in under
half a second. Before changing it, read `docs/adr/0001` and run `make bench` — the benchmark is
the contract, and it reports the regime where the solver does *not* win too.

`make bench-ref` measures it against OR-Tools, which is what a real job would use. That table is
the honest one: with a dimensioned fleet the gap is single-digit, and with a **saturated** fleet
OR-Tools serves 344 stops against 320. Never write "beats OR-Tools" — the claim is bounded to the
strategies and budgets tested, on factory settings.

## Layout

```
backend/     Django 5 + DRF. Clean Architecture: domain/ is framework-free, apps/ is the adapter.
  optimizer/ the VRP solver. Pure Python, zero dependencies, no Django.
web/         React 19 + TypeScript + Vite + TanStack Query + MapLibre.
android/     Kotlin + Compose, multi-module Clean Architecture per feature.
infra/       Terraform for AWS. Written to be read, never applied. See infra/CLAUDE.md.
docs/adr/    the decisions and their costs. Read before arguing with a design.
```

## Tech stack

- **Backend**: Python 3.13, Django 5.2, DRF 3.18, drf-spectacular, pytest, ruff. SQLite in dev,
  Postgres in containers.
- **Web**: React 19, TypeScript 6, Vite 8, TanStack Query 5, MapLibre 6, Vitest, oxlint.
- **Android**: AGP 9.0.0 / Kotlin 2.3.0 / Gradle 9.1.0 / JVM 17 / compileSdk 36 / minSdk 26.
  Koin 4.1.1 (NO Hilt/Dagger), Ktor 3.3.3, Room 2.8.4, DataStore 1.2.0, Compose BOM 2025.12.01.
  JUnit 5 + Mockito-Kotlin + Turbine, Detekt + Spotless + ktlint 1.7.0, Konsist.
  **AGP 9.0 rule**: do NOT apply the `kotlin-android` plugin — it is built in.

The Android toolchain and library versions deliberately match `Cococel.Android` so code stays
portable between both projects.

## Android module structure

```
:app                              shell — Koin wiring, navigation, ViewModels, Screens
:core:{common,network,database,storage,ui}
:feature:{auth,route}
```

Dependency rules: `:feature:*` never depend on each other; `:core:*` never depend on
`:feature:*`; everything may depend on `:core:common`. Enforced by
`app/src/test/.../konsist/KonsistArchitectureTest.kt` — if a Konsist test fails, fix the code,
never the test.

## Where the rules live

Path-scoped rules under `.claude/rules/` load when you touch matching files:

- `rules/kotlin/` — architecture and testing (`**/*.kt`)
- `rules/ktor/` — `:core:network` API and DTO conventions
- `rules/compose/` — design tokens, decomposition, previews, semantics
- `rules/python/` — backend Clean Architecture and testing
- `rules/react/` — dashboard conventions
- `rules/terraform/` — AWS conventions and the traps in `infra/`
- `rules/quality/` — code style and static analysis
- `rules/meta/` — always-on: verification gate, edit safety, failure recovery

## Commands

```bash
make setup                       # venv + python deps + npm install
make migrate && make seed        # a planned day over Havana, already half delivered
make run                         # API on :8000
make web                         # dashboard on :5173
make test                        # backend + dashboard tests
make lint                        # ruff + oxlint + tsc
make bench                       # optimizer benchmark
make bench-ref                   # + the OR-Tools comparison (slow, needs requirements-dev)
make schema                      # regenerate docs/openapi.yml
make android                     # tests, lint and debug APK

cd android && ./gradlew spotlessApply           # auto-fix formatting
cd android && ./gradlew detekt spotlessCheck    # static analysis
```

## Slash commands

- `/verify` — the full pipeline across the four surfaces. Run before claiming anything is done.
- `/review` — review the current changes against this project's rules, not generic best practice.
- `/bench` — run the optimizer benchmark and reconcile it with the README tables.
- `/infra` — validate the Terraform without touching AWS.
- `/schema` — regenerate the OpenAPI schema and classify the drift.
- `/adr` — write the next ADR, cost first.

## Agents

- `backend-reviewer` — Django/DRF against the Clean Architecture boundaries.
- `optimizer-reviewer` — the VRP solver, and whether the published numbers are true.
- `infra-reviewer` — Terraform: exposure, IAM, secrets, cost.
- `test-quality-reviewer` — whether a test would fail if the code were wrong.

## AWS is never applied

`terraform apply`, `terraform destroy`, `aws ecs run-task` and `aws s3 rm` are denied in
`.claude/settings.json`. The account this would run in is borrowed, and the stack exists as
readable code, not as a running system. If a task seems to need them, stop and ask.

## Code quality (always-on)

- Write human-readable code. No robotic comment blocks, no section headers.
- **Default: no comments.** Add one only when the *why* is non-obvious — a hidden constraint, an
  upstream quirk, a workaround tied to a specific bug. Never narrate what the code does.
- Don't over-engineer. If the solution handles a future nobody asked for, strip it back.
- Follow existing patterns. The codebase is a better spec than a description.
- Given a bug report with error output, trace the actual error. Don't guess.

## Known limitations

Documented, not hidden. Distances are haversine with a detour factor and are estimates; the plan
is not optimal and with a saturated fleet it serves fewer stops than OR-Tools; the dashboard
stores the JWT in `localStorage`; Android stores tokens in DataStore without encryption; the
Terraform has never been applied to a real account. Each has an ADR or a README entry explaining
the trade.

That honesty is the point of this repo, not an apology in it. A change that makes a documented
limitation stale without updating it is a regression.
