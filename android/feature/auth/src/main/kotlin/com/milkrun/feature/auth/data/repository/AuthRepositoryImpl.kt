package com.milkrun.feature.auth.data.repository

import com.milkrun.core.common.model.Resource
import com.milkrun.core.network.api.AuthApi
import com.milkrun.core.network.dto.auth.LoginRequest
import com.milkrun.core.network.extensions.toErrorType
import com.milkrun.core.network.session.SessionTokenProvider
import com.milkrun.feature.auth.data.mapper.toDomain
import com.milkrun.feature.auth.domain.model.Credentials
import com.milkrun.feature.auth.domain.model.DriverSession
import com.milkrun.feature.auth.domain.repository.AuthRepository
import kotlin.coroutines.cancellation.CancellationException
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import timber.log.Timber

class AuthRepositoryImpl(private val api: AuthApi, private val tokens: SessionTokenProvider) : AuthRepository {

    override val isSignedIn: Flow<Boolean> = tokens.isSignedIn

    override fun signIn(credentials: Credentials): Flow<Resource<DriverSession>> = flow {
        emit(Resource.Loading)
        try {
            val pair = api.signIn(LoginRequest(credentials.username.trim(), credentials.password))
            tokens.update(pair.access, pair.refresh)
            emit(Resource.Success(api.currentUser().toDomain()))
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            // The token is already stored when `currentUser` is what failed. Clearing it keeps
            // the app out of the half-signed-in state where the UI shows the login screen while
            // the Auth plugin still attaches a bearer token.
            tokens.clear()
            val type = e.toErrorType()
            Timber.w(e, "sign-in failed with %s", type)
            emit(Resource.Error(e.message.orEmpty(), type, e))
        }
    }

    override suspend fun signOut() {
        tokens.clear()
    }
}
