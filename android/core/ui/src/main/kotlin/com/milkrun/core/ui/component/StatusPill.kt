package com.milkrun.core.ui.component

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import com.milkrun.core.ui.theme.MilkrunTheme
import com.milkrun.core.ui.theme.status
import com.milkrun.core.ui.tokens.AppRadius
import com.milkrun.core.ui.tokens.AppSpacing

@Composable
fun StatusPill(label: String, container: Color, content: Color, modifier: Modifier = Modifier) {
    Text(
        text = label,
        style = MaterialTheme.typography.labelMedium,
        color = content,
        modifier = modifier
            .background(container, RoundedCornerShape(AppRadius.pill))
            .padding(horizontal = AppSpacing.sm, vertical = AppSpacing.xxs),
    )
}

@Preview(showBackground = true)
@Composable
private fun StatusPillPreview() {
    MilkrunTheme {
        val failed = MaterialTheme.colorScheme.status.failed
        StatusPill(label = "No se pudo", container = failed.container, content = failed.content)
    }
}
