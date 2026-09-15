package com.milkrun.core.network.dto.route

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class RouteStopResponse(
    val id: Int,
    val sequence: Int,
    @SerialName("leg_distance_km") val legDistanceKm: Double,
    @SerialName("eta_minutes") val etaMinutes: Double,
    val stop: StopResponse,
)
