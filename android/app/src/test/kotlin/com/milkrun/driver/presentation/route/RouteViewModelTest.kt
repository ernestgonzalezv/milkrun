package com.milkrun.driver.presentation.route

import app.cash.turbine.test
import com.milkrun.core.common.model.Resource
import com.milkrun.core.common.model.SyncOutcome
import com.milkrun.core.common.model.states.OperationState
import com.milkrun.driver.MainDispatcherExtension
import com.milkrun.feature.auth.domain.usecase.SignOutUseCase
import com.milkrun.feature.route.domain.model.Coordinates
import com.milkrun.feature.route.domain.model.DeliveryOutcome
import com.milkrun.feature.route.domain.model.DeliveryRoute
import com.milkrun.feature.route.domain.model.RouteStop
import com.milkrun.feature.route.domain.model.Stop
import com.milkrun.feature.route.domain.model.StopStatus
import com.milkrun.feature.route.domain.usecase.ObservePendingWorkUseCase
import com.milkrun.feature.route.domain.usecase.ObserveTodaysRouteUseCase
import com.milkrun.feature.route.domain.usecase.RecordDeliveryOutcomeUseCase
import com.milkrun.feature.route.domain.usecase.RefreshRouteUseCase
import com.milkrun.feature.route.domain.usecase.SyncPendingWorkUseCase
import java.time.LocalDate
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.RegisterExtension
import org.mockito.kotlin.any
import org.mockito.kotlin.mock
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

class RouteViewModelTest {

    @JvmField
    @RegisterExtension
    val mainDispatcher = MainDispatcherExtension()

    private val routes = MutableStateFlow<DeliveryRoute?>(null)
    private val pending = MutableStateFlow(0)

    private lateinit var observeTodaysRoute: ObserveTodaysRouteUseCase
    private lateinit var observePendingWork: ObservePendingWorkUseCase
    private lateinit var refreshRoute: RefreshRouteUseCase
    private lateinit var recordOutcome: RecordDeliveryOutcomeUseCase
    private lateinit var syncPendingWork: SyncPendingWorkUseCase
    private lateinit var signOut: SignOutUseCase

    @BeforeEach
    fun setup() {
        observeTodaysRoute = mock()
        observePendingWork = mock()
        refreshRoute = mock()
        recordOutcome = mock()
        syncPendingWork = mock()
        signOut = mock()

        whenever(observeTodaysRoute.invoke()).thenReturn(routes)
        whenever(observePendingWork.invoke()).thenReturn(pending)
        whenever(refreshRoute.invoke()).thenReturn(flowOf(Resource.Success(Unit)))
        whenever(syncPendingWork.invoke()).thenReturn(
            flowOf(Resource.Success(SyncOutcome.NothingPending)),
        )
    }

    private fun viewModel() = RouteViewModel(
        observeTodaysRoute = observeTodaysRoute,
        observePendingWork = observePendingWork,
        refreshRoute = refreshRoute,
        recordOutcome = recordOutcome,
        syncPendingWork = syncPendingWork,
        signOutUseCase = signOut,
    )

    @Test
    fun `given no route for today then the empty case is exposed instead of an error`() = runTest {
        viewModel().state.test {
            assertEquals(OperationState.Loading, awaitItem())
            val state = awaitItem() as OperationState.Success
            assertEquals(RouteUiModel.NoRouteToday, state.data)
        }
    }

    @Test
    fun `given an assigned route then the stops reach the screen`() = runTest {
        routes.value = route()

        viewModel().state.test {
            awaitItem()
            val assigned = (awaitItem() as OperationState.Success).data as RouteUiModel.Assigned
            assertEquals("CAM-03", assigned.route.vehicleCode)
            assertEquals(2, assigned.route.stops.size)
        }
    }

    @Test
    fun `given a refresh failure then the screen is flagged offline`() = runTest {
        whenever(refreshRoute.invoke()).thenReturn(
            flowOf(Resource.Error("io", com.milkrun.core.common.model.ErrorType.NO_INTERNET)),
        )

        val vm = viewModel()
        mainDispatcher.dispatcher.scheduler.advanceUntilIdle()

        assertFalse(vm.sync.value.online)
    }

    @Test
    fun `given queued work then the pending counter reaches the screen`() = runTest {
        val vm = viewModel()

        vm.sync.test {
            assertEquals(0, awaitItem().pending)
            pending.value = 3
            assertEquals(3, awaitItem().pending)
        }
    }

    @Test
    fun `given a delivery when recording then it is queued and the sheet closes`() = runTest {
        val vm = viewModel()
        vm.openStop(12)

        vm.record(DeliveryOutcome.Delivered(12))
        mainDispatcher.dispatcher.scheduler.advanceUntilIdle()

        verify(recordOutcome).invoke(DeliveryOutcome.Delivered(12))
        assertNull(vm.openStopId.value)
        assertEquals(RouteViewModel.Confirmation.DELIVERED, vm.confirmation.value)
    }

    @Test
    fun `given a failed delivery when recording then the confirmation matches`() = runTest {
        val vm = viewModel()
        val outcome = DeliveryOutcome.Failed(
            stopId = 13,
            reason = com.milkrun.feature.route.domain.model.FailureReason.ABSENT,
        )

        vm.record(outcome)
        mainDispatcher.dispatcher.scheduler.advanceUntilIdle()

        verify(recordOutcome).invoke(outcome)
        assertEquals(RouteViewModel.Confirmation.FAILED, vm.confirmation.value)
    }

    @Test
    fun `given a sync that cannot reach the server then the screen goes offline`() = runTest {
        whenever(syncPendingWork.invoke()).thenReturn(
            flowOf(Resource.Success(SyncOutcome.Failed("unreachable", retryable = true))),
        )

        val vm = viewModel()
        vm.sync()
        mainDispatcher.dispatcher.scheduler.advanceUntilIdle()

        assertFalse(vm.sync.value.online)
    }

    @Test
    fun `given a sign out then the session is cleared and the caller is notified`() = runTest {
        var notified = false
        val vm = viewModel()

        vm.signOut { notified = true }
        mainDispatcher.dispatcher.scheduler.advanceUntilIdle()

        verify(signOut).invoke()
        assertTrue(notified)
    }

    private fun route() = DeliveryRoute(
        id = 7,
        date = LocalDate.parse("2026-09-12"),
        vehicleCode = "CAM-03",
        driverName = "Reinier Castillo",
        plannedDistanceKm = 31.8,
        plannedDurationMinutes = 272.1,
        stops = listOf(stop(1, 12, StopStatus.DELIVERED), stop(2, 13, StopStatus.PLANNED)),
    )

    private fun stop(sequence: Int, id: Int, status: StopStatus) = RouteStop(
        sequence = sequence,
        legDistanceKm = 1.2,
        etaMinutes = sequence * 10.0,
        stop = Stop(
            id = id,
            trackingCode = "CODE$id",
            customerName = "Cliente $id",
            address = "Calle $id",
            coordinates = Coordinates(23.1, -82.3),
            demand = 2.0,
            status = status,
        ),
    )
}
