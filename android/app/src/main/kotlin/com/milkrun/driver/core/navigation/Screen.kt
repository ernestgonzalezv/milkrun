package com.milkrun.driver.core.navigation

sealed class Screen(val route: String) {
    data object Login : Screen("login")

    data object Route : Screen("route")
}
