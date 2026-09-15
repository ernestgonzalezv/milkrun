package com.milkrun.core.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider

private val LightScheme = lightColorScheme(
    primary = AppColors.Brand,
    onPrimary = AppColors.SurfaceLight,
    primaryContainer = AppColors.BrandContainer,
    onPrimaryContainer = AppColors.Brand,
    secondary = AppColors.OnSurfaceVariantLight,
    background = AppColors.BackgroundLight,
    onBackground = AppColors.OnSurfaceLight,
    surface = AppColors.SurfaceLight,
    onSurface = AppColors.OnSurfaceLight,
    surfaceVariant = AppColors.SurfaceVariantLight,
    onSurfaceVariant = AppColors.OnSurfaceVariantLight,
    outline = AppColors.OutlineLight,
    error = AppColors.Danger,
    onError = AppColors.SurfaceLight,
    errorContainer = AppColors.DangerContainer,
    onErrorContainer = AppColors.Danger,
)

private val DarkScheme = darkColorScheme(
    primary = AppColors.BrandLight,
    onPrimary = AppColors.BackgroundDark,
    primaryContainer = AppColors.BrandContainerDark,
    onPrimaryContainer = AppColors.BrandLight,
    secondary = AppColors.OnSurfaceVariantDark,
    background = AppColors.BackgroundDark,
    onBackground = AppColors.OnSurfaceDark,
    surface = AppColors.SurfaceDark,
    onSurface = AppColors.OnSurfaceDark,
    surfaceVariant = AppColors.SurfaceVariantDark,
    onSurfaceVariant = AppColors.OnSurfaceVariantDark,
    outline = AppColors.OutlineDark,
    error = AppColors.DangerLight,
    onError = AppColors.BackgroundDark,
    errorContainer = AppColors.DangerContainerDark,
    onErrorContainer = AppColors.DangerLight,
)

/**
 * Material You dynamic colour is deliberately absent. Stop status is communicated by colour —
 * green delivered, red failed, blue pending — and letting the system rewrite the palette from
 * the user's wallpaper breaks that code exactly where it matters most.
 */
@Composable
fun MilkrunTheme(darkTheme: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    val scheme = if (darkTheme) DarkScheme else LightScheme
    val statusColors = if (darkTheme) DarkStatusColors else LightStatusColors

    CompositionLocalProvider(LocalStatusColors provides statusColors) {
        MaterialTheme(
            colorScheme = scheme,
            typography = AppTypography,
            content = content,
        )
    }
}
