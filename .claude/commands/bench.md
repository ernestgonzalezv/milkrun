---
description: Run the optimizer benchmark and check it against the numbers published in the README
---

The benchmark is the contract for `backend/optimizer/`. Any change in there is unverified until
this runs.

1. Run `make bench` (add `--repeticiones N` for a tighter or looser average).
2. Compare every row against the tables in `README.md` under **Resultados**.
3. If a number moved more than ~2%, that is a regression or an improvement, either way it is a
   finding, not noise. Say which rows moved and by how much.
4. If the change is real and intended, **update the README tables with the numbers you just
   measured**. Never carry a figure forward from a previous session.

## When the change touches the solver itself

Also run `make bench-ref` (needs `ortools` from `requirements-dev.txt`). That table is the
honest one: it says where the solver loses.

Two things it must keep saying, because they are true and documented:

- With a dimensioned fleet the gap against OR-Tools is single-digit.
- With a **saturated** fleet the solver serves fewer stops than OR-Tools (320 vs 344 at 400).
  Clarke-Wright minimises kilometres and does not maximise coverage. If a change appears to fix
  this, be suspicious and check that coverage really went up rather than the instance getting
  easier.

Never write "beats OR-Tools" anywhere. The defensible claim is bounded: with the strategies and
budgets tested, and with the library on factory settings. Read the *Qué significan y qué no*
section before describing any result.
