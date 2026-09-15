package com.milkrun.feature.route.domain.model

enum class FailureReason(val code: String) {
    ABSENT("absent"),
    WRONG_ADDRESS("wrong_address"),
    REFUSED("refused"),
    NO_ACCESS("no_access"),
    OTHER("other"),
}
