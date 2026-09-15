package com.milkrun.feature.route.domain.usecase

import com.milkrun.core.common.model.Resource
import com.milkrun.core.common.time.Clock
import com.milkrun.feature.route.domain.repository.RouteRepository
import kotlinx.coroutines.flow.Flow

class RefreshRouteUseCase(private val repository: RouteRepository, private val clock: Clock) {
    operator fun invoke(): Flow<Resource<Unit>> = repository.refresh(clock.today())
}
