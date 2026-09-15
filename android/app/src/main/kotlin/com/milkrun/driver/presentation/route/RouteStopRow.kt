package com.milkrun.driver.presentation.route

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import com.milkrun.core.ui.component.SequenceBadge
import com.milkrun.core.ui.component.StatusPill
import com.milkrun.core.ui.theme.MilkrunTheme
import com.milkrun.core.ui.tokens.AppSpacing
import com.milkrun.driver.R
import com.milkrun.driver.presentation.model.color
import com.milkrun.driver.presentation.model.labelRes
import com.milkrun.feature.route.domain.model.Coordinates
import com.milkrun.feature.route.domain.model.RouteStop
import com.milkrun.feature.route.domain.model.Stop
import com.milkrun.feature.route.domain.model.StopStatus

@Composable
fun RouteStopRow(routeStop: RouteStop, onClick: () -> Unit, modifier: Modifier = Modifier) {
    val status = routeStop.stop.status
    val statusLabel = stringResource(status.labelRes)
    val colors = status.color()

    Card(
        onClick = onClick,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = AppSpacing.xxs),
        modifier = modifier
            .fillMaxWidth()
            .semantics(mergeDescendants = true) {
                role = Role.Button
                contentDescription = "${routeStop.sequence}. " +
                    "${routeStop.stop.customerName}. $statusLabel"
            },
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(AppSpacing.md),
            horizontalArrangement = Arrangement.spacedBy(AppSpacing.md),
            verticalAlignment = Alignment.Top,
        ) {
            SequenceBadge(
                sequence = routeStop.sequence,
                container = colors.container,
                content = colors.content,
            )
            StopSummary(routeStop = routeStop, statusLabel = statusLabel, modifier = Modifier.weight(1f))
            StopMetrics(routeStop)
        }
    }
}

@Composable
private fun StopSummary(routeStop: RouteStop, statusLabel: String, modifier: Modifier = Modifier) {
    val colors = routeStop.stop.status.color()

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(AppSpacing.xxs)) {
        Text(
            text = routeStop.stop.customerName,
            style = MaterialTheme.typography.titleMedium,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        Text(
            text = routeStop.stop.address,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
        StatusPill(label = statusLabel, container = colors.container, content = colors.content)
    }
}

@Composable
private fun StopMetrics(routeStop: RouteStop) {
    Column(horizontalAlignment = Alignment.End) {
        Text(
            text = stringResource(R.string.route_stop_eta, routeStop.etaMinutes.toInt()),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = stringResource(
                R.string.route_stop_leg,
                formatDistance(routeStop.legDistanceKm),
            ),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

internal fun formatDistance(km: Double): String = String.format(java.util.Locale.US, "%.1f", km)

private val previewStop = RouteStop(
    sequence = 7,
    legDistanceKm = 2.1,
    etaMinutes = 55.0,
    stop = Stop(
        id = 1,
        trackingCode = "5SEHJK9Q",
        customerName = "Marlen Gonzalez",
        address = "Calle 41 No. 149, Playa, La Habana",
        coordinates = Coordinates(23.1, -82.4),
        demand = 2.8,
        status = StopStatus.PLANNED,
    ),
)

@Preview(name = "Pending", showBackground = true)
@Composable
private fun RouteStopRowPendingPreview() {
    MilkrunTheme { RouteStopRow(routeStop = previewStop, onClick = {}) }
}

@Preview(name = "Delivered", showBackground = true)
@Composable
private fun RouteStopRowDeliveredPreview() {
    MilkrunTheme {
        RouteStopRow(
            routeStop = previewStop.copy(
                stop = previewStop.stop.copy(status = StopStatus.DELIVERED),
            ),
            onClick = {},
        )
    }
}

@Preview(
    name = "Failed dark",
    showBackground = true,
    uiMode = android.content.res.Configuration.UI_MODE_NIGHT_YES,
)
@Composable
private fun RouteStopRowFailedPreview() {
    MilkrunTheme {
        RouteStopRow(
            routeStop = previewStop.copy(stop = previewStop.stop.copy(status = StopStatus.FAILED)),
            onClick = {},
        )
    }
}
