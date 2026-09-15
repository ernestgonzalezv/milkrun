---
paths:
  - "**/*.kt"
  - "**/*.kts"
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
---

# Code style

| Surface | Tools | Line length |
|---|---|---|
| Kotlin | detekt + spotless + ktlint 1.7.0 | 120 |
| Python | ruff (E, F, I, N, UP, B, C4, SIM, RUF, DJ) | 100 |
| TypeScript | oxlint + `tsc --noEmit` | — |

## Comments

- **Default: no comments.** Code should read top to bottom.
- Add one ONLY when the *why* is non-obvious: a hidden constraint, an upstream API quirk, a
  workaround tied to a specific bug, or behaviour that would surprise the reader.
- Never narrate *what* the code does — the names already say it.
- Never reference the current task or its callers ("used by X", "added for the Y flow"). That
  belongs in the PR description.
- No section-header comment blocks. If a file needs dividers, it needs splitting.

## Forbidden

- Kotlin: `@Inject`/`@Singleton`/Hilt/Dagger, `println`/`Log.d` (use Timber), `LiveData`,
  `mutableStateOf` in a ViewModel, hardcoded user-facing strings, magic spacing/colour numbers.
- Python: business logic in a view, ORM queries outside `infrastructure/`, `timezone.now()`
  inside the domain, bare `except`.
- Everywhere: a suppression without a comment saying why.

## Suppressions

A disabled rule carries the reason next to it. `disable += "OldTargetApi"` says the SDK pin is
deliberate; `tools:ignore="Typos"` says the flagged word is a username. A silent suppression is
indistinguishable from an oversight six months later.

## Naming

`PascalCase` for types and Composables, `camelCase` for functions and properties,
`SCREAMING_SNAKE_CASE` for top-level constants, `snake_case` in Python. Test files mirror the
source path; the filename matches the primary declaration.
