package com.milkrun.feature.auth.domain.model

enum class DriverRole {
    DRIVER,
    DISPATCHER,
    ;

    companion object {
        fun from(code: String): DriverRole = when (code) {
            "driver" -> DRIVER
            else -> DISPATCHER
        }
    }
}
