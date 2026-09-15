package com.milkrun.driver.presentation.stop

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.core.net.toUri
import com.milkrun.core.ui.component.StatusPill
import com.milkrun.core.ui.theme.MilkrunIcons
import com.milkrun.core.ui.tokens.AppSize
import com.milkrun.core.ui.tokens.AppSpacing
import com.milkrun.driver.R
import com.milkrun.driver.presentation.model.color
import com.milkrun.driver.presentation.model.labelRes
import com.milkrun.feature.route.domain.model.DeliveryOutcome
import com.milkrun.feature.route.domain.model.FailureReason
import com.milkrun.feature.route.domain.model.RouteStop

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StopActionsSheet(routeStop: RouteStop, onDismiss: () -> Unit, onRecord: (DeliveryOutcome) -> Unit) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    var pickingReason by rememberSaveable { mutableStateOf(false) }
    var reason by rememberSaveable { mutableStateOf(FailureReason.ABSENT) }
    var note by rememberSaveable { mutableStateOf("") }

    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = sheetState) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .navigationBarsPadding()
                .padding(horizontal = AppSpacing.xl)
                .padding(bottom = AppSpacing.xl),
            verticalArrangement = Arrangement.spacedBy(AppSpacing.md),
        ) {
            StopHeader(routeStop)
            StopDetails(routeStop)
            StopShortcuts(routeStop, onRecord)

            when {
                routeStop.stop.status.isTerminal -> Text(
                    text = stringResource(R.string.stop_closed),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )

                pickingReason -> FailureForm(
                    reason = reason,
                    note = note,
                    onReasonChange = { reason = it },
                    onNoteChange = { note = it },
                    onBack = { pickingReason = false },
                    onConfirm = {
                        onRecord(DeliveryOutcome.Failed(routeStop.stop.id, reason, note))
                    },
                )

                else -> PrimaryActions(
                    onDelivered = { onRecord(DeliveryOutcome.Delivered(routeStop.stop.id, note)) },
                    onFailed = { pickingReason = true },
                )
            }
        }
    }
}

@Composable
private fun StopHeader(routeStop: RouteStop) {
    val colors = routeStop.stop.status.color()

    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(
            text = "${routeStop.sequence}. ${routeStop.stop.customerName}",
            style = MaterialTheme.typography.titleLarge,
            modifier = Modifier.weight(1f),
        )
        StatusPill(
            label = stringResource(routeStop.stop.status.labelRes),
            container = colors.container,
            content = colors.content,
        )
    }
}

@Composable
private fun StopDetails(routeStop: RouteStop) {
    Column(verticalArrangement = Arrangement.spacedBy(AppSpacing.xs)) {
        Text(routeStop.stop.address, style = MaterialTheme.typography.bodyLarge)

        if (routeStop.stop.notes.isNotBlank()) {
            Text(
                text = routeStop.stop.notes,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }

        Text(
            text = stringResource(
                R.string.stop_reference,
                routeStop.stop.trackingCode,
                String.format(java.util.Locale.US, "%.1f", routeStop.stop.demand),
            ),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

/**
 * Calling and navigating are handed to the system with an intent instead of embedding a map:
 * it is what the driver already knows how to use, and it keeps the app from requesting
 * permissions it does not need.
 */
@Composable
private fun StopShortcuts(routeStop: RouteStop, onRecord: (DeliveryOutcome) -> Unit) {
    val context = LocalContext.current
    val stop = routeStop.stop

    Row(horizontalArrangement = Arrangement.spacedBy(AppSpacing.sm)) {
        if (stop.phone.isNotBlank()) {
            OutlinedButton(
                onClick = {
                    context.startActivity(
                        Intent(Intent.ACTION_DIAL, "tel:${stop.phone}".toUri()),
                    )
                },
                modifier = Modifier.weight(1f),
            ) {
                Icon(MilkrunIcons.Call, contentDescription = null)
                Text(
                    text = stringResource(R.string.stop_call),
                    modifier = Modifier.padding(start = AppSpacing.sm),
                )
            }
        }

        OutlinedButton(
            onClick = {
                onRecord(DeliveryOutcome.EnRoute(stop.id))
                val label = Uri.encode(stop.customerName)
                val point = "${stop.coordinates.latitude},${stop.coordinates.longitude}"
                context.startActivity(
                    Intent(Intent.ACTION_VIEW, "geo:$point?q=$point($label)".toUri()),
                )
            },
            modifier = Modifier.weight(1f),
        ) {
            Icon(MilkrunIcons.Navigate, contentDescription = null)
            Text(
                text = stringResource(R.string.stop_navigate),
                modifier = Modifier.padding(start = AppSpacing.sm),
            )
        }
    }
}

@Composable
private fun PrimaryActions(onDelivered: () -> Unit, onFailed: () -> Unit) {
    Button(
        onClick = onDelivered,
        modifier = Modifier.fillMaxWidth().height(AppSize.primaryButton),
    ) {
        Text(stringResource(R.string.stop_mark_delivered))
    }
    OutlinedButton(
        onClick = onFailed,
        modifier = Modifier.fillMaxWidth().height(AppSize.secondaryButton),
        colors = ButtonDefaults.outlinedButtonColors(
            contentColor = MaterialTheme.colorScheme.error,
        ),
    ) {
        Text(stringResource(R.string.stop_mark_failed))
    }
}

@Composable
private fun FailureForm(
    reason: FailureReason,
    note: String,
    onReasonChange: (FailureReason) -> Unit,
    onNoteChange: (String) -> Unit,
    onBack: () -> Unit,
    onConfirm: () -> Unit,
) {
    Text(
        text = stringResource(R.string.stop_failure_question),
        style = MaterialTheme.typography.titleMedium,
    )

    Column(Modifier.selectableGroup()) {
        FailureReason.entries.forEach { option ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .selectable(
                        selected = reason == option,
                        onClick = { onReasonChange(option) },
                        role = Role.RadioButton,
                    )
                    .padding(vertical = AppSpacing.xs),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                RadioButton(selected = reason == option, onClick = null)
                Text(
                    text = stringResource(option.labelRes),
                    modifier = Modifier.padding(start = AppSpacing.sm),
                )
            }
        }
    }

    OutlinedTextField(
        value = note,
        onValueChange = onNoteChange,
        label = { Text(stringResource(R.string.stop_failure_note)) },
        modifier = Modifier.fillMaxWidth(),
        minLines = 2,
    )

    Row(horizontalArrangement = Arrangement.spacedBy(AppSpacing.sm)) {
        OutlinedButton(onClick = onBack, modifier = Modifier.weight(1f)) {
            Text(stringResource(R.string.stop_back))
        }
        Button(
            onClick = onConfirm,
            modifier = Modifier.weight(1f),
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.error,
            ),
        ) {
            Text(stringResource(R.string.stop_confirm))
        }
    }
}
