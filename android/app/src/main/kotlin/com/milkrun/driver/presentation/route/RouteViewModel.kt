package com.milkrun.driver.presentation.route

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.milkrun.core.common.model.Resource
import com.milkrun.core.common.model.SyncOutcome
import com.milkrun.core.common.model.states.OperationState
import com.milkrun.driver.presentation.model.UiError
import com.milkrun.feature.auth.domain.usecase.SignOutUseCase
import com.milkrun.feature.route.domain.model.DeliveryOutcome
import com.milkrun.feature.route.domain.usecase.ObservePendingWorkUseCase
import com.milkrun.feature.route.domain.usecase.ObserveTodaysRouteUseCase
import com.milkrun.feature.route.domain.usecase.RecordDeliveryOutcomeUseCase
import com.milkrun.feature.route.domain.usecase.RefreshRouteUseCase
import com.milkrun.feature.route.domain.usecase.SyncPendingWorkUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class RouteViewModel(
    observeTodaysRoute: ObserveTodaysRouteUseCase,
    observePendingWork: ObservePendingWorkUseCase,
    private val refreshRoute: RefreshRouteUseCase,
    private val recordOutcome: RecordDeliveryOutcomeUseCase,
    private val syncPendingWork: SyncPendingWorkUseCase,
    private val signOutUseCase: SignOutUseCase,
) : ViewModel() {

    private val _state = MutableStateFlow<OperationState<RouteUiModel>>(OperationState.Loading)
    val state: StateFlow<OperationState<RouteUiModel>> = _state.asStateFlow()

    private val _sync = MutableStateFlow(SyncUiState())
    val sync: StateFlow<SyncUiState> = _sync.asStateFlow()

    private val _error = MutableStateFlow<UiError?>(null)
    val error: StateFlow<UiError?> = _error.asStateFlow()

    private val _openStopId = MutableStateFlow<Int?>(null)
    val openStopId: StateFlow<Int?> = _openStopId.asStateFlow()

    private val _confirmation = MutableStateFlow<Confirmation?>(null)
    val confirmation: StateFlow<Confirmation?> = _confirmation.asStateFlow()

    init {
        observeTodaysRoute()
            .onEach { route ->
                _state.value = OperationState.Success(
                    route?.let(RouteUiModel::Assigned) ?: RouteUiModel.NoRouteToday,
                )
            }
            .launchIn(viewModelScope)

        observePendingWork()
            .onEach { count -> _sync.update { it.copy(pending = count) } }
            .launchIn(viewModelScope)

        refresh()
    }

    fun refresh() {
        refreshRoute()
            .onEach { resource ->
                _sync.update {
                    when (resource) {
                        is Resource.Loading -> it.copy(uploading = true)
                        is Resource.Success -> it.copy(uploading = false, online = true)
                        is Resource.Error -> it.copy(uploading = false, online = false)
                    }
                }
            }
            .launchIn(viewModelScope)
    }

    fun openStop(stopId: Int?) {
        _openStopId.value = stopId
    }

    /**
     * Records to the local queue and returns. The upload attempt runs after, and the screen
     * never waits on it: a driver in a basement must still see the stop close.
     */
    fun record(outcome: DeliveryOutcome) {
        viewModelScope.launch {
            recordOutcome(outcome)
            _openStopId.value = null
            _confirmation.value = when (outcome) {
                is DeliveryOutcome.Delivered -> Confirmation.DELIVERED
                is DeliveryOutcome.Failed -> Confirmation.FAILED
                is DeliveryOutcome.EnRoute -> null
            }
            sync()
        }
    }

    fun sync() {
        syncPendingWork()
            .onEach { resource ->
                _sync.update {
                    when (resource) {
                        is Resource.Loading -> it.copy(uploading = true)
                        is Resource.Success -> it.copy(
                            uploading = false,
                            online = resource.data !is SyncOutcome.Failed,
                        )
                        is Resource.Error -> it.copy(uploading = false, online = false)
                    }
                }
            }
            .launchIn(viewModelScope)
    }

    fun confirmationShown() {
        _confirmation.value = null
    }

    fun dismissError() {
        _error.value = null
    }

    fun signOut(onSignedOut: () -> Unit) {
        viewModelScope.launch {
            signOutUseCase()
            onSignedOut()
        }
    }

    enum class Confirmation { DELIVERED, FAILED }
}
