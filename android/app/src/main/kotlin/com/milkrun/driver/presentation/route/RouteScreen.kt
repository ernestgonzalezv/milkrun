package com.milkrun.driver.presentation.route

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.tooling.preview.Preview
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.milkrun.core.common.model.states.OperationState
import com.milkrun.core.ui.component.SyncBanner
import com.milkrun.core.ui.theme.MilkrunIcons
import com.milkrun.core.ui.theme.MilkrunTheme
import com.milkrun.core.ui.tokens.AppSize
import com.milkrun.core.ui.tokens.AppSpacing
import com.milkrun.driver.R
import com.milkrun.driver.presentation.stop.StopActionsSheet
import com.milkrun.feature.route.domain.model.DeliveryRoute
import org.koin.androidx.compose.koinViewModel

@Composable
fun RouteScreen(onSignedOut: () -> Unit, modifier: Modifier = Modifier, viewModel: RouteViewModel = koinViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val sync by viewModel.sync.collectAsStateWithLifecycle()
    val openStopId by viewModel.openStopId.collectAsStateWithLifecycle()
    val confirmation by viewModel.confirmation.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }

    val deliveredMessage = stringResource(R.string.stop_recorded_delivered)
    val failedMessage = stringResource(R.string.stop_recorded_failed)

    LaunchedEffect(confirmation) {
        val message = when (confirmation) {
            RouteViewModel.Confirmation.DELIVERED -> deliveredMessage
            RouteViewModel.Confirmation.FAILED -> failedMessage
            null -> null
        }
        if (message != null) {
            snackbar.showSnackbar(message)
            viewModel.confirmationShown()
        }
    }

    RouteContent(
        state = state,
        sync = sync,
        snackbar = snackbar,
        onRefresh = viewModel::refresh,
        onSignOut = { viewModel.signOut(onSignedOut) },
        onOpenStop = viewModel::openStop,
        modifier = modifier,
    )

    val assigned = (state as? OperationState.Success)?.data as? RouteUiModel.Assigned
    val openStop = openStopId?.let { id -> assigned?.route?.stops?.firstOrNull { it.stop.id == id } }
    if (openStop != null) {
        StopActionsSheet(
            routeStop = openStop,
            onDismiss = { viewModel.openStop(null) },
            onRecord = viewModel::record,
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun RouteContent(
    state: OperationState<RouteUiModel>,
    sync: SyncUiState,
    snackbar: SnackbarHostState,
    onRefresh: () -> Unit,
    onSignOut: () -> Unit,
    onOpenStop: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    val route = ((state as? OperationState.Success)?.data as? RouteUiModel.Assigned)?.route

    Scaffold(
        modifier = modifier,
        snackbarHost = { SnackbarHost(snackbar) },
        topBar = {
            TopAppBar(
                title = { RouteTitle(route) },
                actions = {
                    IconButton(onClick = onRefresh, enabled = !sync.uploading) {
                        Icon(
                            imageVector = MilkrunIcons.Refresh,
                            contentDescription = stringResource(R.string.route_refresh),
                        )
                    }
                    IconButton(onClick = onSignOut) {
                        Icon(
                            imageVector = MilkrunIcons.SignOut,
                            contentDescription = stringResource(R.string.route_sign_out),
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            if (route != null && route.stops.isNotEmpty()) {
                RouteProgress(route)
            }

            SyncBanner(
                online = sync.online,
                pending = sync.pending,
                uploading = sync.uploading,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = AppSpacing.lg, vertical = AppSpacing.sm),
            )

            RouteBody(
                loading = state is OperationState.Loading || state is OperationState.Idle,
                route = route,
                onOpenStop = onOpenStop,
            )
        }
    }
}

@Composable
private fun RouteBody(loading: Boolean, route: DeliveryRoute?, onOpenStop: (Int) -> Unit) {
    when {
        loading -> Centered { CircularProgressIndicator() }

        route == null || route.stops.isEmpty() -> Centered { EmptyRoute() }

        else -> LazyColumn(
            contentPadding = PaddingValues(
                horizontal = AppSpacing.lg,
                vertical = AppSpacing.sm,
            ),
            verticalArrangement = Arrangement.spacedBy(AppSpacing.sm),
        ) {
            items(route.stops, key = { it.stop.id }) { routeStop ->
                RouteStopRow(routeStop = routeStop, onClick = { onOpenStop(routeStop.stop.id) })
            }
        }
    }
}

@Composable
private fun RouteTitle(route: DeliveryRoute?) {
    Column {
        Text(
            text = route?.let { stringResource(R.string.route_title, it.vehicleCode) }
                ?: stringResource(R.string.route_title_empty),
            style = MaterialTheme.typography.titleMedium,
        )
        if (route != null && route.stops.isNotEmpty()) {
            Text(
                text = stringResource(
                    R.string.route_summary,
                    route.closed,
                    route.stops.size,
                    formatDistance(route.plannedDistanceKm),
                ),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun RouteProgress(route: DeliveryRoute) {
    val description = pluralStringResource(
        R.plurals.route_progress_description,
        route.stops.size,
        route.closed,
        route.stops.size,
    )
    LinearProgressIndicator(
        progress = { route.progress },
        modifier = Modifier
            .fillMaxWidth()
            .height(AppSize.progressBar)
            .clearAndSetSemantics { contentDescription = description },
    )
}

@Composable
private fun EmptyRoute() {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(AppSpacing.sm),
    ) {
        Text(
            text = stringResource(R.string.route_empty_title),
            style = MaterialTheme.typography.titleMedium,
        )
        Text(
            text = stringResource(R.string.route_empty_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun Centered(content: @Composable () -> Unit) {
    Box(
        modifier = Modifier.fillMaxSize().padding(AppSpacing.xxl),
        contentAlignment = Alignment.Center,
    ) {
        content()
    }
}

@Preview(name = "No route today", showBackground = true)
@Composable
private fun RouteEmptyPreview() {
    MilkrunTheme {
        RouteContent(
            state = OperationState.Success(RouteUiModel.NoRouteToday),
            sync = SyncUiState(),
            snackbar = remember { SnackbarHostState() },
            onRefresh = {},
            onSignOut = {},
            onOpenStop = {},
        )
    }
}

@Preview(name = "Offline with queue", showBackground = true)
@Composable
private fun RouteOfflinePreview() {
    MilkrunTheme {
        RouteContent(
            state = OperationState.Success(RouteUiModel.NoRouteToday),
            sync = SyncUiState(online = false, pending = 3),
            snackbar = remember { SnackbarHostState() },
            onRefresh = {},
            onSignOut = {},
            onOpenStop = {},
        )
    }
}
