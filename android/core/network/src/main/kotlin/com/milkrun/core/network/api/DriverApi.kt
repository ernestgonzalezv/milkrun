package com.milkrun.core.network.api

import com.milkrun.core.network.dto.delivery.EventBatchRequest
import com.milkrun.core.network.dto.delivery.PingBatchRequest
import com.milkrun.core.network.dto.delivery.PingResultResponse
import com.milkrun.core.network.dto.delivery.SyncResultResponse
import com.milkrun.core.network.dto.route.RouteResponse

interface DriverApi {
    /**
     * Returns `null` when the backend answers 204, which means the driver has no route for
     * that day. That is not an error and must stay distinguishable from a failed request.
     */
    suspend fun todaysRoute(date: String): RouteResponse?

    suspend fun uploadEvents(request: EventBatchRequest): SyncResultResponse

    suspend fun uploadPings(request: PingBatchRequest): PingResultResponse
}
