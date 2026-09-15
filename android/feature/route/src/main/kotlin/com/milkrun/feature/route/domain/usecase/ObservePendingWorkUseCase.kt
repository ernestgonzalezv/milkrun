package com.milkrun.feature.route.domain.usecase

import com.milkrun.feature.route.domain.repository.RouteRepository
import kotlinx.coroutines.flow.Flow

class ObservePendingWorkUseCase(private val repository: RouteRepository) {
    operator fun invoke(): Flow<Int> = repository.observePendingCount()
}
