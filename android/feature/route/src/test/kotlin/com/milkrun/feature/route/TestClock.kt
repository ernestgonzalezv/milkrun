package com.milkrun.feature.route

import com.milkrun.core.common.time.Clock
import java.time.Instant
import java.time.LocalDate

class TestClock(
    private val instant: Instant = Instant.parse("2026-09-12T14:10:18Z"),
    private val date: LocalDate = LocalDate.parse("2026-09-12"),
) : Clock {
    override fun now(): Instant = instant

    override fun today(): LocalDate = date
}
