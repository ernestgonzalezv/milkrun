---
paths:
  - "android/core/ui/**"
  - "android/**/presentation/**/*.kt"
---

# Design system, token discipline

> **Enforced by Konsist**: raw `Color(0x…)` literals outside `:core:ui` fail the build.

Nothing hardcoded, everything semantic, inherited from the Material 3 theme. If a style is
missing, add it to `:core:ui` first, then consume it.

## Forbidden outside `:core:ui`

- `Color(0xFF…)` or `Color.Red`, raw colour values.
- `TextStyle(...)` with raw `fontSize`/`fontWeight`, or `.copy(fontSize = …)` on a text style.
  That signals a missing role: add it to `AppTypography`.
- `Modifier.padding(8.dp)`, `RoundedCornerShape(16.dp)`, `Modifier.size(34.dp)`, magic numbers.
  Use `AppSpacing.*`, `AppRadius.*`, `AppSize.*`.
- `Icons.Default.<name>`, wrap it in `MilkrunIcons.<role>` first so swapping icon sets later
  does not touch every screen.
- Hardcoded user-facing strings. Use `stringResource` / `pluralStringResource`.

## Tokens that exist

`theme/AppColors.kt` (primitives), `theme/StatusColors.kt` (the `container`/`content` pair per
delivery status, reached through `MaterialTheme.colorScheme.status`), `theme/AppTypography.kt`,
`theme/MilkrunIcons.kt`, `tokens/{AppSpacing,AppRadius,AppSize}.kt`, and `theme/Theme.kt`
which exposes `MilkrunTheme { }`.

## ColorScheme-first

If a value maps to a Material 3 role (primary, surface, onSurface, error, outline), read
`MaterialTheme.colorScheme.<role>`. `AppColors` is the source of *values*; `colorScheme` and
`status` are the source of *meaning*.

## Dynamic colour is off, deliberately

Stop status is communicated by colour, green delivered, red failed, blue pending. Letting
Material You rewrite the palette from the user's wallpaper breaks that code exactly where it
matters most, and the app and the web dashboard share the same tokens so both read as one
product. Do not turn it on without changing how status is communicated first.

## Plurals

Spanish agreement breaks silently when a count is interpolated into a fixed sentence
("1 entrega guardadas"). Any string carrying a count is a `<plurals>`, not a `<string>`.
