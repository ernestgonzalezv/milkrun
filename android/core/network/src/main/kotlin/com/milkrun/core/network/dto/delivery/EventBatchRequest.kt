package com.milkrun.core.network.dto.delivery

import kotlinx.serialization.Serializable

@Serializable
data class EventBatchRequest(val events: List<DeliveryEventRequest>)
