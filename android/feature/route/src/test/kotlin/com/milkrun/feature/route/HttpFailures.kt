package com.milkrun.feature.route

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respondError
import io.ktor.client.request.get
import io.ktor.http.HttpStatusCode

/**
 * Builds the exception Ktor actually throws for a status code. Stubbing the type by hand drifts
 * from the real one, and the mapping under test reads fields that a hand-built instance lacks.
 */
suspend fun httpFailure(status: HttpStatusCode): Throwable {
    val client = HttpClient(MockEngine { respondError(status) }) { expectSuccess = true }
    return runCatching { client.get("http://localhost/probe") }.exceptionOrNull()!!
}
