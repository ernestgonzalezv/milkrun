# Workspace: backend

Django 5 + DRF over a Clean Architecture core. `domain/` owns the business and imports no
framework; `infrastructure/` adapts it to the ORM and to `optimizer/`; `apps/` is the delivery
layer; `config/container.py` wires them.

`optimizer/` is the reason this project exists: a hand-written VRP solver with zero dependencies.
Read `docs/adr/0001` and `docs/adr/0004` before touching it, and run `make bench` after.

Rules: `.claude/rules/python/`. Architecture is enforced by `tests/test_architecture.py`.
