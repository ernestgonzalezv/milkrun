package com.milkrun.core.network.api

import com.milkrun.core.network.dto.auth.LoginRequest
import com.milkrun.core.network.dto.auth.TokenPairResponse
import com.milkrun.core.network.dto.auth.UserResponse

interface AuthApi {
    suspend fun signIn(request: LoginRequest): TokenPairResponse

    suspend fun currentUser(): UserResponse
}
