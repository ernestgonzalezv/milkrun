package com.milkrun.feature.route

import com.milkrun.core.network.dto.route.RouteResponse
import com.milkrun.core.network.dto.route.RouteStopResponse
import com.milkrun.core.network.dto.route.StopResponse

fun stopResponse(id: Int = 12, status: String = "planned", customerName: String = "Liudmila Torres") = StopResponse(
    id = id,
    trackingCode = "ZU6P6E6K",
    customerName = customerName,
    address = "Calzada del Cerro No. 711, Cerro, La Habana",
    latitude = 23.1179,
    longitude = -82.3689,
    demand = 2.5,
    status = status,
    statusDisplay = "Planificada",
    phone = "+53 55512345",
    notes = "Tocar el timbre del segundo piso",
)

fun routeStopResponse(sequence: Int = 1, stop: StopResponse = stopResponse()) = RouteStopResponse(
    id = sequence,
    sequence = sequence,
    legDistanceKm = 9.58,
    etaMinutes = 26.1,
    stop = stop,
)

fun routeResponse(stops: List<RouteStopResponse> = listOf(routeStopResponse())) = RouteResponse(
    id = 7,
    date = "2026-09-12",
    status = "dispatched",
    vehicleCode = "CAM-03",
    driverName = "Reinier Castillo",
    plannedDistanceKm = 31.8,
    plannedDurationMinutes = 272.1,
    stops = stops,
)
