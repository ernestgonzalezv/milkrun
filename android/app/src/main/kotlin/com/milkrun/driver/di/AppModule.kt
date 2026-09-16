package com.milkrun.driver.di

import com.milkrun.core.common.time.Clock
import com.milkrun.core.common.time.SystemClock
import com.milkrun.core.database.MilkrunDatabaseProvider
import org.koin.android.ext.koin.androidContext
import org.koin.dsl.module

val appModule = module {
    single<Clock> { SystemClock() }
    single { MilkrunDatabaseProvider(androidContext()) }

    single { get<MilkrunDatabaseProvider>().pendingEvents() }
    single { get<MilkrunDatabaseProvider>().pendingPings() }
    single { get<MilkrunDatabaseProvider>().cachedRoutes() }
    single { get<MilkrunDatabaseProvider>().localStopStates() }
}
