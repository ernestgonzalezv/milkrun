package com.milkrun.driver.presentation.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.milkrun.core.common.model.Resource
import com.milkrun.core.common.model.states.OperationState
import com.milkrun.driver.presentation.model.UiError
import com.milkrun.feature.auth.domain.model.Credentials
import com.milkrun.feature.auth.domain.model.DriverSession
import com.milkrun.feature.auth.domain.usecase.SignInUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach

class LoginViewModel(private val signIn: SignInUseCase) : ViewModel() {

    private val _state = MutableStateFlow<OperationState<DriverSession>>(OperationState.Idle)
    val state: StateFlow<OperationState<DriverSession>> = _state.asStateFlow()

    private val _error = MutableStateFlow<UiError?>(null)
    val error: StateFlow<UiError?> = _error.asStateFlow()

    fun signIn(credentials: Credentials) {
        if (!credentials.isComplete || _state.value is OperationState.Loading) return

        _error.value = null
        signIn.invoke(credentials)
            .onEach { resource ->
                _state.value = when (resource) {
                    is Resource.Loading -> OperationState.Loading
                    is Resource.Success -> OperationState.Success(resource.data)
                    is Resource.Error -> {
                        _error.value = UiError.fromErrorType(resource.type)
                        OperationState.Error(resource.message, resource.exception)
                    }
                }
            }
            .launchIn(viewModelScope)
    }

    fun dismissError() {
        _error.value = null
        if (_state.value is OperationState.Error) _state.value = OperationState.Idle
    }
}
