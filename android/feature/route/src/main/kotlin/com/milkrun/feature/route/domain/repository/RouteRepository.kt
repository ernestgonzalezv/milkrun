package com.milkrun.feature.route.domain.repository

import com.milkrun.core.common.model.Resource
import com.milkrun.core.common.model.SyncOutcome
import com.milkrun.feature.route.domain.model.Coordinates
import com.milkrun.feature.route.domain.model.DeliveryOutcome
import com.milkrun.feature.route.domain.model.DeliveryRoute
import java.time.LocalDate
import kotlinx.coroutines.flow.Flow

interface RouteRepository {
    /**
     * The stored route with locally recorded outcomes already applied. Backed by the database,
     * not the network, so the screen renders identically with or without coverage.
     */
    fun observeRoute(date: LocalDate): Flow<DeliveryRoute?>

    fun observePendingCount(): Flow<Int>

    fun refresh(date: LocalDate): Flow<Resource<Unit>>

    fun sync(): Flow<Resource<SyncOutcome>>

    /** Writes to the local queue only. Never waits on the network. */
    suspend fun record(outcome: DeliveryOutcome)

    suspend fun recordLocation(coordinates: Coordinates, accuracyM: Double?, speedKmh: Double?)
}
