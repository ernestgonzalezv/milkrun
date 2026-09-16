package com.milkrun.core.ui.theme

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.Directions
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Sync
import androidx.compose.ui.graphics.vector.ImageVector

/**
 * Semantic icon set. Screens name the role, not the glyph, so swapping icon packs later does
 * not touch every file.
 */
object MilkrunIcons {
    val Offline: ImageVector = Icons.Default.CloudOff
    val Syncing: ImageVector = Icons.Default.Sync
    val Info: ImageVector = Icons.Default.Info
    val Refresh: ImageVector = Icons.Default.Refresh
    val SignOut: ImageVector = Icons.AutoMirrored.Filled.Logout
    val Call: ImageVector = Icons.Default.Call
    val Navigate: ImageVector = Icons.Default.Directions
}
