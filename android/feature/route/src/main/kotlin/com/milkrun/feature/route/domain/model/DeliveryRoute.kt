package com.milkrun.feature.route.domain.model

import java.time.LocalDate

data class DeliveryRoute(
    val id: Int,
    val date: LocalDate,
    val vehicleCode: String,
    val driverName: String,
    val plannedDistanceKm: Double,
    val plannedDurationMinutes: Double,
    val stops: List<RouteStop>,
) {
    val delivered: Int get() = stops.count { it.stop.status == StopStatus.DELIVERED }

    val failed: Int get() = stops.count { it.stop.status == StopStatus.FAILED }

    val closed: Int get() = delivered + failed

    val progress: Float get() = if (stops.isEmpty()) 0f else closed.toFloat() / stops.size
}
