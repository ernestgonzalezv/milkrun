package com.milkrun.core.network.dto.delivery

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class LocationPingRequest(
    val latitude: Double,
    val longitude: Double,
    @SerialName("recorded_at") val recordedAt: String,
    @SerialName("accuracy_m") val accuracyM: Double? = null,
    @SerialName("speed_kmh") val speedKmh: Double? = null,
)
