package com.milkrun.feature.route.data.repository

import com.milkrun.core.common.model.Resource
import com.milkrun.core.common.model.SyncOutcome
import com.milkrun.core.common.time.Clock
import com.milkrun.core.database.dao.CachedRouteDao
import com.milkrun.core.database.dao.LocalStopStateDao
import com.milkrun.core.database.dao.PendingEventDao
import com.milkrun.core.database.dao.PendingPingDao
import com.milkrun.core.database.entity.CachedRouteEntity
import com.milkrun.core.database.entity.LocalStopStateEntity
import com.milkrun.core.database.entity.PendingPingEntity
import com.milkrun.core.network.api.DriverApi
import com.milkrun.core.network.dto.delivery.EventBatchRequest
import com.milkrun.core.network.dto.delivery.PingBatchRequest
import com.milkrun.core.network.dto.route.RouteResponse
import com.milkrun.core.network.extensions.isRetryable
import com.milkrun.core.network.extensions.toErrorType
import com.milkrun.feature.route.data.mapper.projectedStatus
import com.milkrun.feature.route.data.mapper.toDomain
import com.milkrun.feature.route.data.mapper.toEntity
import com.milkrun.feature.route.data.mapper.toRequest
import com.milkrun.feature.route.domain.model.Coordinates
import com.milkrun.feature.route.domain.model.DeliveryOutcome
import com.milkrun.feature.route.domain.model.DeliveryRoute
import com.milkrun.feature.route.domain.model.StopStatus
import com.milkrun.feature.route.domain.repository.RouteRepository
import java.time.LocalDate
import java.util.UUID
import kotlin.coroutines.cancellation.CancellationException
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flow
import kotlinx.serialization.json.Json
import timber.log.Timber

class RouteRepositoryImpl(
    private val api: DriverApi,
    private val pendingEvents: PendingEventDao,
    private val pendingPings: PendingPingDao,
    private val cachedRoutes: CachedRouteDao,
    private val localStopStates: LocalStopStateDao,
    private val clock: Clock,
    private val json: Json,
) : RouteRepository {

    override fun observeRoute(date: LocalDate): Flow<DeliveryRoute?> = combine(
        cachedRoutes.observe(date.toString()),
        localStopStates.observeAll(),
    ) { cached, localStates ->
        val statuses = localStates.associate { it.stopId to StopStatus.from(it.status) }
        cached?.let { entity ->
            runCatching { json.decodeFromString<RouteResponse>(entity.payload).toDomain(statuses) }
                .onFailure { Timber.e(it, "stored route payload could not be parsed") }
                .getOrNull()
        }
    }

    override fun observePendingCount(): Flow<Int> = pendingEvents.pendingCount()

    override fun refresh(date: LocalDate): Flow<Resource<Unit>> = flow {
        emit(Resource.Loading)
        try {
            val response = api.todaysRoute(date.toString())
            if (response != null) {
                cachedRoutes.save(
                    CachedRouteEntity(
                        date = date.toString(),
                        payload = json.encodeToString(RouteResponse.serializer(), response),
                        savedAt = clock.now().toEpochMilli(),
                    ),
                )
                cachedRoutes.deleteBefore(date.toString())
            }
            emit(Resource.Success(Unit))
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            val type = e.toErrorType()
            Timber.i("route refresh failed with %s", type)
            emit(Resource.Error(e.message.orEmpty(), type, e))
        }
    }

    override suspend fun record(outcome: DeliveryOutcome) {
        pendingEvents.enqueue(
            outcome.toEntity(
                clientEventId = UUID.randomUUID().toString(),
                occurredAt = clock.now().toString(),
            ),
        )
        localStopStates.save(
            LocalStopStateEntity(
                stopId = outcome.stopId,
                status = outcome.projectedStatus().code,
                updatedAt = clock.now().toEpochMilli(),
            ),
        )
    }

    override suspend fun recordLocation(coordinates: Coordinates, accuracyM: Double?, speedKmh: Double?) {
        pendingPings.enqueue(
            PendingPingEntity(
                recordedAt = clock.now().toString(),
                latitude = coordinates.latitude,
                longitude = coordinates.longitude,
                accuracyM = accuracyM,
                speedKmh = speedKmh,
            ),
        )
    }

    /**
     * Events leave the queue whether the server created them or reported them as duplicates:
     * in both cases the fact is recorded there, which is the only question that matters.
     */
    override fun sync(): Flow<Resource<SyncOutcome>> = flow {
        emit(Resource.Loading)
        val events = pendingEvents.pending()
        val pings = pendingPings.pending()

        if (events.isEmpty() && pings.isEmpty()) {
            emit(Resource.Success(SyncOutcome.NothingPending))
            return@flow
        }

        try {
            var uploaded = 0
            var duplicates = 0

            if (events.isNotEmpty()) {
                val result = api.uploadEvents(EventBatchRequest(events.map { it.toRequest() }))
                pendingEvents.confirm(events.map { it.clientEventId })
                uploaded = result.created
                duplicates = result.duplicates
            }

            if (pings.isNotEmpty()) {
                uploadPings(pings.map { it.toRequest() }, pings.map { it.recordedAt })
            }

            emit(Resource.Success(SyncOutcome.Synced(uploaded, duplicates)))
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            val type = e.toErrorType()
            pendingEvents.markFailed(events.map { it.clientEventId }, type.name)
            Timber.w(e, "sync failed with %s", type)
            emit(
                Resource.Success(
                    SyncOutcome.Failed(e.message.orEmpty(), retryable = type.isRetryable()),
                ),
            )
        }
    }

    /**
     * Pings are secondary: if they fail the next pass picks them up, and a failed ping must not
     * abort a sync that already delivered the events.
     */
    private suspend fun uploadPings(
        requests: List<com.milkrun.core.network.dto.delivery.LocationPingRequest>,
        timestamps: List<String>,
    ) {
        runCatching {
            api.uploadPings(PingBatchRequest(requests))
            pendingPings.confirm(timestamps)
        }.onFailure { Timber.i("location pings could not be uploaded: %s", it.message) }
    }
}
