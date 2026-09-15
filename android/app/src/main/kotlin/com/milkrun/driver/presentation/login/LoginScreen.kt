package com.milkrun.driver.presentation.login

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.milkrun.core.common.model.states.OperationState
import com.milkrun.core.ui.component.Notice
import com.milkrun.core.ui.component.NoticeTone
import com.milkrun.core.ui.theme.MilkrunTheme
import com.milkrun.core.ui.tokens.AppSize
import com.milkrun.core.ui.tokens.AppSpacing
import com.milkrun.driver.R
import com.milkrun.feature.auth.domain.model.Credentials
import org.koin.androidx.compose.koinViewModel

@Composable
fun LoginScreen(onSignedIn: () -> Unit, modifier: Modifier = Modifier, viewModel: LoginViewModel = koinViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val error by viewModel.error.collectAsStateWithLifecycle()

    LaunchedEffect(state) {
        if (state is OperationState.Success) onSignedIn()
    }

    LoginContent(
        submitting = state is OperationState.Loading,
        errorMessage = error?.messageRes?.let { stringResource(it) },
        onSubmit = viewModel::signIn,
        modifier = modifier,
    )
}

@Composable
private fun LoginContent(
    submitting: Boolean,
    errorMessage: String?,
    onSubmit: (Credentials) -> Unit,
    modifier: Modifier = Modifier,
) {
    var username by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    val credentials = Credentials(username, password)

    Scaffold(modifier = modifier) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .imePadding()
                .padding(horizontal = AppSpacing.xl, vertical = AppSpacing.xxl),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Column(
                modifier = Modifier.widthIn(max = AppSize.formMaxWidth).fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(AppSpacing.lg),
            ) {
                LoginHeader()
                CredentialFields(
                    username = username,
                    password = password,
                    enabled = !submitting,
                    onUsernameChange = { username = it },
                    onPasswordChange = { password = it },
                    onDone = { onSubmit(credentials) },
                )
                if (errorMessage != null) LoginError(errorMessage)
                SubmitButton(
                    submitting = submitting,
                    enabled = credentials.isComplete && !submitting,
                    onClick = { onSubmit(credentials) },
                )
                LoginHint()
            }
        }
    }
}

@Composable
private fun CredentialFields(
    username: String,
    password: String,
    enabled: Boolean,
    onUsernameChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onDone: () -> Unit,
) {
    OutlinedTextField(
        value = username,
        onValueChange = onUsernameChange,
        label = { Text(stringResource(R.string.login_username)) },
        singleLine = true,
        enabled = enabled,
        keyboardOptions = KeyboardOptions(
            keyboardType = KeyboardType.Text,
            imeAction = ImeAction.Next,
        ),
        modifier = Modifier.fillMaxWidth(),
    )

    OutlinedTextField(
        value = password,
        onValueChange = onPasswordChange,
        label = { Text(stringResource(R.string.login_password)) },
        singleLine = true,
        enabled = enabled,
        visualTransformation = PasswordVisualTransformation(),
        keyboardOptions = KeyboardOptions(
            keyboardType = KeyboardType.Password,
            imeAction = ImeAction.Done,
        ),
        keyboardActions = KeyboardActions(onDone = { onDone() }),
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
private fun LoginError(message: String) {
    Notice(
        text = message,
        tone = NoticeTone.ERROR,
        modifier = Modifier
            .fillMaxWidth()
            .semantics { liveRegion = LiveRegionMode.Assertive },
    )
}

@Composable
private fun SubmitButton(submitting: Boolean, enabled: Boolean, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier.fillMaxWidth().height(AppSize.primaryButton),
    ) {
        if (submitting) {
            CircularProgressIndicator(
                modifier = Modifier.height(AppSize.icon),
                strokeWidth = AppSpacing.xxs,
                color = MaterialTheme.colorScheme.onPrimary,
            )
        } else {
            Text(stringResource(R.string.login_submit))
        }
    }
}

@Composable
private fun LoginHeader() {
    Column(verticalArrangement = Arrangement.spacedBy(AppSpacing.xs)) {
        Text(
            text = stringResource(R.string.login_title),
            style = MaterialTheme.typography.headlineSmall,
        )
        Text(
            text = stringResource(R.string.login_subtitle),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun LoginHint() {
    Text(
        text = stringResource(R.string.login_demo_hint),
        style = MaterialTheme.typography.labelMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

@Preview(name = "Idle", showBackground = true)
@Composable
private fun LoginIdlePreview() {
    MilkrunTheme {
        LoginContent(submitting = false, errorMessage = null, onSubmit = {})
    }
}

@Preview(name = "Error", showBackground = true)
@Composable
private fun LoginErrorPreview() {
    MilkrunTheme {
        LoginContent(
            submitting = false,
            errorMessage = "Usuario o contraseña incorrectos.",
            onSubmit = {},
        )
    }
}

@Preview(
    name = "Submitting dark",
    showBackground = true,
    uiMode = android.content.res.Configuration.UI_MODE_NIGHT_YES,
)
@Composable
private fun LoginSubmittingPreview() {
    MilkrunTheme {
        LoginContent(submitting = true, errorMessage = null, onSubmit = {})
    }
}
