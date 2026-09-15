---
paths:
  - "backend/tests/**"
---

# Backend testing

- **Framework:** pytest + pytest-django. `make test` or `.venv/bin/python -m pytest`.
- Tests are named as sentences in Spanish: `test_reenviar_la_misma_cola_no_duplica_eventos`.
  The name states the behaviour, not the method under test.

## Three tiers, and which to reach for

| Tier | Where | What it covers | Cost |
|---|---|---|---|
| Domain | `test_domain_*.py` | Policies and use cases against the fakes in `tests/fakes.py`. No database. | milliseconds |
| Optimizer | `test_geo/solver/local_search.py` | Invariants over generated instances. No Django. | milliseconds |
| API | `test_api_*.py` | HTTP status, permissions, response shape, query budgets. | seconds |

**Write the domain test first.** If a rule can be covered without a database, covering it with an
API test instead buys nothing and costs seconds on every run.

## Invariants over examples

The optimizer is tested with properties, not fixed expected outputs — a route plan has too many
degrees of freedom to pin a result. What must hold for *any* input:

- every stop appears exactly once across routes and unassigned;
- no route exceeds its vehicle's capacity or shift;
- local search never lengthens a route;
- the same input produces the same plan.

Where an exact answer is computable, compare against it: with seven stops brute force is 5040
permutations, so `refine` is asserted to reach the true optimum.

## Query budgets

`django_assert_max_num_queries` guards the N+1s that a prefetch removes. If someone deletes the
prefetch, the test says so instead of production doing it.

## Discipline

- Never assert on a number you did not verify. When a constant is wrong, check the maths by hand
  before changing the code — the first haversine test failed because the *expectation* was wrong.
- Rate limiting is real code: isolate it per test by clearing the cache, not by disabling it.
- A test with `or True` in the assertion is worse than no test. Assert the postcondition
  exhaustively or delete it.
