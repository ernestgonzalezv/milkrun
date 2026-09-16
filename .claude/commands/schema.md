---
description: Regenerate the OpenAPI schema and report any drift in the API contract
---

1. Run `make schema`, regenerates `docs/openapi.yml` from the code.
2. Report exactly what changed in the file.
3. Classify every change:
   - **Additive** (new endpoint, new optional field): safe.
   - **Breaking** (removed or renamed field, changed type, new required field, changed status
     code): breaks the dashboard, the Android app, or both. Name which client breaks and where.
4. If `drf-spectacular` emits warnings, fix them at the source. A warning usually means the
   generated TypeScript client will have an unreadable name, that is what `ENUM_NAME_OVERRIDES`
   in `settings.py` exists for.

The schema is generated from the code and never hand-edited. If `docs/openapi.yml` and the code
disagree, the code wins and the file gets regenerated.
