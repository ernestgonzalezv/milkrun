package com.milkrun.core.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.milkrun.core.database.entity.CachedRouteEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface CachedRouteDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun save(route: CachedRouteEntity)

    @Query("SELECT * FROM cached_routes WHERE date = :date")
    fun observe(date: String): Flow<CachedRouteEntity?>

    @Query("DELETE FROM cached_routes WHERE date < :date")
    suspend fun deleteBefore(date: String)
}
