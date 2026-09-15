package com.milkrun.feature.route.domain.model

data class Stop(
    val id: Int,
    val trackingCode: String,
    val customerName: String,
    val address: String,
    val coordinates: Coordinates,
    val demand: Double,
    val status: StopStatus,
    val phone: String = "",
    val notes: String = "",
)
