package com.milkrun.core.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.milkrun.core.database.entity.PendingEventEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface PendingEventDao {

    /**
     * IGNORE, not REPLACE: if the event is already queued the original row — with its real
     * device timestamp and its retry history — is the one that matters.
     */
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun enqueue(event: PendingEventEntity): Long

    @Query("SELECT * FROM pending_events ORDER BY occurredAt ASC LIMIT :limit")
    suspend fun pending(limit: Int = 200): List<PendingEventEntity>

    @Query("SELECT COUNT(*) FROM pending_events")
    fun pendingCount(): Flow<Int>

    @Query("DELETE FROM pending_events WHERE clientEventId IN (:ids)")
    suspend fun confirm(ids: List<String>)

    @Query(
        "UPDATE pending_events SET attempts = attempts + 1, lastError = :error " +
            "WHERE clientEventId IN (:ids)",
    )
    suspend fun markFailed(ids: List<String>, error: String)
}
