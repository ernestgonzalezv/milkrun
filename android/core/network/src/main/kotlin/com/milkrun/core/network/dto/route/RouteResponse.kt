package com.milkrun.core.network.dto.route

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class RouteResponse(
    val id: Int,
    val date: String,
    val status: String,
    @SerialName("vehicle_code") val vehicleCode: String,
    @SerialName("driver_name") val driverName: String = "",
    @SerialName("planned_distance_km") val plannedDistanceKm: Double,
    @SerialName("planned_duration_minutes") val plannedDurationMinutes: Double,
    val stops: List<RouteStopResponse> = emptyList(),
)
