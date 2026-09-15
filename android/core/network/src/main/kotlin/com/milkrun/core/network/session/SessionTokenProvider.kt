package com.milkrun.core.network.session

import kotlinx.coroutines.flow.Flow

/**
 * Read/write access to the stored session. It lives here because the Ktor `Auth` plugin needs
 * it, while the storage implementation belongs to `:core:storage` — so no feature module has to
 * depend on the storage layer just to know whether someone is signed in.
 */
interface SessionTokenProvider {
    val isSignedIn: Flow<Boolean>

    suspend fun accessToken(): String?

    suspend fun refreshToken(): String?

    suspend fun update(access: String, refresh: String)

    suspend fun clear()
}
