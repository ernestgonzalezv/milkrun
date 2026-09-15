package com.milkrun.feature.route.domain.usecase

import com.milkrun.feature.route.domain.model.Coordinates
import com.milkrun.feature.route.domain.repository.RouteRepository

class RecordLocationUseCase(private val repository: RouteRepository) {
    suspend operator fun invoke(coordinates: Coordinates, accuracyM: Double? = null, speedKmh: Double? = null) =
        repository.recordLocation(coordinates, accuracyM, speedKmh)
}
