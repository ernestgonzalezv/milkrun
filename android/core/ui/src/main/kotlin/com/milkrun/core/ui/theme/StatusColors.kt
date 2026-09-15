package com.milkrun.core.ui.theme

import androidx.compose.material3.ColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

/**
 * Semantic pair for a status chip. Material 3 has no role for "this delivery failed", so the
 * pair is exposed as a token instead of letting screens pick colours.
 */
@Immutable
data class StatusColor(val container: Color, val content: Color)

@Immutable
data class StatusColors(
    val neutral: StatusColor,
    val pending: StatusColor,
    val inProgress: StatusColor,
    val done: StatusColor,
    val failed: StatusColor,
)

internal val LightStatusColors = StatusColors(
    neutral = StatusColor(AppColors.SurfaceVariantLight, AppColors.OnSurfaceVariantLight),
    pending = StatusColor(AppColors.BrandContainer, AppColors.Brand),
    inProgress = StatusColor(AppColors.WarningContainer, AppColors.Warning),
    done = StatusColor(AppColors.SuccessContainer, AppColors.Success),
    failed = StatusColor(AppColors.DangerContainer, AppColors.Danger),
)

internal val DarkStatusColors = StatusColors(
    neutral = StatusColor(AppColors.SurfaceVariantDark, AppColors.OnSurfaceVariantDark),
    pending = StatusColor(AppColors.BrandContainerDark, AppColors.BrandLight),
    inProgress = StatusColor(AppColors.WarningContainerDark, AppColors.WarningLight),
    done = StatusColor(AppColors.SuccessContainerDark, AppColors.SuccessLight),
    failed = StatusColor(AppColors.DangerContainerDark, AppColors.DangerLight),
)

internal val LocalStatusColors = staticCompositionLocalOf { LightStatusColors }

val ColorScheme.status: StatusColors
    @Composable @ReadOnlyComposable
    get() = LocalStatusColors.current
