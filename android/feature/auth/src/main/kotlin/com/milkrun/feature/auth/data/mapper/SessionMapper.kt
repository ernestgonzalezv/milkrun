package com.milkrun.feature.auth.data.mapper

import com.milkrun.core.network.dto.auth.UserResponse
import com.milkrun.feature.auth.domain.model.DriverRole
import com.milkrun.feature.auth.domain.model.DriverSession

fun UserResponse.toDomain(): DriverSession = DriverSession(
    id = id,
    username = username,
    fullName = fullName,
    role = DriverRole.from(role),
)
