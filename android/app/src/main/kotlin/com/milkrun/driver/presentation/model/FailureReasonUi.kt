package com.milkrun.driver.presentation.model

import androidx.annotation.StringRes
import com.milkrun.driver.R
import com.milkrun.feature.route.domain.model.FailureReason

@get:StringRes
val FailureReason.labelRes: Int
    get() = when (this) {
        FailureReason.ABSENT -> R.string.reason_absent
        FailureReason.WRONG_ADDRESS -> R.string.reason_wrong_address
        FailureReason.REFUSED -> R.string.reason_refused
        FailureReason.NO_ACCESS -> R.string.reason_no_access
        FailureReason.OTHER -> R.string.reason_other
    }
