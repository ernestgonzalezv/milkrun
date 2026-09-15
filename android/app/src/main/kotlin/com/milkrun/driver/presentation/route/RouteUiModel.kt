package com.milkrun.driver.presentation.route

import com.milkrun.feature.route.domain.model.DeliveryRoute

/**
 * "No route today" is a normal outcome, not an error, so it gets its own case instead of being
 * folded into a nullable success.
 */
sealed interface RouteUiModel {
    data object NoRouteToday : RouteUiModel

    data class Assigned(val route: DeliveryRoute) : RouteUiModel
}

data class SyncUiState(val online: Boolean = true, val uploading: Boolean = false, val pending: Int = 0)
