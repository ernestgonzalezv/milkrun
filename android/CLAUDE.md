# Workspace: android

Kotlin + Compose driver app. Multi-module Clean Architecture per feature, Koin for DI, Ktor for
networking, Room + DataStore for persistence.

```
:app                              Koin wiring, navigation, ViewModels, Screens
:core:{common,network,database,storage,ui}
:feature:{auth,route}
```

The app is offline-first and that is the whole point: marking a delivery writes to Room and
returns, and `SyncWorker` uploads when there is signal. Nothing in the UI waits on the network for
something the driver just did.

Toolchain and library versions match `Cococel.Android` on purpose so code stays portable.
**AGP 9.0 rule**: do NOT apply the `kotlin-android` plugin — it is built in.

Rules: `.claude/rules/{kotlin,ktor,compose}/`. Architecture is enforced by
`app/src/test/.../konsist/KonsistArchitectureTest.kt`.

```bash
./gradlew spotlessApply                                   # auto-fix formatting
./gradlew testDebugUnitTest detekt spotlessCheck lintDebug assembleDebug
```
