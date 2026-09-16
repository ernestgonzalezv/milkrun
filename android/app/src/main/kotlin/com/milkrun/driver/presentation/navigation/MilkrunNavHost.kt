package com.milkrun.driver.presentation.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.milkrun.driver.core.navigation.Screen
import com.milkrun.driver.presentation.login.LoginScreen
import com.milkrun.driver.presentation.route.RouteScreen

@Composable
fun MilkrunNavHost(startDestination: String, modifier: Modifier = Modifier) {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier,
    ) {
        composable(Screen.Login.route) {
            LoginScreen(
                onSignedIn = {
                    navController.navigate(Screen.Route.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                },
            )
        }

        composable(Screen.Route.route) {
            RouteScreen(
                onSignedOut = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(Screen.Route.route) { inclusive = true }
                    }
                },
            )
        }
    }
}
