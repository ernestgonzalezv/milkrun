package com.milkrun.core.network.dto.delivery

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class DeliveryEventRequest(
    val stop: Int,
    @SerialName("client_event_id") val clientEventId: String,
    val kind: String,
    @SerialName("occurred_at") val occurredAt: String,
    val reason: String = "",
    val note: String = "",
    val latitude: Double? = null,
    val longitude: Double? = null,
)
