package com.milkrun.driver.presentation.model

import androidx.annotation.StringRes
import com.milkrun.core.common.model.ErrorType
import com.milkrun.driver.R

/**
 * Presentation-side mapping of an [ErrorType] to something a driver can read.
 *
 * Repositories deliberately do not produce user-facing text: they classify the failure and let
 * this layer resolve the wording, so translations live with the rest of the strings.
 */
@JvmInline
value class UiError(@param:StringRes @get:StringRes val messageRes: Int) {

    companion object {
        fun fromErrorType(type: ErrorType): UiError = UiError(
            when (type) {
                ErrorType.NO_INTERNET -> R.string.error_no_internet
                ErrorType.NETWORK_ERROR -> R.string.error_network
                ErrorType.UNAUTHORIZED -> R.string.error_unauthorized
                ErrorType.NOT_FOUND -> R.string.error_not_found
                ErrorType.BUSINESS_ERROR -> R.string.error_business
                ErrorType.UNKNOWN_ERROR -> R.string.error_unknown
            },
        )
    }
}
