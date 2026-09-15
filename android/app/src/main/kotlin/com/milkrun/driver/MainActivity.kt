package com.milkrun.driver

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.milkrun.core.ui.theme.MilkrunTheme
import com.milkrun.driver.core.navigation.Screen
import com.milkrun.driver.presentation.navigation.MilkrunNavHost
import com.milkrun.feature.auth.domain.usecase.ObserveSessionUseCase
import org.koin.android.ext.android.inject

class MainActivity : ComponentActivity() {

    private val observeSession: ObserveSessionUseCase by inject()

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)

        setContent {
            val signedIn by observeSession().collectAsStateWithLifecycle(initialValue = false)

            MilkrunTheme {
                MilkrunNavHost(
                    startDestination = if (signedIn) Screen.Route.route else Screen.Login.route,
                )
            }
        }
    }
}
