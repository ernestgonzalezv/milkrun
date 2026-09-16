---
paths:
  - "android/core/ui/**"
  - "android/**/presentation/**/*.kt"
---

# Composable decomposition, state and previews

## Decomposition

The public screen Composable composes layout only. Visual atoms are `private @Composable`
functions in the same file, and each reads `MaterialTheme.*` locally rather than accepting
colours or text styles from its parent. That removes prop drilling and makes every atom
independently previewable.

Detekt's `LongMethod` (60 lines) is the tripwire: when a screen body trips it, the fix is to
extract an atom, not to raise the limit.

## State ownership

- **ViewModel owns business state** as `StateFlow`. Screens observe with
  `collectAsStateWithLifecycle()`, never `collectAsState()`.
- **Screens own ephemeral UI state**, text being typed, sheet open, scroll position, via
  `remember`/`rememberSaveable`. Credentials being typed live in the screen, not the ViewModel.
- **Atoms own nothing.** Immutable parameters and callbacks only.
- Never call a ViewModel method from a Composable body. Only from `LaunchedEffect`, a callback,
  or a `rememberCoroutineScope().launch { }`.
- Always give `LazyColumn` items a stable `key = { it.id }`.

## Previews

Every reusable Composable ships `@Preview` entries for its visually distinct states, in the same
file, `private`, wrapped in `MilkrunTheme { }`, with realistic data, never "Lorem ipsum",
which hides truncation bugs. Add a `uiMode = UI_MODE_NIGHT_YES` variant when dark mode differs.
Previews never call `koinViewModel()`; pass a fake state.

## Accessibility

A control is drivable by a screen reader when its node reports both a **role** and a **name**.

- `Modifier.clickable` has no role by default, pass `role = Role.Button`.
- `clickable` does not merge descendants: a `contentDescription` on the inner icon never reaches
  the control. Put the name on the clickable node with `semantics(mergeDescendants = true)` and
  pass `contentDescription = null` to the icon.
- Decorative nodes get `clearAndSetSemantics { }` so the row announces once, not four times.
- Errors that appear in place get `liveRegion = LiveRegionMode.Assertive`, so they are announced
  instead of waiting to be found.
