package com.milkrun.core.common.model.states

sealed class OperationState<out T> {
    data object Idle : OperationState<Nothing>()

    data object Loading : OperationState<Nothing>()

    data class Success<T>(val data: T) : OperationState<T>()

    data class Error(val message: String, val exception: Throwable? = null) : OperationState<Nothing>()
}
