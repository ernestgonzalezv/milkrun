# Verification gate (always on)

Never report work as done without proving it ran. The loop is
**gather context → take action → verify work → repeat**, and the third step is not optional.

## What "verified" means per surface

| Change | Minimum proof |
|---|---|
| Backend | `pytest` green + `ruff check .` clean + the schema generates without warnings |
| Dashboard | `npm run test:run`, `npm run typecheck`, `npm run lint`, `npm run build` |
| Android | `./gradlew testDebugUnitTest detekt spotlessCheck lintDebug assembleDebug` |
| Anything user-visible | run it and look at it — install the APK, open the screen, read the log |

## Rules

- A compile is not a test. A test passing is not the feature working.
- When you change behaviour a user can see, drive the real thing: install on the emulator, tap
  through the flow, read logcat. The offline queue was only proven by turning on airplane mode.
- Report failures with their output. Never say "should work".
- If part of the work is blocked, finish everything else and say exactly what was left and why.
- When a number appears in a README or a report, it came from a command you ran in this session.
  Never copy a benchmark figure forward after changing the code that produces it.

## Corrections

If you find your own error, state it in a sentence and fix it. Do not narrate the mistake, do not
apologise twice, and do not re-audit statements that were already correct.
