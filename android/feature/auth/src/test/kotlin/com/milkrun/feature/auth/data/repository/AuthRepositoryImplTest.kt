package com.milkrun.feature.auth.data.repository

import app.cash.turbine.test
import com.milkrun.core.common.model.ErrorType
import com.milkrun.core.common.model.Resource
import com.milkrun.core.network.api.AuthApi
import com.milkrun.core.network.dto.auth.TokenPairResponse
import com.milkrun.core.network.dto.auth.UserResponse
import com.milkrun.feature.auth.FakeSession
import com.milkrun.feature.auth.domain.model.Credentials
import com.milkrun.feature.auth.domain.model.DriverRole
import com.milkrun.feature.auth.httpFailure
import io.ktor.http.HttpStatusCode
import java.io.IOException
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.mockito.kotlin.any
import org.mockito.kotlin.mock
import org.mockito.kotlin.whenever

class AuthRepositoryImplTest {

    private lateinit var api: AuthApi
    private lateinit var session: FakeSession
    private lateinit var repository: AuthRepositoryImpl

    @BeforeEach
    fun setup() {
        api = mock()
        session = FakeSession()
        repository = AuthRepositoryImpl(api, session)
    }

    @Test
    fun `given valid credentials when signing in then it emits Loading then Success`() = runTest {
        whenever(api.signIn(any())).thenReturn(TokenPairResponse("access-1", "refresh-1"))
        whenever(api.currentUser()).thenReturn(
            UserResponse(id = 3, username = "chofer3", fullName = "Reinier Castillo", role = "driver"),
        )

        repository.signIn(credentials()).test {
            assertEquals(Resource.Loading, awaitItem())
            val success = awaitItem() as Resource.Success
            assertEquals("chofer3", success.data.username)
            assertEquals(DriverRole.DRIVER, success.data.role)
            awaitComplete()
        }

        assertEquals("access-1", session.accessToken())
    }

    @Test
    fun `given no connection when signing in then it emits Error with NO_INTERNET`() = runTest {
        whenever(api.signIn(any())).thenAnswer { throw IOException("unreachable") }

        repository.signIn(credentials()).test {
            assertEquals(Resource.Loading, awaitItem())
            val error = awaitItem() as Resource.Error
            assertEquals(ErrorType.NO_INTERNET, error.type)
            awaitComplete()
        }
    }

    @Test
    fun `given bad credentials when signing in then it emits Error with UNAUTHORIZED`() = runTest {
        val failure = httpFailure(HttpStatusCode.Unauthorized)
        whenever(api.signIn(any())).thenAnswer { throw failure }

        repository.signIn(credentials()).test {
            assertEquals(Resource.Loading, awaitItem())
            assertEquals(ErrorType.UNAUTHORIZED, (awaitItem() as Resource.Error).type)
            awaitComplete()
        }
    }

    @Test
    fun `given an unexpected failure when signing in then it emits Error with UNKNOWN_ERROR`() = runTest {
        whenever(api.signIn(any())).thenAnswer { throw IllegalStateException("boom") }

        repository.signIn(credentials()).test {
            assertEquals(Resource.Loading, awaitItem())
            assertEquals(ErrorType.UNKNOWN_ERROR, (awaitItem() as Resource.Error).type)
            awaitComplete()
        }
    }

    @Test
    fun `given the token call succeeds but the profile fails then no half session is left`() = runTest {
        val failure = httpFailure(HttpStatusCode.Forbidden)
        whenever(api.signIn(any())).thenReturn(TokenPairResponse("access-1", "refresh-1"))
        whenever(api.currentUser()).thenAnswer { throw failure }

        repository.signIn(credentials()).test {
            awaitItem()
            assertTrue(awaitItem() is Resource.Error)
            awaitComplete()
        }

        assertNull(session.accessToken())
        assertTrue(session.cleared)
    }

    @Test
    fun `given a signed in driver when signing out then the session is cleared`() = runTest {
        val signedIn = AuthRepositoryImpl(api, FakeSession(access = "token"))

        signedIn.signOut()

        signedIn.isSignedIn.test {
            assertEquals(false, awaitItem())
        }
    }

    @Test
    fun `given a repository when observing the session then it reflects the stored token`() = runTest {
        AuthRepositoryImpl(api, FakeSession(access = "token")).isSignedIn.test {
            assertEquals(true, awaitItem())
        }
    }

    private fun credentials() = Credentials("chofer3", "milkrun")
}
