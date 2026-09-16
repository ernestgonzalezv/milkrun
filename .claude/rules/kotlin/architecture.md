---
paths:
  - "android/**/*.kt"
---

# Kotlin / Android architecture

> **Enforced by Konsist** (`app/src/test/.../konsist/KonsistArchitectureTest.kt`): domain purity,
> feature isolation, Koin-only DI, no LiveData, immutable ViewModel state, single-invoke use
> cases, no DTOs in presentation. If a Konsist test fails, fix the code, never the test.

Clean Architecture per feature module with four layers: **presentation (`:app/presentation/`) →
ViewModel → use case → repository → data source**. Never skip layers.

## Mandatory invariants

- **Per-feature folder layout:**
  ```
  feature/<name>/
    data/     repository/ + mapper/
    domain/   model/ + repository/ (interface) + usecase/
    di/       <Name>Module.kt (Koin)
  ```
- **Presentation lives in `:app/presentation/`** (Screens + ViewModels). Feature modules carry no
  Compose code.
- **Domain has zero Android imports.** No `androidx.*`, no `android.*`, no Compose, no Koin, no
  Ktor, no Room. Pure Kotlin plus `kotlinx.coroutines.flow` and `java.time`.
- **State via ViewModel + `StateFlow`.** No `LiveData`. No `mutableStateOf` owned by a ViewModel. Compose state is screen-scoped only.
- **DI via Koin** (`single`, `factory`, `viewModel`). No Hilt, no Dagger, no `@Inject`. Each
  feature exposes one `<Name>Module.kt` in `di/`; `:app` splits its graph across
  `di/{App,Network,ViewModel}Module.kt`.
- **All HTTP goes through Ktor `*Api` interfaces** in `:core:network`. Never build an
  `HttpClient` in feature code.
- **Errors: `Resource<T>`** (`Loading | Success | Error(message, type, exception)`) from
  `:core:common.model`. Repositories emit `Flow<Resource<T>>` and never throw across the
  boundary. Map exceptions with `Throwable.toErrorType()`
  (`:core:network/extensions/ErrorMappingExt.kt`).
- **Repositories produce no user-facing text.** They classify the failure into an `ErrorType`;
  `UiError.fromErrorType()` in `:app/presentation/model/` resolves the wording from string
  resources. Translations live with the strings, not in the data layer.
- **Navigation routes are a `sealed class Screen(val route: String)`** in
  `app/.../core/navigation/Screen.kt`. Never `navController.navigate("raw string")`.

## ViewModel conventions

- Private mutable, public immutable:
  ```kotlin
  private val _state = MutableStateFlow<OperationState<RouteUiModel>>(OperationState.Loading)
  val state: StateFlow<OperationState<RouteUiModel>> = _state.asStateFlow()
  ```
- Flow chains from use cases use `.onEach { }.launchIn(viewModelScope)`.
- One `OperationState<T>` per concern. Errors that the screen can dismiss without losing the
  operation go in a separate `StateFlow<UiError?>`.
- The UI never waits on the network for something the driver just did. Record locally, return,
  and let the sync happen after.

## Use case conventions

- One class per use case, single responsibility. `operator fun invoke(...)`, `Flow<Resource<T>>`
  for streams, `suspend` for one-shot.
- **No default parameter values.** A use case named `ObserveTodaysRouteUseCase` takes no date: it
  injects the `Clock`. Defaults that call into an injected collaborator make the class
  effectively unmockable.
- No use case wraps another. Shared logic belongs in the repository.

## Repository conventions

- Interface in `domain/repository/`, implementation in `data/repository/`.
- Always `try { } catch (e: CancellationException) { throw e } catch (e: Exception) { }`.
- Map DTO → domain via extension functions in `data/mapper/`. Private for nested mappers.
- Depend on the narrowest interface available. Repositories take DAOs, not the database.

## Cross-module rules

- `:feature:*` never depend on each other.
- `:core:*` never depend on `:feature:*`.
- Everything may depend on `:core:common`.
- Use `api()` only for types that appear in a module's public contract, `:core:network` exposes
  `ktor-client-core` that way because repositories catch Ktor's exception types by design.
