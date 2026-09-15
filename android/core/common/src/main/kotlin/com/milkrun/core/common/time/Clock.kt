package com.milkrun.core.common.time

import java.time.Instant
import java.time.LocalDate

/**
 * Injectable clock. Domain code never calls `Instant.now()` directly so that tests can
 * assert on exact timestamps instead of tolerating drift.
 */
interface Clock {
    fun now(): Instant

    fun today(): LocalDate
}

class SystemClock : Clock {
    override fun now(): Instant = Instant.now()

    override fun today(): LocalDate = LocalDate.now()
}
