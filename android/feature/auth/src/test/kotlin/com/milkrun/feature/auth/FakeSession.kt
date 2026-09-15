package com.milkrun.feature.auth

import com.milkrun.core.network.session.SessionTokenProvider
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.map

class FakeSession(access: String? = null) : SessionTokenProvider {

    private val state = MutableStateFlow<Pair<String?, String?>>(access to null)

    var cleared: Boolean = false
        private set

    override val isSignedIn: Flow<Boolean> = state.map { it.first != null }

    override suspend fun accessToken(): String? = state.value.first

    override suspend fun refreshToken(): String? = state.value.second

    override suspend fun update(access: String, refresh: String) {
        state.value = access to refresh
    }

    override suspend fun clear() {
        state.value = null to null
        cleared = true
    }
}
