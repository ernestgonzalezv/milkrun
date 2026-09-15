package com.milkrun.feature.auth.di

import com.milkrun.feature.auth.data.repository.AuthRepositoryImpl
import com.milkrun.feature.auth.domain.repository.AuthRepository
import com.milkrun.feature.auth.domain.usecase.ObserveSessionUseCase
import com.milkrun.feature.auth.domain.usecase.SignInUseCase
import com.milkrun.feature.auth.domain.usecase.SignOutUseCase
import org.koin.dsl.module

val authModule = module {
    single<AuthRepository> { AuthRepositoryImpl(get(), get()) }

    factory { SignInUseCase(get()) }
    factory { SignOutUseCase(get()) }
    factory { ObserveSessionUseCase(get()) }
}
