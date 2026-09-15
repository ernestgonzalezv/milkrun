package com.milkrun.core.network.dto.delivery

import kotlinx.serialization.Serializable

@Serializable
data class SyncResultResponse(val created: Int = 0, val duplicates: Int = 0, val rejected: Int = 0)
