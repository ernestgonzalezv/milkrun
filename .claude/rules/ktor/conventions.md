---
paths:
  - "android/core/network/**"
---

# `:core:network` — Ktor conventions

This module owns the shared `HttpClient`, every `*Api` interface, every DTO, and the error
mapping. Nothing else constructs an HTTP client.

## File layout

```
core/network/src/main/kotlin/.../
  client/
    HttpClientFactory.kt       builds the shared client
    MilkrunJson.kt          the single Json configuration
  api/
    <Concept>Api.kt            interface with suspend methods
    <Concept>ApiImpl.kt        implementation over HttpClient
  dto/<concept>/               one DTO per file, filename matches the class
  extensions/ErrorMappingExt.kt
  config/NetworkConfig.kt      interface; implementation provided by :app DI
  session/SessionTokenProvider.kt
```

## Api surface invariants

- Every `*Api` method is `suspend` and returns `Unit` or a typed DTO. Never `Map<String, *>`,
  never raw `JsonElement`.
- Bodies are typed request DTOs. Path and query parameters are typed.
- Base URL comes from `NetworkConfig.baseUrl`, never hardcoded.
- One `*Api` per backend concept (`AuthApi`, `DriverApi`). No mega-interface.
- **A 204 is not an error.** Where the backend answers 204 for "nothing today", the method
  returns `T?` and the impl checks `HttpStatusCode.NoContent` — the caller must be able to tell
  "no route" from "request failed".

## DTO shape

```kotlin
@Serializable
data class RouteStopResponse(
    val id: Int,
    val sequence: Int,
    @SerialName("leg_distance_km") val legDistanceKm: Double,
    val stop: StopResponse,
)
```

- `@Serializable`, all fields `val`, defaults for optional fields, never `var`.
- Keep the backend's field names via `@SerialName`. The wire format is the contract.
- `ignoreUnknownKeys = true` is deliberate: the backend can deploy a field before every phone
  has the app that reads it, and an unknown key must not crash a driver mid-route.

## Auth and plugins

- The single bearer injection lives in the `Auth` plugin inside `HttpClientFactory`. Never add an
  `Authorization` header at a call site.
- `sendWithoutRequest` excludes the token endpoints — those are what mint the token.
  `URLBuilder` exposes `encodedPathSegments`, not `encodedPath`.
- Logging is `LogLevel.INFO`, never `BODY`: request bodies carry tokens and customer data.
- Timeouts are long on purpose (20 s connect, 45 s request). Drivers work on intermittent 2G, and
  cutting at ten seconds turns a slow-but-arriving response into a failed delivery.
- Errors are **not** mapped here. `*Api` methods throw; the consuming repository catches and runs
  `toErrorType()`.

## Testability

`applyMilkrunDefaults()` holds every client setting as an extension on `HttpClientConfig<*>`,
so tests build the same stack over `MockEngine` and exercise the real auth and serialization
behaviour instead of a stand-in.
