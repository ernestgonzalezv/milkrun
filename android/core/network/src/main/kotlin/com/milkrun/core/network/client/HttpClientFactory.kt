package com.milkrun.core.network.client

import com.milkrun.core.network.config.NetworkConfig
import com.milkrun.core.network.dto.auth.RefreshRequest
import com.milkrun.core.network.dto.auth.TokenPairResponse
import com.milkrun.core.network.session.SessionTokenProvider
import io.ktor.client.HttpClient
import io.ktor.client.HttpClientConfig
import io.ktor.client.engine.okhttp.OkHttp
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.plugins.auth.Auth
import io.ktor.client.plugins.auth.providers.BearerTokens
import io.ktor.client.plugins.auth.providers.bearer
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.defaultRequest
import io.ktor.client.plugins.logging.LogLevel
import io.ktor.client.plugins.logging.Logger
import io.ktor.client.plugins.logging.Logging
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.request.url
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.URLBuilder
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json
import timber.log.Timber

private const val CONNECT_TIMEOUT_MS = 20_000L
private const val REQUEST_TIMEOUT_MS = 45_000L

private const val AUTH_PATH = "/api/v1/auth/token"

/** The token endpoints must never carry a bearer header: that is what mints it. */
private fun URLBuilder.isAuthEndpoint(): Boolean = encodedPathSegments.containsAll(listOf("auth", "token"))

object HttpClientFactory {

    fun create(config: NetworkConfig, tokens: SessionTokenProvider, json: Json = MilkrunJson): HttpClient =
        HttpClient(OkHttp) {
            applyMilkrunDefaults(config, tokens, json)
        }
}

/**
 * Every client setting lives here so tests can build the same stack over `MockEngine` and
 * exercise the real auth and serialization behaviour instead of a stand-in.
 *
 * Timeouts are longer than a typical mobile app's on purpose. Drivers work on intermittent 2G;
 * cutting at ten seconds turns a slow-but-arriving response into a failed delivery.
 */
fun HttpClientConfig<*>.applyMilkrunDefaults(
    config: NetworkConfig,
    tokens: SessionTokenProvider,
    json: Json = MilkrunJson,
) {
    expectSuccess = true

    defaultRequest {
        url(config.baseUrl)
        contentType(ContentType.Application.Json)
    }

    install(ContentNegotiation) {
        json(json)
    }

    install(HttpTimeout) {
        connectTimeoutMillis = CONNECT_TIMEOUT_MS
        requestTimeoutMillis = REQUEST_TIMEOUT_MS
        socketTimeoutMillis = REQUEST_TIMEOUT_MS
    }

    install(Auth) {
        bearer {
            loadTokens {
                val access = tokens.accessToken() ?: return@loadTokens null
                BearerTokens(access, tokens.refreshToken().orEmpty())
            }
            refreshTokens {
                val refresh = tokens.refreshToken() ?: return@refreshTokens null
                runCatching {
                    client.post("${config.baseUrl}$AUTH_PATH/refresh/") {
                        markAsRefreshTokenRequest()
                        setBody(RefreshRequest(refresh))
                    }.let { json.decodeFromString<TokenPairResponse>(it.bodyAsText()) }
                }.fold(
                    onSuccess = { pair ->
                        tokens.update(pair.access, pair.refresh)
                        BearerTokens(pair.access, pair.refresh)
                    },
                    onFailure = {
                        tokens.clear()
                        null
                    },
                )
            }
            sendWithoutRequest { request -> !request.url.isAuthEndpoint() }
        }
    }

    if (config.isDebug) {
        install(Logging) {
            logger = object : Logger {
                override fun log(message: String) = Timber.tag("Http").d(message)
            }
            // INFO and not BODY: request bodies carry tokens and customer data, and logcat
            // is readable by any app with the right permission on a rooted device.
            level = LogLevel.INFO
        }
    }
}
