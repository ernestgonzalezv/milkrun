package com.milkrun.core.storage.session

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.milkrun.core.network.session.SessionTokenProvider
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.sessionDataStore by preferencesDataStore(name = "session")

/**
 * DataStore rather than SharedPreferences: the Ktor `Auth` plugin reads the token from a
 * coroutine on a network dispatcher, and SharedPreferences performs disk I/O on whichever
 * thread calls it without saying so.
 *
 * Known limitation: DataStore does not encrypt. Production should back this with the Keystore.
 */
class SessionStore(private val context: Context) : SessionTokenProvider {

    private val accessKey = stringPreferencesKey("access")
    private val refreshKey = stringPreferencesKey("refresh")

    override val isSignedIn: Flow<Boolean> =
        context.sessionDataStore.data.map { it[accessKey] != null }

    override suspend fun accessToken(): String? = context.sessionDataStore.data.first()[accessKey]

    override suspend fun refreshToken(): String? = context.sessionDataStore.data.first()[refreshKey]

    override suspend fun update(access: String, refresh: String) {
        context.sessionDataStore.edit {
            it[accessKey] = access
            if (refresh.isNotBlank()) it[refreshKey] = refresh
        }
    }

    override suspend fun clear() {
        context.sessionDataStore.edit { it.clear() }
    }
}
