package com.milkrun.core.network.dto.auth

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class UserResponse(
    val id: Int,
    val username: String,
    @SerialName("full_name") val fullName: String = "",
    val role: String,
    val phone: String = "",
)
