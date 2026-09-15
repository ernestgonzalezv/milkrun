package com.milkrun.feature.route.data.mapper

import com.milkrun.core.network.dto.route.RouteResponse
import com.milkrun.core.network.dto.route.RouteStopResponse
import com.milkrun.core.network.dto.route.StopResponse
import com.milkrun.feature.route.domain.model.Coordinates
import com.milkrun.feature.route.domain.model.DeliveryRoute
import com.milkrun.feature.route.domain.model.RouteStop
import com.milkrun.feature.route.domain.model.Stop
import com.milkrun.feature.route.domain.model.StopStatus
import java.time.LocalDate

fun RouteResponse.toDomain(localStatuses: Map<Int, StopStatus> = emptyMap()): DeliveryRoute = DeliveryRoute(
    id = id,
    date = LocalDate.parse(date),
    vehicleCode = vehicleCode,
    driverName = driverName,
    plannedDistanceKm = plannedDistanceKm,
    plannedDurationMinutes = plannedDurationMinutes,
    stops = stops.map { it.toDomain(localStatuses) },
)

private fun RouteStopResponse.toDomain(localStatuses: Map<Int, StopStatus>): RouteStop = RouteStop(
    sequence = sequence,
    legDistanceKm = legDistanceKm,
    etaMinutes = etaMinutes,
    stop = stop.toDomain(localStatuses[stop.id]),
)

/**
 * A locally recorded status wins over the server's: it is newer by definition, because it has
 * not been uploaded yet.
 */
private fun StopResponse.toDomain(localStatus: StopStatus?): Stop = Stop(
    id = id,
    trackingCode = trackingCode,
    customerName = customerName,
    address = address,
    coordinates = Coordinates(latitude, longitude),
    demand = demand,
    status = localStatus ?: StopStatus.from(status),
    phone = phone,
    notes = notes,
)
