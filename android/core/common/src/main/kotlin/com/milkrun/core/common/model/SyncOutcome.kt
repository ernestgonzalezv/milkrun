package com.milkrun.core.common.model

/**
 * Result of draining the offline queue.
 *
 * [retryable] tells the caller whether waiting changes anything: a lost connection resolves
 * itself, a 4xx does not, and retrying it forever would spin the worker without progress.
 */
sealed class SyncOutcome {
    data class Synced(val uploaded: Int, val duplicates: Int) : SyncOutcome()

    data object NothingPending : SyncOutcome()

    data class Failed(val reason: String, val retryable: Boolean) : SyncOutcome()
}
