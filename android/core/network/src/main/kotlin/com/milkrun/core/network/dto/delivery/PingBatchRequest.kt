package com.milkrun.core.network.dto.delivery

import kotlinx.serialization.Serializable

@Serializable
data class PingBatchRequest(val pings: List<LocationPingRequest>)
