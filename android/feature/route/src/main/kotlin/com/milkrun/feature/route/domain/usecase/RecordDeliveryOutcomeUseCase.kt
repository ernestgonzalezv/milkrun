package com.milkrun.feature.route.domain.usecase

import com.milkrun.feature.route.domain.model.DeliveryOutcome
import com.milkrun.feature.route.domain.repository.RouteRepository

class RecordDeliveryOutcomeUseCase(private val repository: RouteRepository) {
    suspend operator fun invoke(outcome: DeliveryOutcome) = repository.record(outcome)
}
