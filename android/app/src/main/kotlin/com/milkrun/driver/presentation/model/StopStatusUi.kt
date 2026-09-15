package com.milkrun.driver.presentation.model

import androidx.annotation.StringRes
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import com.milkrun.core.ui.theme.StatusColor
import com.milkrun.core.ui.theme.status
import com.milkrun.driver.R
import com.milkrun.feature.route.domain.model.StopStatus

@get:StringRes
val StopStatus.labelRes: Int
    get() = when (this) {
        StopStatus.PENDING -> R.string.status_pending
        StopStatus.PLANNED -> R.string.status_planned
        StopStatus.IN_TRANSIT -> R.string.status_in_transit
        StopStatus.DELIVERED -> R.string.status_delivered
        StopStatus.FAILED -> R.string.status_failed
        StopStatus.CANCELLED -> R.string.status_cancelled
    }

@Composable
fun StopStatus.color(): StatusColor {
    val colors = MaterialTheme.colorScheme.status
    return when (this) {
        StopStatus.PENDING -> colors.neutral
        StopStatus.PLANNED -> colors.pending
        StopStatus.IN_TRANSIT -> colors.inProgress
        StopStatus.DELIVERED -> colors.done
        StopStatus.FAILED, StopStatus.CANCELLED -> colors.failed
    }
}
