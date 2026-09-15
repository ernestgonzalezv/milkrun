package com.milkrun.driver.di

import com.milkrun.core.network.api.AuthApi
import com.milkrun.core.network.api.AuthApiImpl
import com.milkrun.core.network.api.DriverApi
import com.milkrun.core.network.api.DriverApiImpl
import com.milkrun.core.network.client.HttpClientFactory
import com.milkrun.core.network.client.MilkrunJson
import com.milkrun.core.network.config.NetworkConfig
import com.milkrun.core.network.session.SessionTokenProvider
import com.milkrun.core.storage.session.SessionStore
import com.milkrun.driver.BuildConfig
import io.ktor.client.HttpClient
import kotlinx.serialization.json.Json
import org.koin.android.ext.koin.androidContext
import org.koin.dsl.module

val networkModule = module {
    single<Json> { MilkrunJson }

    single<NetworkConfig> {
        object : NetworkConfig {
            override val baseUrl = BuildConfig.API_URL
            override val isDebug = BuildConfig.DEBUG
        }
    }

    single { SessionStore(androidContext()) }
    single<SessionTokenProvider> { get<SessionStore>() }

    single<HttpClient> { HttpClientFactory.create(get(), get(), get()) }

    single<AuthApi> { AuthApiImpl(get()) }
    single<DriverApi> { DriverApiImpl(get()) }
}
