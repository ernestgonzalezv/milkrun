package com.milkrun.feature.route.di

import com.milkrun.feature.route.data.repository.RouteRepositoryImpl
import com.milkrun.feature.route.domain.repository.RouteRepository
import com.milkrun.feature.route.domain.usecase.ObservePendingWorkUseCase
import com.milkrun.feature.route.domain.usecase.ObserveTodaysRouteUseCase
import com.milkrun.feature.route.domain.usecase.RecordDeliveryOutcomeUseCase
import com.milkrun.feature.route.domain.usecase.RecordLocationUseCase
import com.milkrun.feature.route.domain.usecase.RefreshRouteUseCase
import com.milkrun.feature.route.domain.usecase.SyncPendingWorkUseCase
import org.koin.dsl.module

val routeModule = module {
    single<RouteRepository> {
        RouteRepositoryImpl(get(), get(), get(), get(), get(), get(), get())
    }

    factory { ObserveTodaysRouteUseCase(get(), get()) }
    factory { ObservePendingWorkUseCase(get()) }
    factory { RefreshRouteUseCase(get(), get()) }
    factory { RecordDeliveryOutcomeUseCase(get()) }
    factory { RecordLocationUseCase(get()) }
    factory { SyncPendingWorkUseCase(get()) }
}
