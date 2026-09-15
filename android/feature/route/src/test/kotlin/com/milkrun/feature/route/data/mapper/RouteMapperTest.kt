package com.milkrun.feature.route.data.mapper

import com.milkrun.feature.route.domain.model.StopStatus
import com.milkrun.feature.route.routeResponse
import com.milkrun.feature.route.routeStopResponse
import com.milkrun.feature.route.stopResponse
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class RouteMapperTest {

    @Test
    fun `given a payload when mapping then every field reaches the domain model`() {
        val route = routeResponse().toDomain()

        assertEquals(7, route.id)
        assertEquals("CAM-03", route.vehicleCode)
        assertEquals("2026-09-12", route.date.toString())
        assertEquals(1, route.stops.size)
        assertEquals("ZU6P6E6K", route.stops.first().stop.trackingCode)
        assertEquals(26.1, route.stops.first().etaMinutes)
        assertEquals(23.1179, route.stops.first().stop.coordinates.latitude)
    }

    @Test
    fun `given a locally recorded status then it wins over the one from the server`() {
        val route = routeResponse().toDomain(mapOf(12 to StopStatus.DELIVERED))

        assertEquals(StopStatus.DELIVERED, route.stops.first().stop.status)
    }

    @Test
    fun `given no local status then the server status is kept`() {
        val route = routeResponse().toDomain()

        assertEquals(StopStatus.PLANNED, route.stops.first().stop.status)
    }

    @Test
    fun `given an unknown status code then it degrades to PENDING instead of crashing`() {
        val route = routeResponse(
            stops = listOf(routeStopResponse(stop = stopResponse(status = "teleported"))),
        ).toDomain()

        assertEquals(StopStatus.PENDING, route.stops.first().stop.status)
    }

    @Test
    fun `given mixed statuses when counting then progress reflects the closed stops`() {
        val route = routeResponse(
            stops = listOf(
                routeStopResponse(sequence = 1, stop = stopResponse(id = 1, status = "delivered")),
                routeStopResponse(sequence = 2, stop = stopResponse(id = 2, status = "failed")),
                routeStopResponse(sequence = 3, stop = stopResponse(id = 3, status = "planned")),
                routeStopResponse(sequence = 4, stop = stopResponse(id = 4, status = "planned")),
            ),
        ).toDomain()

        assertEquals(1, route.delivered)
        assertEquals(1, route.failed)
        assertEquals(2, route.closed)
        assertEquals(0.5f, route.progress)
    }
}
