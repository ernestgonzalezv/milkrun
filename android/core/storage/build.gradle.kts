plugins {
    id("milkrun.android.library")
}

android {
    namespace = "com.milkrun.core.storage"
}

dependencies {
    implementation(project(":core:common"))
    implementation(project(":core:network"))

    implementation(libs.datastore)
}
