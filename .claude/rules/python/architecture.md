---
paths:
  - "backend/**/*.py"
---

# Backend — Clean Architecture

> **Enforced by `backend/tests/test_architecture.py`**: the domain imports no framework, the
> optimizer imports nothing, views with business rules never touch the ORM, and no use case
> wraps another. If one of those fails, fix the code — never the test.

```
domain/          entities, value objects, policies, ports, use cases. No Django.
infrastructure/  adapters: ORM repositories, the optimizer wrapper, the clock.
apps/            delivery layer: persistence models, serializers, views.
config/container.py   composition root — the only place that picks concrete adapters.
optimizer/       the VRP solver. Pure Python, zero dependencies. See ADR 0004.
```

## Mandatory invariants

- **The domain imports no `django`, no `rest_framework`, no `apps`, no `infrastructure`.**
  Entities are frozen dataclasses; the ORM models are the persistence schema, not the domain.
- **Ports are `typing.Protocol`, not base classes.** Adapters inherit nothing and just satisfy
  the shape, so the domain never appears in an adapter's signature.
- **A use case takes its ports in `__init__` and exposes one `__call__`.** None calls another —
  shared logic goes down to the repository or to `policies.py`.
- **Views do three things**: validate input, invoke a use case, serialize the result. No ORM
  queries, no business rules, no `try` around the use case.
- **Domain errors are business exceptions**, translated to HTTP by the `EXCEPTION_HANDLER` in
  `apps/shared/http.py`. A use case does not know that a 409 exists.
- **Serializers are `Serializer`, not `ModelSerializer`**, because they serialize entities. The
  API shape stops moving when the schema moves.
- **Time comes from the `Clock` port.** No `timezone.now()` inside the domain.

## The documented exception

The fleet catalogues (`DepotViewSet`, `VehicleViewSet`, `DriverProfileViewSet`) stay as
`ModelViewSet` over the ORM. They are CRUD over reference data with no business rules, and
wrapping them would add a layer that only forwards. See ADR 0007. The architecture test excludes
them by name, not by accident. When a depot gains rules, it moves.

## Repositories

- One per aggregate, in `infrastructure/repositories.py`. Every ORM query in the project lives
  there or in the admin.
- Pagination happens in the repository and returns `Page(items, total)`; `apps/shared/http.py`
  builds the DRF-shaped envelope.
- The `_detailed()` queryset is the single definition of "a route loaded whole". Without its
  prefetch, serializing five routes of twenty stops fires ~100 queries.
- Idempotency lives in database constraints, never in a read-then-write check: `exists()` before
  `create()` has a race window, a unique constraint does not.

## Style

- Max line length 100. `ruff check .` must be clean; the same rules apply to tests.
- **Default: no comments.** Add one only when the *why* is non-obvious. Never narrate what the
  code does.
- Code comments and docstrings are in Spanish here, matching the rest of the backend. Do not
  mix languages within a file.
