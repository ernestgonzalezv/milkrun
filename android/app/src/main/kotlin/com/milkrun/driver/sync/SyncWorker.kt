package com.milkrun.driver.sync

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.milkrun.core.common.model.Resource
import com.milkrun.core.common.model.SyncOutcome
import com.milkrun.feature.auth.domain.usecase.ObserveSessionUseCase
import com.milkrun.feature.route.domain.usecase.RefreshRouteUseCase
import com.milkrun.feature.route.domain.usecase.SyncPendingWorkUseCase
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.last
import org.koin.core.component.KoinComponent
import org.koin.core.component.inject

private const val PERIODIC_WORK = "milkrun-sync-periodic"
private const val IMMEDIATE_WORK = "milkrun-sync-immediate"
private const val PERIOD_MINUTES = 15L
private const val PERIODIC_BACKOFF_SECONDS = 30L
private const val IMMEDIATE_BACKOFF_SECONDS = 15L

/**
 * Drains the offline queue when the network is back.
 *
 * WorkManager rather than a custom service: it survives the process being killed, respects Doze
 * and battery saver, and retries with backoff without any of that being hand-rolled. On a
 * delivery phone sitting in a pocket with the screen off, that is the difference between the
 * events arriving and them waiting until someone opens the app.
 */
class SyncWorker(context: Context, parameters: WorkerParameters) :
    CoroutineWorker(context, parameters),
    KoinComponent {

    private val syncPendingWork: SyncPendingWorkUseCase by inject()
    private val refreshRoute: RefreshRouteUseCase by inject()
    private val observeSession: ObserveSessionUseCase by inject()

    override suspend fun doWork(): Result {
        if (!observeSession().first()) return Result.success()

        val result = syncPendingWork().last()
        val outcome = (result as? Resource.Success)?.data

        return when {
            outcome is SyncOutcome.Failed && outcome.retryable -> Result.retry()
            outcome is SyncOutcome.Failed -> Result.failure()
            else -> {
                refreshRoute().last()
                Result.success()
            }
        }
    }

    companion object {
        private val onlyWhenConnected = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        /** Safety net at the shortest period WorkManager allows. */
        fun schedulePeriodic(context: Context) {
            val request = PeriodicWorkRequestBuilder<SyncWorker>(PERIOD_MINUTES, TimeUnit.MINUTES)
                .setConstraints(onlyWhenConnected)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    PERIODIC_BACKOFF_SECONDS,
                    TimeUnit.SECONDS,
                )
                .build()

            WorkManager.getInstance(context)
                .enqueueUniquePeriodicWork(PERIODIC_WORK, ExistingPeriodicWorkPolicy.KEEP, request)
        }

        fun push(context: Context) {
            val request = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(onlyWhenConnected)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    IMMEDIATE_BACKOFF_SECONDS,
                    TimeUnit.SECONDS,
                )
                .build()

            WorkManager.getInstance(context).enqueueUniqueWork(
                IMMEDIATE_WORK,
                ExistingWorkPolicy.APPEND_OR_REPLACE,
                request,
            )
        }
    }
}
