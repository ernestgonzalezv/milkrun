package com.milkrun.feature.auth.domain.model

data class Credentials(val username: String, val password: String) {
    val isComplete: Boolean get() = username.isNotBlank() && password.isNotBlank()
}
