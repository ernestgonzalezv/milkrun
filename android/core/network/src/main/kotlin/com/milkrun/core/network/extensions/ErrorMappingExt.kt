package com.milkrun.core.network.extensions

import com.milkrun.core.common.model.ErrorType
import io.ktor.client.plugins.ClientRequestException
import io.ktor.client.plugins.HttpRequestTimeoutException
import io.ktor.client.plugins.ServerResponseException
import io.ktor.http.HttpStatusCode
import java.io.IOException

fun Throwable.toErrorType(): ErrorType = when (this) {
    is IOException, is HttpRequestTimeoutException -> ErrorType.NO_INTERNET
    is ClientRequestException -> when (response.status) {
        HttpStatusCode.Unauthorized, HttpStatusCode.Forbidden -> ErrorType.UNAUTHORIZED
        HttpStatusCode.NotFound -> ErrorType.NOT_FOUND
        else -> ErrorType.BUSINESS_ERROR
    }
    is ServerResponseException -> ErrorType.NETWORK_ERROR
    else -> ErrorType.UNKNOWN_ERROR
}

/**
 * Whether retrying the same request later could succeed. A dropped connection resolves itself;
 * a rejected payload never will, and retrying it forever burns battery without progress.
 */
fun ErrorType.isRetryable(): Boolean = when (this) {
    ErrorType.NO_INTERNET, ErrorType.NETWORK_ERROR -> true
    else -> false
}
