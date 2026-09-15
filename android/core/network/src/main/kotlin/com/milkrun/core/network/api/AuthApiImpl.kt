package com.milkrun.core.network.api

import com.milkrun.core.network.dto.auth.LoginRequest
import com.milkrun.core.network.dto.auth.TokenPairResponse
import com.milkrun.core.network.dto.auth.UserResponse
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody

class AuthApiImpl(private val client: HttpClient) : AuthApi {

    override suspend fun signIn(request: LoginRequest): TokenPairResponse =
        client.post("/api/v1/auth/token/") { setBody(request) }.body()

    override suspend fun currentUser(): UserResponse = client.get("/api/v1/auth/me/").body()
}
