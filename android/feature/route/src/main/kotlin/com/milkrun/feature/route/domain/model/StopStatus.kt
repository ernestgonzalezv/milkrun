package com.milkrun.feature.route.domain.model

enum class StopStatus(val code: String) {
    PENDING("pending"),
    PLANNED("planned"),
    IN_TRANSIT("in_transit"),
    DELIVERED("delivered"),
    FAILED("failed"),
    CANCELLED("cancelled"),
    ;

    val isTerminal: Boolean get() = this == DELIVERED || this == FAILED || this == CANCELLED

    companion object {
        fun from(code: String): StopStatus = entries.firstOrNull { it.code == code } ?: PENDING
    }
}
