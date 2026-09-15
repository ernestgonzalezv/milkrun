package com.milkrun.core.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.milkrun.core.database.entity.PendingPingEntity

@Dao
interface PendingPingDao {

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun enqueue(ping: PendingPingEntity)

    @Query("SELECT * FROM pending_pings ORDER BY recordedAt ASC LIMIT :limit")
    suspend fun pending(limit: Int = 200): List<PendingPingEntity>

    @Query("DELETE FROM pending_pings WHERE recordedAt IN (:timestamps)")
    suspend fun confirm(timestamps: List<String>)
}
