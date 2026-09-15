package com.milkrun.core.database.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/** Locally known status of a stop, so the screen reacts before the network does. */
@Entity(tableName = "local_stop_states")
data class LocalStopStateEntity(@PrimaryKey val stopId: Int, val status: String, val updatedAt: Long)
