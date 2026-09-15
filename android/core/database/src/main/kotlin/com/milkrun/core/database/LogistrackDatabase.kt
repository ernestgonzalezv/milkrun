package com.milkrun.core.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.milkrun.core.database.dao.CachedRouteDao
import com.milkrun.core.database.dao.LocalStopStateDao
import com.milkrun.core.database.dao.PendingEventDao
import com.milkrun.core.database.dao.PendingPingDao
import com.milkrun.core.database.entity.CachedRouteEntity
import com.milkrun.core.database.entity.LocalStopStateEntity
import com.milkrun.core.database.entity.PendingEventEntity
import com.milkrun.core.database.entity.PendingPingEntity

@Database(
    entities = [
        PendingEventEntity::class,
        PendingPingEntity::class,
        CachedRouteEntity::class,
        LocalStopStateEntity::class,
    ],
    version = 1,
    exportSchema = true,
)
internal abstract class MilkrunDatabase : RoomDatabase() {

    abstract fun pendingEvents(): PendingEventDao

    abstract fun pendingPings(): PendingPingDao

    abstract fun cachedRoutes(): CachedRouteDao

    abstract fun localStopStates(): LocalStopStateDao
}

/**
 * The only public surface of this module.
 *
 * Room itself — `RoomDatabase`, the builder, the generated implementation — stays internal, so
 * no other module ends up with Room on its compile classpath just to reach a DAO.
 */
class MilkrunDatabaseProvider(context: Context) {

    // No `fallbackToDestructiveMigration`. This database holds deliveries that have not reached
    // the server; wiping it on an app update would destroy a driver's work.
    private val database: MilkrunDatabase =
        Room.databaseBuilder(context, MilkrunDatabase::class.java, "milkrun.db").build()

    fun pendingEvents(): PendingEventDao = database.pendingEvents()

    fun pendingPings(): PendingPingDao = database.pendingPings()

    fun cachedRoutes(): CachedRouteDao = database.cachedRoutes()

    fun localStopStates(): LocalStopStateDao = database.localStopStates()
}
