package com.milkrun.driver

import android.app.Application
import com.milkrun.driver.di.appModule
import com.milkrun.driver.di.networkModule
import com.milkrun.driver.di.viewModelModule
import com.milkrun.driver.sync.SyncWorker
import com.milkrun.feature.auth.di.authModule
import com.milkrun.feature.route.di.routeModule
import org.koin.android.ext.koin.androidContext
import org.koin.android.ext.koin.androidLogger
import org.koin.core.context.startKoin
import org.koin.core.logger.Level
import timber.log.Timber

class MilkrunApplication : Application() {

    override fun onCreate() {
        super.onCreate()

        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        }

        startKoin {
            androidLogger(if (BuildConfig.DEBUG) Level.INFO else Level.NONE)
            androidContext(this@MilkrunApplication)
            modules(appModule, networkModule, authModule, routeModule, viewModelModule)
        }

        SyncWorker.schedulePeriodic(this)
    }
}
