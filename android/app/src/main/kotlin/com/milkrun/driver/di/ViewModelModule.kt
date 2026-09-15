package com.milkrun.driver.di

import com.milkrun.driver.presentation.login.LoginViewModel
import com.milkrun.driver.presentation.route.RouteViewModel
import org.koin.core.module.dsl.viewModel
import org.koin.dsl.module

val viewModelModule = module {
    viewModel { LoginViewModel(get()) }
    viewModel { RouteViewModel(get(), get(), get(), get(), get(), get()) }
}
