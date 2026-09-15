package com.milkrun.core.network.api

import com.milkrun.core.network.FakeSession
import com.milkrun.core.network.TestNetworkConfig
import com.milkrun.core.network.client.applyMilkrunDefaults
import com.milkrun.core.network.dto.auth.LoginRequest
import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.MockRequestHandleScope
import io.ktor.client.engine.mock.respond
import io.ktor.client.engine.mock.respondError
import io.ktor.client.request.HttpRequestData
import io.ktor.client.request.HttpResponseData
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.http.headersOf
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

/**
 * Exercises the real client stack over `MockEngine` rather than stubbing the interface: what
 * needs verifying is which headers leave the device and how the client reacts to status codes,
 * and a mocked interface never runs any of that.
 */
class AuthApiTest {

    private val recorded = mutableListOf<HttpRequestData>()

    private fun client(session: FakeSession, handler: MockRequestHandleScope.(HttpRequestData) -> HttpResponseData) =
        HttpClient(
            MockEngine { request ->
                recorded += request
                handler(request)
            },
        ) {
            applyMilkrunDefaults(TestNetworkConfig(), session)
        }

    @Test
    fun `given a stored token when calling an endpoint then it carries the bearer header`() = runTest {
        val api = AuthApiImpl(
            client(FakeSession(access = "abc123")) {
                respond(
                    content = """{"id":1,"username":"chofer1","role":"driver"}""",
                    headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString()),
                )
            },
        )

        api.currentUser()

        assertEquals("Bearer abc123", recorded.single().headers[HttpHeaders.Authorization])
    }

    @Test
    fun `given a stored token when signing in then the token endpoint carries no bearer header`() = runTest {
        val api = AuthApiImpl(
            client(FakeSession(access = "stale")) {
                respond(
                    content = """{"access":"new","refresh":"r"}""",
                    headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString()),
                )
            },
        )

        api.signIn(LoginRequest("chofer1", "milkrun"))

        assertNull(recorded.single().headers[HttpHeaders.Authorization])
    }

    @Test
    fun `given a 401 when the refresh succeeds then the call is retried with the new token`() = runTest {
        val session = FakeSession(access = "expired", refresh = "good")
        val api = AuthApiImpl(
            client(session) { request ->
                when {
                    request.url.encodedPath.contains("refresh") -> respond(
                        content = """{"access":"fresh","refresh":"r2"}""",
                        headers = headersOf(
                            HttpHeaders.ContentType,
                            ContentType.Application.Json.toString(),
                        ),
                    )

                    request.headers[HttpHeaders.Authorization] == "Bearer fresh" -> respond(
                        content = """{"id":1,"username":"chofer1","role":"driver"}""",
                        headers = headersOf(
                            HttpHeaders.ContentType,
                            ContentType.Application.Json.toString(),
                        ),
                    )

                    else -> respondError(HttpStatusCode.Unauthorized)
                }
            },
        )

        val user = api.currentUser()

        assertEquals("chofer1", user.username)
        assertEquals("fresh", session.accessToken())
        assertTrue(recorded.size >= 3)
    }

    @Test
    fun `given a 401 when the refresh also fails then the session is cleared`() = runTest {
        val session = FakeSession(access = "expired", refresh = "bad")
        val api = AuthApiImpl(client(session) { respondError(HttpStatusCode.Unauthorized) })

        runCatching { api.currentUser() }

        assertTrue(session.cleared)
    }

    @Test
    fun `given an unknown field in the payload when parsing then it is ignored`() = runTest {
        val api = AuthApiImpl(
            client(FakeSession(access = "abc")) {
                respond(
                    content = """{"id":1,"username":"chofer1","role":"driver","future_field":42}""",
                    headers = headersOf(
                        HttpHeaders.ContentType,
                        ContentType.Application.Json.toString(),
                    ),
                )
            },
        )

        assertEquals("chofer1", api.currentUser().username)
    }
}
