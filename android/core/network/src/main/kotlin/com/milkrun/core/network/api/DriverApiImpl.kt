package com.milkrun.core.network.api

import com.milkrun.core.network.dto.delivery.EventBatchRequest
import com.milkrun.core.network.dto.delivery.PingBatchRequest
import com.milkrun.core.network.dto.delivery.PingResultResponse
import com.milkrun.core.network.dto.delivery.SyncResultResponse
import com.milkrun.core.network.dto.route.RouteResponse
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.get
import io.ktor.client.request.parameter
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.HttpStatusCode

class DriverApiImpl(private val client: HttpClient) : DriverApi {

    override suspend fun todaysRoute(date: String): RouteResponse? {
        val response = client.get("/api/v1/me/route/") { parameter("date", date) }
        return if (response.status == HttpStatusCode.NoContent) null else response.body()
    }

    override suspend fun uploadEvents(request: EventBatchRequest): SyncResultResponse =
        client.post("/api/v1/me/events/") { setBody(request) }.body()

    override suspend fun uploadPings(request: PingBatchRequest): PingResultResponse =
        client.post("/api/v1/me/pings/") { setBody(request) }.body()
}
