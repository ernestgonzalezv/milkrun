package com.milkrun.core.network.client

import kotlinx.serialization.json.Json

/**
 * `ignoreUnknownKeys` is deliberate: the backend can deploy a new field before the app that
 * reads it reaches every phone, and an unknown key must not crash a driver mid-route.
 */
val MilkrunJson: Json = Json {
    ignoreUnknownKeys = true
    explicitNulls = false
    coerceInputValues = true
}
