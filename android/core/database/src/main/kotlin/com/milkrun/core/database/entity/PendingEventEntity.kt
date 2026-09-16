package com.milkrun.core.database.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * A delivery outcome the driver recorded that has not reached the server yet.
 *
 * `clientEventId` is generated on the phone before the first upload attempt. The server has a
 * unique constraint on it, so replaying the whole queue never duplicates anything, which is
 * what lets the upload policy be "retry until 2xx" with no reconciliation logic.
 */
@Entity(
    tableName = "pending_events",
    indices = [Index(value = ["clientEventId"], unique = true)],
)
data class PendingEventEntity(
    @PrimaryKey val clientEventId: String,
    val stopId: Int,
    val kind: String,
    val reason: String = "",
    val note: String = "",
    val latitude: Double? = null,
    val longitude: Double? = null,
    /** Device time in ISO-8601. This is what orders the events, not arrival time. */
    val occurredAt: String,
    val attempts: Int = 0,
    val lastError: String? = null,
)
