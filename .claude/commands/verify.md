---
description: Full verification pipeline — backend, dashboard, Android, infra. Run before claiming done.
---

Run the full pipeline for milkrun. Execute sequentially and **do not stop at the first
failure**: run every stage, collect the failures, then fix them. A green backend hides nothing
if the dashboard does not typecheck.

1. **Backend lint** — `cd backend && .venv/bin/ruff check .`
2. **Backend tests** — `cd backend && .venv/bin/python -m pytest`
3. **Migrations up to date** — `cd backend && .venv/bin/python manage.py makemigrations --check --dry-run`
4. **OpenAPI schema** — `make schema`, then check `docs/openapi.yml` did not change in a way
   nobody asked for. Schema drift is an API break.
5. **Dashboard** — `cd web && npm run lint && npx tsc --noEmit && npm run test:run`
6. **Android** — `cd android && ./gradlew testDebugUnitTest detekt spotlessCheck lintDebug`
7. **Infra** — only if `infra/**` changed, and only if `terraform` is installed:
   `cd infra && terraform fmt -check -recursive && terraform init -backend=false && terraform validate`
   Then `tflint` if available. **Never** `apply` or `destroy`.

For each stage: report PASS/FAIL. On failure, read the actual error to its root cause before
changing anything — do not guess from the stage name.

Finish with a table and the real counts, not remembered ones:

| Stage | Status | Detail |
|---|---|---|
| Backend lint | PASS/FAIL | |
| Backend tests | PASS/FAIL | N passed |
| Migrations | PASS/FAIL | |
| OpenAPI | PASS/FAIL | drift / no drift |
| Dashboard | PASS/FAIL | N passed |
| Android | PASS/FAIL | N passed |
| Infra | PASS/FAIL/SKIP | |

If any number in `README.md` contradicts what you just measured, fix the README in the same pass.
