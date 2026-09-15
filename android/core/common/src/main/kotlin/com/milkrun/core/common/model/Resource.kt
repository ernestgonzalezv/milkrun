package com.milkrun.core.common.model

sealed class Resource<out T> {
    data class Success<T>(val data: T) : Resource<T>()

    data class Error(
        val message: String,
        val type: ErrorType = ErrorType.UNKNOWN_ERROR,
        val exception: Throwable? = null,
    ) : Resource<Nothing>()

    data object Loading : Resource<Nothing>()

    companion object {
        fun <T> success(data: T): Resource<T> = Success(data)

        fun error(
            message: String,
            type: ErrorType = ErrorType.UNKNOWN_ERROR,
            exception: Throwable? = null,
        ): Resource<Nothing> = Error(message, type, exception)

        fun loading(): Resource<Nothing> = Loading
    }
}
