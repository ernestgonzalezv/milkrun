---
paths:
  - "android/**/src/test/**"
  - "android/**/*Test.kt"
---

# Testing. Android

- **Framework:** JUnit 5 (Jupiter) + Mockito-Kotlin + Turbine. Coroutines via `runTest { }`.
- **Command:** `./gradlew testDebugUnitTest`, or `:feature:<name>:testDebugUnitTest` for one
  module.
- Test files mirror the source path under `src/test/`. Filename is `<Source>Test.kt`.
- `@BeforeEach` to isolate state. No shared mutable globals.

## Naming. Given/When/Then

```kotlin
@Test
fun `given no connection when signing in then it emits Error with NO_INTERNET`() = runTest { }
```

## What to test

| Layer | What you must cover |
|---|---|
| Use case | Each `invoke` path. Verify it forwards repository emissions unchanged. |
| Repository | Every return path produces the right `Resource<T>`, mapped to the right `ErrorType`. |
| Mapper | Round-trip with realistic fixtures. Null/empty/unknown-enum handling. |
| ViewModel | Each public method. Loading → Success/Error transitions, including the initial emission. |
| `*Api` | Over Ktor `MockEngine`: path, method, body and headers. |

## Repositories must cover all three failure shapes

1. `IOException` → `ErrorType.NO_INTERNET`, retryable
2. Rejected by the server (4xx) → `ErrorType.BUSINESS_ERROR`/`UNAUTHORIZED`, **not** retryable
3. `RuntimeException` → `ErrorType.UNKNOWN_ERROR`

## Gotchas learned here

- **Mockito rejects `thenThrow` with a checked exception on a `suspend` function**, the compiled
  signature does not declare it. Use `thenAnswer { throw IOException(...) }`.
- **Do not hand-build Ktor exception types.** `ClientRequestException` reads fields a mock does
  not have and throws NPE. Produce the real one through `MockEngine`, see `httpFailure()`.
- **Main dispatcher**: use the shared `MainDispatcherExtension` (`@RegisterExtension`), not a
  per-class `setUp`. JUnit 5 callbacks take a non-null `ExtensionContext`.

## Flow assertions

Turbine when timing matters, `.toList()` for plain enumeration:

```kotlin
repository.signIn(credentials).test {
    assertEquals(Resource.Loading, awaitItem())
    val success = awaitItem() as Resource.Success
    assertEquals("chofer3", success.data.username)
    awaitComplete()
}
```
