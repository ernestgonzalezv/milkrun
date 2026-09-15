package com.milkrun.core.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.milkrun.core.database.entity.LocalStopStateEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface LocalStopStateDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun save(state: LocalStopStateEntity)

    @Query("SELECT * FROM local_stop_states")
    fun observeAll(): Flow<List<LocalStopStateEntity>>

    @Query("DELETE FROM local_stop_states WHERE updatedAt < :threshold")
    suspend fun deleteOlderThan(threshold: Long)
}
