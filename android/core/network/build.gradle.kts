plugins {
    id("milkrun.android.library")
}

android {
    namespace = "com.milkrun.core.network"
}

dependencies {
    implementation(project(":core:common"))

    api(libs.ktor.client.core)
    implementation(libs.ktor.client.okhttp)
    implementation(libs.ktor.client.content.negotiation)
    implementation(libs.ktor.client.logging)
    implementation(libs.ktor.client.auth)
    implementation(libs.ktor.serialization.kotlinx.json)

    testImplementation(libs.ktor.client.mock)
}
