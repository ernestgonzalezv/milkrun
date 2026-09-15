package com.milkrun.core.database.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/** A ping needs no generated id: its own timestamp identifies it. */
@Entity(tableName = "pending_pings")
data class PendingPingEntity(
    @PrimaryKey val recordedAt: String,
    val latitude: Double,
    val longitude: Double,
    val accuracyM: Double? = null,
    val speedKmh: Double? = null,
)
