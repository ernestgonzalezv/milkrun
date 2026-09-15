package com.milkrun.core.network.dto.auth

import kotlinx.serialization.Serializable

@Serializable
data class RefreshRequest(val refresh: String)
