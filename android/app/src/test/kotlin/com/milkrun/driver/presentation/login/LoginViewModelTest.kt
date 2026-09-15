package com.milkrun.driver.presentation.login

import app.cash.turbine.test
import com.milkrun.core.common.model.ErrorType
import com.milkrun.core.common.model.Resource
import com.milkrun.core.common.model.states.OperationState
import com.milkrun.driver.MainDispatcherExtension
import com.milkrun.driver.R
import com.milkrun.feature.auth.domain.model.Credentials
import com.milkrun.feature.auth.domain.model.DriverRole
import com.milkrun.feature.auth.domain.model.DriverSession
import com.milkrun.feature.auth.domain.usecase.SignInUseCase
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.RegisterExtension
import org.mockito.kotlin.any
import org.mockito.kotlin.mock
import org.mockito.kotlin.never
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

class LoginViewModelTest {

    @JvmField
    @RegisterExtension
    val mainDispatcher = MainDispatcherExtension()

    private lateinit var signIn: SignInUseCase
    private lateinit var viewModel: LoginViewModel

    @BeforeEach
    fun setup() {
        signIn = mock()
        viewModel = LoginViewModel(signIn)
    }

    @Test
    fun `given valid credentials when signing in then it goes Idle to Loading to Success`() = runTest {
        whenever(signIn.invoke(any())).thenReturn(
            flowOf(Resource.Loading, Resource.Success(session())),
        )

        viewModel.state.test {
            assertEquals(OperationState.Idle, awaitItem())
            viewModel.signIn(credentials())
            assertEquals(OperationState.Loading, awaitItem())
            val success = awaitItem() as OperationState.Success
            assertEquals("chofer3", success.data.username)
        }
    }

    @Test
    fun `given bad credentials when signing in then a readable error is surfaced`() = runTest {
        whenever(signIn.invoke(any())).thenReturn(
            flowOf(Resource.Loading, Resource.Error("rejected", ErrorType.UNAUTHORIZED)),
        )

        viewModel.error.test {
            assertNull(awaitItem())
            viewModel.signIn(credentials())
            assertEquals(R.string.error_unauthorized, awaitItem()?.messageRes)
        }
    }

    @Test
    fun `given no connection when signing in then the network message is surfaced`() = runTest {
        whenever(signIn.invoke(any())).thenReturn(
            flowOf(Resource.Loading, Resource.Error("io", ErrorType.NO_INTERNET)),
        )

        viewModel.error.test {
            awaitItem()
            viewModel.signIn(credentials())
            assertEquals(R.string.error_no_internet, awaitItem()?.messageRes)
        }
    }

    @Test
    fun `given incomplete credentials then the use case is never called`() = runTest {
        viewModel.signIn(Credentials(username = "chofer3", password = ""))

        verify(signIn, never()).invoke(any())
    }

    @Test
    fun `given a request in flight then a second submit is ignored`() = runTest {
        whenever(signIn.invoke(any())).thenReturn(flowOf(Resource.Loading))

        viewModel.state.test {
            awaitItem()
            viewModel.signIn(credentials())
            assertEquals(OperationState.Loading, awaitItem())
            viewModel.signIn(credentials())
            expectNoEvents()
        }
    }

    @Test
    fun `given a dismissed error then the form returns to Idle`() = runTest {
        whenever(signIn.invoke(any())).thenReturn(
            flowOf(Resource.Error("rejected", ErrorType.UNAUTHORIZED)),
        )

        viewModel.signIn(credentials())
        mainDispatcher.dispatcher.scheduler.advanceUntilIdle()
        assertTrue(viewModel.state.value is OperationState.Error)

        viewModel.dismissError()

        assertEquals(OperationState.Idle, viewModel.state.value)
        assertNull(viewModel.error.value)
    }

    private fun credentials() = Credentials("chofer3", "milkrun")

    private fun session() = DriverSession(
        id = 3,
        username = "chofer3",
        fullName = "Reinier Castillo",
        role = DriverRole.DRIVER,
    )
}
