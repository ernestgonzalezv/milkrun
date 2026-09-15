# Contributing

Thanks for taking a look. This is a working project, not a demo, so the bar is the same as it
would be on a team.

## The loop

**Gather context → take action → verify work → repeat.** The third step is not optional.

```bash
make lint        # ruff + oxlint + tsc
make test        # backend + dashboard
make android     # Android tests, detekt, spotless, lint
```

CI runs all of that plus Terraform validation. A pull request with a red pipeline will not be
reviewed until it is green.

## Where the rules live

`.claude/rules/` holds path-scoped conventions that apply to whatever you touch — Python
architecture, Kotlin and Compose, React, Terraform, and the always-on ones about verification and
edit safety. They are written for an AI assistant but they are the same rules a human reviewer
applies.

## Things that will get a change sent back

- **Editing an architecture test to make it pass.** `backend/tests/test_architecture.py` and the
  Konsist tests encode the real boundaries. If a change needs one relaxed, that is the discussion,
  not a quiet edit.
- **Assigning `Stop.status` directly.** State is a projection of the event log
  ([ADR 0002](docs/adr/0002-bitacora-append-only-y-estado-proyectado.md)). Writing it by hand
  breaks the guarantee that makes the driver's offline queue safe to resend.
- **Touching the solver without running `make bench`.** The benchmark is the contract. If a number
  in the README moves, update the README in the same change — with figures from a run you did, not
  carried forward.
- **Claiming the solver beats OR-Tools.** The defensible claim is bounded; see the README section
  and keep it that way.
- **A new limitation that is not written down.** The *Known limitations* section is the most
  valuable part of this repo. A change that makes it stale is a regression.

## Comments

Default is none. Add one only when the *why* is not obvious from the code — a hidden constraint, an
upstream quirk, a deliberate trade. Never narrate what the code does.

## Commits

Present tense, imperative, explaining the why when it is not obvious:

```
fix the map container collapsing to zero height

MapLibre stamps .maplibregl-map on the container and its stylesheet sets
position: relative. That sheet ships with the lazily loaded chunk, so it
lands after ours and wins the tie.
```

## Reporting a bug

Include the command you ran, what you expected, and the actual output. For anything involving the
solver, include the seed — every benchmark and test instance is reproducible from one.
