package com.milkrun.core.ui.component

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.tooling.preview.Preview
import com.milkrun.core.ui.theme.MilkrunIcons
import com.milkrun.core.ui.theme.MilkrunTheme
import com.milkrun.core.ui.theme.status
import com.milkrun.core.ui.tokens.AppRadius
import com.milkrun.core.ui.tokens.AppSize
import com.milkrun.core.ui.tokens.AppSpacing

@Composable
fun Notice(text: String, tone: NoticeTone, modifier: Modifier = Modifier, icon: ImageVector? = null) {
    val status = MaterialTheme.colorScheme.status
    val color = when (tone) {
        NoticeTone.INFO -> status.neutral
        NoticeTone.WARNING -> status.inProgress
        NoticeTone.ERROR -> status.failed
        NoticeTone.SUCCESS -> status.done
    }

    Row(
        modifier = modifier
            .background(color.container, RoundedCornerShape(AppRadius.md))
            .padding(horizontal = AppSpacing.md, vertical = AppSpacing.md),
        horizontalArrangement = Arrangement.spacedBy(AppSpacing.sm),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (icon != null) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color.content,
                modifier = Modifier.size(AppSize.icon),
            )
        }
        Text(text, style = MaterialTheme.typography.bodyMedium, color = color.content)
    }
}

@Preview(name = "Warning", showBackground = true)
@Composable
private fun NoticeWarningPreview() {
    MilkrunTheme {
        Notice(
            text = "Sin conexión. 3 entregas guardadas en el teléfono.",
            tone = NoticeTone.WARNING,
            icon = MilkrunIcons.Offline,
        )
    }
}

@Preview(name = "Error dark", showBackground = true, uiMode = android.content.res.Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun NoticeErrorPreview() {
    MilkrunTheme {
        Notice(text = "Usuario o contraseña incorrectos.", tone = NoticeTone.ERROR)
    }
}
