package com.milkrun.core.database.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * The day's route, stored as the raw payload.
 *
 * The app only ever reads it whole to render it and never queries parts of it, so normalising
 * it into tables would buy schema work and migrations in exchange for nothing.
 */
@Entity(tableName = "cached_routes")
data class CachedRouteEntity(@PrimaryKey val date: String, val payload: String, val savedAt: Long)
