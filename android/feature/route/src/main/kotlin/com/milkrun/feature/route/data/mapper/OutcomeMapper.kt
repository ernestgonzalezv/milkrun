package com.milkrun.feature.route.data.mapper

import com.milkrun.core.database.entity.PendingEventEntity
import com.milkrun.core.database.entity.PendingPingEntity
import com.milkrun.core.network.dto.delivery.DeliveryEventRequest
import com.milkrun.core.network.dto.delivery.LocationPingRequest
import com.milkrun.feature.route.domain.model.DeliveryOutcome
import com.milkrun.feature.route.domain.model.StopStatus

internal const val KIND_DELIVERED = "delivered"
internal const val KIND_FAILED = "failed"
internal const val KIND_DEPARTED = "departed"

fun DeliveryOutcome.toEntity(clientEventId: String, occurredAt: String): PendingEventEntity = PendingEventEntity(
    clientEventId = clientEventId,
    stopId = stopId,
    kind = kind(),
    reason = (this as? DeliveryOutcome.Failed)?.reason?.code.orEmpty(),
    note = note(),
    occurredAt = occurredAt,
)

fun DeliveryOutcome.projectedStatus(): StopStatus = when (this) {
    is DeliveryOutcome.Delivered -> StopStatus.DELIVERED
    is DeliveryOutcome.Failed -> StopStatus.FAILED
    is DeliveryOutcome.EnRoute -> StopStatus.IN_TRANSIT
}

fun PendingEventEntity.toRequest(): DeliveryEventRequest = DeliveryEventRequest(
    stop = stopId,
    clientEventId = clientEventId,
    kind = kind,
    occurredAt = occurredAt,
    reason = reason,
    note = note,
    latitude = latitude,
    longitude = longitude,
)

fun PendingPingEntity.toRequest(): LocationPingRequest = LocationPingRequest(
    latitude = latitude,
    longitude = longitude,
    recordedAt = recordedAt,
    accuracyM = accuracyM,
    speedKmh = speedKmh,
)

private fun DeliveryOutcome.kind(): String = when (this) {
    is DeliveryOutcome.Delivered -> KIND_DELIVERED
    is DeliveryOutcome.Failed -> KIND_FAILED
    is DeliveryOutcome.EnRoute -> KIND_DEPARTED
}

private fun DeliveryOutcome.note(): String = when (this) {
    is DeliveryOutcome.Delivered -> note
    is DeliveryOutcome.Failed -> note
    is DeliveryOutcome.EnRoute -> ""
}
