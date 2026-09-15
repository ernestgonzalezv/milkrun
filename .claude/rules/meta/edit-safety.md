# Edit safety (always on)

## Before editing

- Read the file. Study the code nearby before writing — the codebase is a better spec than any
  description, and matching its idiom matters more than personal preference.
- Before deleting or overwriting anything, look at what is there.

## Destructive operations

- Never wipe local state that represents work: the Room database holds deliveries that have not
  reached the server, which is why `fallbackToDestructiveMigration` is absent by design. When a
  schema rename breaks it in development, uninstall the app — do not "fix" it by letting Room
  drop the table.
- Do not commit or push unless asked.
- Caches that can be rebuilt locally are fair game to delete; caches that would be re-downloaded
  from the network are not.

## When something goes wrong

- Trace the actual error. Read the stack trace to its root cause before changing a line.
- If two attempts fail the same way, stop and re-plan rather than forcing a third.
- A failing check is information. `LongMethod` firing on a screen body means extract a composable,
  not raise the limit.
