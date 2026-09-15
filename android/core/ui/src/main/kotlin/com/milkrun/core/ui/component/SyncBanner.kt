package com.milkrun.core.ui.component

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import com.milkrun.core.ui.R
import com.milkrun.core.ui.theme.MilkrunIcons
import com.milkrun.core.ui.theme.MilkrunTheme

/**
 * Connection and queue state.
 *
 * The most important piece of an offline-first app: without it the driver cannot tell whether
 * what they marked reached the server or is still sitting on the phone, and that doubt is what
 * generates calls to the office.
 */
@Composable
fun SyncBanner(online: Boolean, pending: Int, uploading: Boolean, modifier: Modifier = Modifier) {
    when {
        !online -> Notice(
            text = if (pending > 0) {
                pluralStringResource(R.plurals.sync_offline_pending, pending, pending)
            } else {
                stringResource(R.string.sync_offline_idle)
            },
            tone = NoticeTone.WARNING,
            icon = MilkrunIcons.Offline,
            modifier = modifier,
        )

        uploading -> Notice(
            text = stringResource(R.string.sync_uploading),
            tone = NoticeTone.INFO,
            icon = MilkrunIcons.Syncing,
            modifier = modifier,
        )

        pending > 0 -> Notice(
            text = pluralStringResource(R.plurals.sync_pending, pending, pending),
            tone = NoticeTone.INFO,
            icon = MilkrunIcons.Info,
            modifier = modifier,
        )
    }
}

@Preview(name = "Offline with one queued", showBackground = true)
@Composable
private fun SyncBannerOfflineSinglePreview() {
    MilkrunTheme { SyncBanner(online = false, pending = 1, uploading = false) }
}

@Preview(name = "Offline with several queued", showBackground = true)
@Composable
private fun SyncBannerOfflineManyPreview() {
    MilkrunTheme { SyncBanner(online = false, pending = 4, uploading = false) }
}

@Preview(name = "Uploading", showBackground = true)
@Composable
private fun SyncBannerUploadingPreview() {
    MilkrunTheme { SyncBanner(online = true, pending = 2, uploading = true) }
}
