package com.milkrun.core.network.dto.auth

import kotlinx.serialization.Serializable

@Serializable
data class TokenPairResponse(val access: String, val refresh: String = "")
