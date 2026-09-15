plugins {
    id("milkrun.android.feature")
}

android {
    namespace = "com.milkrun.feature.route"
}

dependencies {
    implementation(project(":core:network"))
    implementation(project(":core:database"))

    testImplementation(libs.ktor.client.mock)
}
