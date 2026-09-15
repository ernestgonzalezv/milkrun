package com.milkrun.feature.auth.domain.usecase

import com.milkrun.feature.auth.domain.repository.AuthRepository

class SignOutUseCase(private val repository: AuthRepository) {
    suspend operator fun invoke() = repository.signOut()
}
