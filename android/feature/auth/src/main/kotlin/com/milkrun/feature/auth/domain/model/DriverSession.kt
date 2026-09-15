package com.milkrun.feature.auth.domain.model

data class DriverSession(val id: Int, val username: String, val fullName: String, val role: DriverRole) {
    val displayName: String get() = fullName.ifBlank { username }
}
