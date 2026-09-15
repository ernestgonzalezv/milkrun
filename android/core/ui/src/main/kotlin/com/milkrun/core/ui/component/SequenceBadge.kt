package com.milkrun.core.ui.component

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.tooling.preview.Preview
import com.milkrun.core.ui.theme.MilkrunTheme
import com.milkrun.core.ui.theme.status
import com.milkrun.core.ui.tokens.AppSize

/**
 * Position of a stop inside the route. Marked as decorative for screen readers because the row
 * already announces "stop 3 of 24" as a whole.
 */
@Composable
fun SequenceBadge(sequence: Int, container: Color, content: Color, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .size(AppSize.badge)
            .background(container, CircleShape)
            .clearAndSetSemantics { },
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = sequence.toString(),
            style = MaterialTheme.typography.labelLarge,
            color = content,
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun SequenceBadgePreview() {
    MilkrunTheme {
        val done = MaterialTheme.colorScheme.status.done
        SequenceBadge(sequence = 7, container = done.container, content = done.content)
    }
}
