<div align="center">

<img src="docs/img/logo.svg" width="76" alt="">

# milkrun

**Route planning for delivery fleets.
400 stops across 26 vans in under half a second — and the driver keeps working when the signal drops.**

[![CI](https://github.com/ernestgonzalezv/milkrun/actions/workflows/ci.yml/badge.svg)](https://github.com/ernestgonzalezv/milkrun/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-332%20passing-brightgreen.svg)](#development)
[![Solver](https://img.shields.io/badge/solver-zero%20dependencies-8b5cf6.svg)](backend/optimizer)

<img src="docs/img/dashboard.png" alt="The dispatcher dashboard: four routes across New York, planned in 27 ms" width="880">

</div>

---

A *milk run* is one trip that serves many stops. **milkrun works out which stops, in which
order, and which van** — then follows the day as it happens.

The interesting part is not the CRUD. It is [`backend/optimizer/`](backend/optimizer): a vehicle
routing solver written from scratch — Clarke-Wright savings, 2-opt, Or-opt, cheapest insertion —
in pure Python with **zero dependencies**. It plans 400 deliveries across 26 vehicles in **0.45 s**
and drives **16–22% fewer kilometres** than a dispatcher routing by hand.

Everything below that number is measured, reproducible with one command, and reported with the
cases where it loses.

## Run it

Needs Python 3.13, Node 24 and `make`. Nothing else — no API keys, no cloud account, no Docker.

```bash
git clone https://github.com/ernestgonzalezv/milkrun.git
cd milkrun
make setup && make migrate && make seed   # 80 deliveries across New York, already planned
```

Then, in two terminals:

```bash
make run    # API        → http://127.0.0.1:8000
make web    # dashboard  → http://localhost:5173
```

Sign in as `dispatch` / `milkrun`. Press **Re-plan day** and watch the solve time.

| | |
|---|---|
| Interactive API docs | <http://127.0.0.1:8000/api/docs/> |
| Public tracking, no auth | `GET /api/v1/track/{code}/` |
| Other cities | `make seed CITY=chicago` · `la` · `havana` |

## What it is

Three surfaces over one API, each solving a different person's problem.

| Surface | Who | What it does |
|---|---|---|
| **Dashboard** — React 19, MapLibre | the dispatcher | plans the day, watches it happen |
| **Driver app** — Kotlin, Compose | the driver | the day's stops, **works with no signal** |
| **Public tracking** — no auth | the customer | where is my delivery |

The driver app is the reason the architecture looks the way it does. Deliveries get marked in
basements, stairwells and dead zones, so the app writes to a local queue and syncs when the signal
returns. That queue can be resent without duplicating anything — the guarantee lives in a database
constraint, not in a Python `if`. See [ADR 0003](docs/adr/0003-idempotencia-de-la-cola-offline.md).

## The solver

Planning a day is the **vehicle routing problem**: split N stops across K vehicles, respecting
capacity and shift length, minimising distance. Assigning 400 stops to 26 vans has more possible
answers than there are atoms in the universe, so the exact optimum is out of reach and a heuristic
is the only option.

```
1  savings      which stops belong on the same trip      Clarke-Wright
2  consolidate  squeeze the routes into the real fleet
3  local search untangle each route                       2-opt, Or-opt
4  insertion    place whatever was left over              cheapest insertion
```

### Results

Reproducible with `make bench`. Average of 5 instances per row, distances in km.

**Fleet sized to the day's demand** — normal operation:

```
 stops  veh |  plan km  served  km/stop |   NN km  served |  vs NN   vs arrival-order    time
    25    3 |      131      25     5.22 |     163      25 |  19.4%              64.1%     2ms
    50    4 |      183      50     3.66 |     237      50 |  22.3%              72.1%     9ms
   100    8 |      282     100     2.82 |     353     100 |  20.1%              78.1%    30ms
   200   14 |      435     200     2.18 |     547     200 |  20.1%              82.6%   114ms
   400   26 |      704     400     1.76 |     842     400 |  16.3%              85.9%   453ms
```

**Fleet at 80% of demand** — the uncomfortable case:

```
   400   26 |      746     319     2.34 |     763     328 |  -0.6%              82.2%   351ms
```

**That second table is also a result.** Clarke-Wright minimises kilometres; it does not maximise
coverage. When capacity runs short the problem becomes *which stops to serve at all*, and a greedy
baseline competes with it. It is pinned by a test so it cannot quietly get worse.

Two things make these numbers mean something: the baselines run with **the same fleet and the same
constraints**, and improvement is measured **per stop served** — a method that delivers less drives
less, and that does not make it better.

### Against OR-Tools

Baselines are human rivals. To know the real cost of the heuristic it has to be measured against
the industry standard, so `make bench-ref` runs [Google OR-Tools](https://developers.google.com/optimization)
on the same instances.

```
 stops  veh |  milkrun km/stop    time |  OR-Tools km/stop    time |    gap
    50    4 |            3.660    10ms |             3.458   5000ms |  +5.8%
   200   14 |            2.176   117ms |             2.186   5000ms |  -0.4%
   400   26 |            1.760   466ms |             1.873   5000ms |  -6.0%
```

At 400 stops milkrun comes out ahead — and that needed checking, not celebrating. The obvious
explanation is that 5 seconds is not enough for OR-Tools at that size, so it was given more time
and more starting strategies:

```
400 stops — milkrun: 1.756 km/stop in 0.45 s

OR-Tools, growing budget      5s 1.858    15s 1.855    30s 1.818    60s 1.807
OR-Tools, 20s, other starts   PATH_CHEAPEST 1.851   SAVINGS 1.893   CHRISTOFIDES 1.829
```

It is not a time problem: at 60 seconds — 130× the budget — OR-Tools is still 2.8% behind.

**The headline is still not "beats OR-Tools."** Four starting strategies and budgets up to a minute
were tried, all on factory settings; OR-Tools has metaheuristics and LNS parameters that were not
touched, and someone who knows it would likely close and reverse that gap. The defensible claim is
smaller and still useful: **a well-implemented construction heuristic competes with the reference
library three orders of magnitude faster.**

And with a saturated fleet OR-Tools wins where it counts — it serves **344 stops against 320**.

### Against the exact optimum

OR-Tools is a strong reference but still a heuristic. For small instances the optimum can be
*computed*, so it is: [`test_optimizer_properties.py`](backend/tests/test_optimizer_properties.py)
enumerates the entire solution space — every permutation of stops across every partition between
vehicles — and compares against it.

```
capacity to spare, 6-8 stops    gap  0.00%     the plan IS the optimum
capacity tight, 7 stops         gap  2-12%     mean 2.3%, worst 11.8%
```

With room to spare, Clarke-Wright with 2-opt and Or-opt does not land near the optimum — it lands
**on** it. The moment capacity forces the work across vehicles, the question stops being *in which
order* and becomes *what goes with what*, and that is where the heuristic costs something.

The tests assert **equality**, not a bound: tolerating 20% when reality is 0% would not catch a 15%
regression.

## Architecture

```
backend/     Django 5 + DRF. domain/ is framework-free; apps/ is the adapter.
  optimizer/ the solver. Pure Python, zero dependencies, does not import Django.
web/         React 19 + TypeScript + Vite + TanStack Query + MapLibre.
android/     Kotlin + Compose, multi-module Clean Architecture.
infra/       Terraform for AWS. Written to be read — see the note below.
docs/adr/    the decisions and what they cost.
```

Three decisions shape everything else:

**A delivery's state is a projection, not an editable field.** Events are appended to a log and
`status` is derived from it. That is what makes the driver's offline queue safe to resend, and it
means "what did the system know at 3pm" is answerable during a customer dispute.
→ [ADR 0002](docs/adr/0002-bitacora-append-only-y-estado-proyectado.md)

**Idempotency lives in a database constraint.** Not in application code, where two concurrent
syncs race. → [ADR 0003](docs/adr/0003-idempotencia-de-la-cola-offline.md)

**The optimizer does not know Django exists.** It takes dataclasses and returns dataclasses, which
is why the exact-optimum test above can brute-force it without a database.
→ [ADR 0004](docs/adr/0004-optimizador-como-paquete-puro.md)

The boundaries are enforced by tests, not by convention:
[`test_architecture.py`](backend/tests/test_architecture.py) fails if the domain imports a
framework, if a view with business rules touches the ORM, or if a use case wraps another.

## Known limitations

Documented, not hidden. Each one is a decision with its cost in view.

- **Distances are estimates.** Haversine with a 1.35 detour factor, not street distances. Good
  enough to compare routes, not to bill a client for kilometres. The error is worst with a physical
  barrier in between: two points 2 km apart in a straight line can be 12 km apart through a tunnel.
  → [ADR 0006](docs/adr/0006-distancias-geodesicas-con-factor-de-rodeo.md)
- **With a saturated fleet the solver serves fewer stops than OR-Tools** — 320 against 344. What
  would close it is inter-route local search (relocate and swap), which is not there.
- **The dashboard keeps the JWT in `localStorage`**, so an XSS steals it. The right answer in
  production is an `httpOnly` cookie; it is not there because the same backend serves the mobile
  app, where cookies do not apply.
- **Android stores tokens in DataStore unencrypted.** Production would put them behind the Keystore.
- **The Terraform has never been applied to a real AWS account.** It is validated in CI with `fmt`,
  `validate`, `tflint` and `checkov`, with no credentials. `terraform apply` is denied on purpose.
  → [`infra/README.md`](infra/README.md)

## Development

```bash
make test        # 243 backend + 26 dashboard tests
make lint        # ruff + oxlint + tsc
make bench       # optimizer benchmark
make bench-ref   # + the OR-Tools comparison (slow, needs requirements-dev)
make android     # Android tests, detekt, spotless, lint and debug APK
make schema      # regenerate docs/openapi.yml from the code
```

**332 tests green** — 243 backend, 26 dashboard, 63 Android — with ruff, oxlint, tsc, detekt,
spotless and Android lint clean. CI runs all four surfaces plus Terraform validation on every push.

Contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © Ernesto González
