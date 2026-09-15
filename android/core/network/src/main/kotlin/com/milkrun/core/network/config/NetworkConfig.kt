package com.milkrun.core.network.config

/**
 * Values that change per build variant. The implementation is provided by `:app` DI so that
 * `:core:network` never reads `BuildConfig` of a module it does not own.
 */
interface NetworkConfig {
    val baseUrl: String
    val isDebug: Boolean
}
