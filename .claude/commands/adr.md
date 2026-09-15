---
description: Write a new ADR in docs/adr/ following the existing format
---

Create the next ADR. Read two or three existing ones in `docs/adr/` first — match their voice,
length and structure exactly rather than importing a template.

Number it as the next free integer, filename `NNNN-titulo-en-kebab-case.md`.

The point of an ADR here is **the cost**, not the choice. An ADR that only says what was decided
is worthless; the ones in this repo are useful because they say what was given up. Cover:

- The forces in tension, honestly stated — including the option that was nearly chosen.
- The decision.
- What it costs, concretely. If there is no cost, either it is not a decision worth an ADR, or
  the cost has not been found yet.
- What would make you reverse it.

If the decision introduces a limitation a user could hit, add it to **Limitaciones conocidas** in
`README.md` in the same pass and link the ADR. A limitation that only lives in an ADR is hidden.
