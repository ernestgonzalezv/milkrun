package com.milkrun.feature.auth.domain.usecase

import com.milkrun.feature.auth.domain.repository.AuthRepository
import kotlinx.coroutines.flow.Flow

class ObserveSessionUseCase(private val repository: AuthRepository) {
    operator fun invoke(): Flow<Boolean> = repository.isSignedIn
}
