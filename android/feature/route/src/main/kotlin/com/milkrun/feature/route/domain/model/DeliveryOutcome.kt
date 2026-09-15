package com.milkrun.feature.route.domain.model

/**
 * What the driver reports from the field. Modelled as a sealed type so a failure without a
 * reason cannot be constructed — the backend rejects it, and catching that at compile time is
 * cheaper than catching it after the queue has already accepted the event.
 */
sealed interface DeliveryOutcome {
    val stopId: Int

    data class Delivered(override val stopId: Int, val note: String = "") : DeliveryOutcome

    data class Failed(override val stopId: Int, val reason: FailureReason, val note: String = "") : DeliveryOutcome

    data class EnRoute(override val stopId: Int) : DeliveryOutcome
}
