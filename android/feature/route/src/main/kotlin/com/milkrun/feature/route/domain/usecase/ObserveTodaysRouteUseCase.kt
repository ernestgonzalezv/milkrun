package com.milkrun.feature.route.domain.usecase

import com.milkrun.core.common.time.Clock
import com.milkrun.feature.route.domain.model.DeliveryRoute
import com.milkrun.feature.route.domain.repository.RouteRepository
import kotlinx.coroutines.flow.Flow

/**
 * No date parameter: the use case *is* "today". The clock is injected so tests can pin it
 * without the caller having to thread a date through every layer.
 */
class ObserveTodaysRouteUseCase(private val repository: RouteRepository, private val clock: Clock) {
    operator fun invoke(): Flow<DeliveryRoute?> = repository.observeRoute(clock.today())
}
