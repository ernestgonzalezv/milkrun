package com.milkrun.feature.auth.domain.repository

import com.milkrun.core.common.model.Resource
import com.milkrun.feature.auth.domain.model.Credentials
import com.milkrun.feature.auth.domain.model.DriverSession
import kotlinx.coroutines.flow.Flow

interface AuthRepository {
    val isSignedIn: Flow<Boolean>

    fun signIn(credentials: Credentials): Flow<Resource<DriverSession>>

    suspend fun signOut()
}
