package com.milkrun.core.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * Colour primitives. The only file in the codebase allowed to hold raw values, everywhere
 * else reads meaning through `MaterialTheme.colorScheme` or the extensions below.
 *
 * Shared one-for-one with the web dashboard tokens so both surfaces read as one product.
 */
internal object AppColors {
    val Brand = Color(0xFF0B5FFF)
    val BrandLight = Color(0xFF4D8BFF)
    val BrandContainer = Color(0xFFE8F0FF)
    val BrandContainerDark = Color(0xFF14243F)

    val Success = Color(0xFF0F7B4F)
    val SuccessLight = Color(0xFF48C78E)
    val SuccessContainer = Color(0xFFE3F5EC)
    val SuccessContainerDark = Color(0xFF10281F)

    val Warning = Color(0xFFA8620A)
    val WarningLight = Color(0xFFE0A44A)
    val WarningContainer = Color(0xFFFDF0DD)
    val WarningContainerDark = Color(0xFF2A2113)

    val Danger = Color(0xFFB3261E)
    val DangerLight = Color(0xFFF2706A)
    val DangerContainer = Color(0xFFFCE9E7)
    val DangerContainerDark = Color(0xFF2D1614)

    val SurfaceLight = Color(0xFFFFFFFF)
    val SurfaceVariantLight = Color(0xFFF0F2F5)
    val BackgroundLight = Color(0xFFF6F7F9)
    val OnSurfaceLight = Color(0xFF16191D)
    val OnSurfaceVariantLight = Color(0xFF5B6470)
    val OutlineLight = Color(0xFFDFE3E8)

    val SurfaceDark = Color(0xFF171B21)
    val SurfaceVariantDark = Color(0xFF1E242C)
    val BackgroundDark = Color(0xFF101317)
    val OnSurfaceDark = Color(0xFFE8ECF1)
    val OnSurfaceVariantDark = Color(0xFFA3ADBA)
    val OutlineDark = Color(0xFF2A323C)
}
