plugins {
    id("milkrun.android.library")
    id("milkrun.android.compose")
}

android {
    namespace = "com.milkrun.core.ui"
}

dependencies {
    implementation(project(":core:common"))

    implementation(libs.androidx.material.icons.extended)
    implementation(libs.androidx.lifecycle.runtime.compose)
}
