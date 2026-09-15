package com.milkrun.feature.route.data.repository

import app.cash.turbine.test
import com.milkrun.core.common.model.Resource
import com.milkrun.core.common.model.SyncOutcome
import com.milkrun.core.database.dao.CachedRouteDao
import com.milkrun.core.database.dao.LocalStopStateDao
import com.milkrun.core.database.dao.PendingEventDao
import com.milkrun.core.database.dao.PendingPingDao
import com.milkrun.core.database.entity.CachedRouteEntity
import com.milkrun.core.database.entity.LocalStopStateEntity
import com.milkrun.core.database.entity.PendingEventEntity
import com.milkrun.core.network.api.DriverApi
import com.milkrun.core.network.client.MilkrunJson
import com.milkrun.core.network.dto.delivery.SyncResultResponse
import com.milkrun.core.network.dto.route.RouteResponse
import com.milkrun.feature.route.TestClock
import com.milkrun.feature.route.domain.model.DeliveryOutcome
import com.milkrun.feature.route.domain.model.FailureReason
import com.milkrun.feature.route.domain.model.StopStatus
import com.milkrun.feature.route.httpFailure
import com.milkrun.feature.route.routeResponse
import io.ktor.http.HttpStatusCode
import java.io.IOException
import java.time.LocalDate
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Nested
import org.junit.jupiter.api.Test
import org.mockito.kotlin.any
import org.mockito.kotlin.argumentCaptor
import org.mockito.kotlin.mock
import org.mockito.kotlin.never
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

class RouteRepositoryImplTest {

    private val today: LocalDate = LocalDate.parse("2026-09-12")

    private lateinit var api: DriverApi
    private lateinit var pendingEvents: PendingEventDao
    private lateinit var pendingPings: PendingPingDao
    private lateinit var cachedRoutes: CachedRouteDao
    private lateinit var localStopStates: LocalStopStateDao
    private lateinit var repository: RouteRepositoryImpl

    @BeforeEach
    fun setup() {
        api = mock()
        pendingEvents = mock()
        pendingPings = mock()
        cachedRoutes = mock()
        localStopStates = mock()
        repository = RouteRepositoryImpl(
            api = api,
            pendingEvents = pendingEvents,
            pendingPings = pendingPings,
            cachedRoutes = cachedRoutes,
            localStopStates = localStopStates,
            clock = TestClock(),
            json = MilkrunJson,
        )
    }

    @Nested
    inner class ObserveRoute {

        @Test
        fun `given a stored route then it is served from the database`() = runTest {
            givenStoredRoute()
            whenever(localStopStates.observeAll()).thenReturn(flowOf(emptyList()))

            repository.observeRoute(today).test {
                val route = awaitItem()
                assertEquals("CAM-03", route?.vehicleCode)
                awaitComplete()
            }
        }

        @Test
        fun `given a local outcome then it overrides the stored status`() = runTest {
            givenStoredRoute()
            whenever(localStopStates.observeAll()).thenReturn(
                flowOf(listOf(LocalStopStateEntity(12, StopStatus.DELIVERED.code, 0L))),
            )

            repository.observeRoute(today).test {
                assertEquals(StopStatus.DELIVERED, awaitItem()?.stops?.first()?.stop?.status)
                awaitComplete()
            }
        }

        @Test
        fun `given a corrupt payload then it yields null instead of crashing`() = runTest {
            whenever(cachedRoutes.observe(any())).thenReturn(
                flowOf(CachedRouteEntity(today.toString(), "{not json", 0L)),
            )
            whenever(localStopStates.observeAll()).thenReturn(flowOf(emptyList()))

            repository.observeRoute(today).test {
                assertEquals(null, awaitItem())
                awaitComplete()
            }
        }
    }

    @Nested
    inner class RecordOutcome {

        @Test
        fun `given a delivery then it is queued and projected locally without touching the network`() = runTest {
            repository.record(DeliveryOutcome.Delivered(stopId = 12, note = "Entregado"))

            val event = argumentCaptor<PendingEventEntity>()
            verify(pendingEvents).enqueue(event.capture())
            assertEquals(12, event.firstValue.stopId)
            assertEquals("delivered", event.firstValue.kind)
            assertEquals("2026-09-12T14:10:18Z", event.firstValue.occurredAt)
            assertTrue(event.firstValue.clientEventId.isNotBlank())

            val state = argumentCaptor<LocalStopStateEntity>()
            verify(localStopStates).save(state.capture())
            assertEquals(StopStatus.DELIVERED.code, state.firstValue.status)
        }

        @Test
        fun `given a failure then the reason travels with the event`() = runTest {
            repository.record(
                DeliveryOutcome.Failed(stopId = 13, reason = FailureReason.ABSENT, note = "Nadie abrió"),
            )

            val event = argumentCaptor<PendingEventEntity>()
            verify(pendingEvents).enqueue(event.capture())
            assertEquals("failed", event.firstValue.kind)
            assertEquals("absent", event.firstValue.reason)
        }
    }

    @Nested
    inner class Sync {

        @Test
        fun `given an empty queue then nothing is uploaded`() = runTest {
            whenever(pendingEvents.pending()).thenReturn(emptyList())
            whenever(pendingPings.pending()).thenReturn(emptyList())

            repository.sync().test {
                assertEquals(Resource.Loading, awaitItem())
                val result = (awaitItem() as Resource.Success).data
                assertEquals(SyncOutcome.NothingPending, result)
                awaitComplete()
            }
        }

        @Test
        fun `given queued events when the upload succeeds then the queue is cleared`() = runTest {
            whenever(pendingEvents.pending()).thenReturn(listOf(queuedEvent()))
            whenever(pendingPings.pending()).thenReturn(emptyList())
            whenever(api.uploadEvents(any())).thenReturn(SyncResultResponse(created = 1))

            repository.sync().test {
                awaitItem()
                val result = (awaitItem() as Resource.Success).data as SyncOutcome.Synced
                assertEquals(1, result.uploaded)
                awaitComplete()
            }

            verify(pendingEvents).confirm(listOf("event-1"))
        }

        @Test
        fun `given the server reports duplicates then the queue is cleared all the same`() = runTest {
            whenever(pendingEvents.pending()).thenReturn(listOf(queuedEvent()))
            whenever(pendingPings.pending()).thenReturn(emptyList())
            whenever(api.uploadEvents(any())).thenReturn(SyncResultResponse(duplicates = 1))

            repository.sync().test {
                awaitItem()
                val result = (awaitItem() as Resource.Success).data as SyncOutcome.Synced
                assertEquals(0, result.uploaded)
                assertEquals(1, result.duplicates)
                awaitComplete()
            }

            verify(pendingEvents).confirm(listOf("event-1"))
        }

        @Test
        fun `given no connection then the queue is kept and the failure is retryable`() = runTest {
            whenever(pendingEvents.pending()).thenReturn(listOf(queuedEvent()))
            whenever(pendingPings.pending()).thenReturn(emptyList())
            whenever(api.uploadEvents(any())).thenAnswer { throw IOException("unreachable") }

            repository.sync().test {
                awaitItem()
                val result = (awaitItem() as Resource.Success).data as SyncOutcome.Failed
                assertTrue(result.retryable)
                awaitComplete()
            }

            verify(pendingEvents, never()).confirm(any())
            verify(pendingEvents).markFailed(listOf("event-1"), "NO_INTERNET")
        }

        @Test
        fun `given the server rejects the batch then the failure is not retryable`() = runTest {
            val rejection = httpFailure(HttpStatusCode.BadRequest)
            whenever(pendingEvents.pending()).thenReturn(listOf(queuedEvent()))
            whenever(pendingPings.pending()).thenReturn(emptyList())
            whenever(api.uploadEvents(any())).thenAnswer { throw rejection }

            repository.sync().test {
                awaitItem()
                val result = (awaitItem() as Resource.Success).data as SyncOutcome.Failed
                assertFalse(result.retryable)
                awaitComplete()
            }

            verify(pendingEvents, never()).confirm(any())
        }
    }

    private fun queuedEvent() = PendingEventEntity(
        clientEventId = "event-1",
        stopId = 12,
        kind = "delivered",
        occurredAt = "2026-09-12T14:10:18Z",
    )

    private suspend fun givenStoredRoute() {
        whenever(cachedRoutes.observe(any())).thenReturn(
            flowOf(
                CachedRouteEntity(
                    date = today.toString(),
                    payload = MilkrunJson.encodeToString(
                        RouteResponse.serializer(),
                        routeResponse(),
                    ),
                    savedAt = 0L,
                ),
            ),
        )
    }
}
