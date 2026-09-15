plugins {
    id("milkrun.android.feature")
}

android {
    namespace = "com.milkrun.feature.auth"
}

dependencies {
    implementation(project(":core:network"))

    testImplementation(libs.ktor.client.mock)
}
