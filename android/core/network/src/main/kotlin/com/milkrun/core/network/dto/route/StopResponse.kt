package com.milkrun.core.network.dto.route

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class StopResponse(
    val id: Int,
    @SerialName("tracking_code") val trackingCode: String,
    @SerialName("customer_name") val customerName: String,
    val address: String,
    val latitude: Double,
    val longitude: Double,
    val demand: Double,
    val status: String,
    @SerialName("status_display") val statusDisplay: String = "",
    val phone: String = "",
    val notes: String = "",
)
