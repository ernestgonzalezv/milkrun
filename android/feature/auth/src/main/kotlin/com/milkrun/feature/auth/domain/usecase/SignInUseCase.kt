package com.milkrun.feature.auth.domain.usecase

import com.milkrun.core.common.model.Resource
import com.milkrun.feature.auth.domain.model.Credentials
import com.milkrun.feature.auth.domain.model.DriverSession
import com.milkrun.feature.auth.domain.repository.AuthRepository
import kotlinx.coroutines.flow.Flow

class SignInUseCase(private val repository: AuthRepository) {
    operator fun invoke(credentials: Credentials): Flow<Resource<DriverSession>> = repository.signIn(credentials)
}
