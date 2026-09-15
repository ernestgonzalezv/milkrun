package com.milkrun.core.network.extensions

import com.milkrun.core.common.model.ErrorType
import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respondError
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.request.get
import io.ktor.http.HttpStatusCode
import java.io.IOException
import java.net.SocketTimeoutException
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.CsvSource

/**
 * The failures are produced by a real client so the mapping is exercised against the exception
 * types Ktor actually throws, not against hand-built stand-ins that can drift from them.
 */
class ErrorMappingExtTest {

    @ParameterizedTest(name = "given HTTP {0} when mapping then it is {1}")
    @CsvSource(
        "401, UNAUTHORIZED",
        "403, UNAUTHORIZED",
        "404, NOT_FOUND",
        "400, BUSINESS_ERROR",
        "409, BUSINESS_ERROR",
        "500, NETWORK_ERROR",
        "503, NETWORK_ERROR",
    )
    fun `maps HTTP status codes to error types`(status: Int, expected: ErrorType) = runTest {
        val thrown = failureFrom(HttpStatusCode.fromValue(status))

        assertEquals(expected, thrown.toErrorType())
    }

    @Test
    fun `given an IO failure when mapping then it is NO_INTERNET`() {
        assertEquals(ErrorType.NO_INTERNET, IOException("closed").toErrorType())
        assertEquals(ErrorType.NO_INTERNET, SocketTimeoutException().toErrorType())
    }

    @Test
    fun `given an unexpected failure when mapping then it is UNKNOWN_ERROR`() {
        assertEquals(ErrorType.UNKNOWN_ERROR, IllegalStateException().toErrorType())
    }

    @Test
    fun `given a transport failure then it is retryable and a rejection is not`() {
        assertTrue(ErrorType.NO_INTERNET.isRetryable())
        assertTrue(ErrorType.NETWORK_ERROR.isRetryable())
        assertFalse(ErrorType.BUSINESS_ERROR.isRetryable())
        assertFalse(ErrorType.UNAUTHORIZED.isRetryable())
        assertFalse(ErrorType.NOT_FOUND.isRetryable())
    }

    private suspend fun failureFrom(status: HttpStatusCode): Throwable {
        val client = HttpClient(MockEngine { respondError(status) }) {
            expectSuccess = true
            install(HttpTimeout)
        }
        return runCatching { client.get("http://localhost/probe") }.exceptionOrNull()!!
    }
}
