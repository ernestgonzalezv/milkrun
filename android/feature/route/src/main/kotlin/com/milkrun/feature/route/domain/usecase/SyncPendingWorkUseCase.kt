package com.milkrun.feature.route.domain.usecase

import com.milkrun.core.common.model.Resource
import com.milkrun.core.common.model.SyncOutcome
import com.milkrun.feature.route.domain.repository.RouteRepository
import kotlinx.coroutines.flow.Flow

class SyncPendingWorkUseCase(private val repository: RouteRepository) {
    operator fun invoke(): Flow<Resource<SyncOutcome>> = repository.sync()
}
