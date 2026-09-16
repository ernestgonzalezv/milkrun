plugins {
    id("milkrun.android.library")
    alias(libs.plugins.ksp)
}

android {
    namespace = "com.milkrun.core.database"
}

ksp {
    arg("room.schemaLocation", "$projectDir/schemas")
}

dependencies {
    implementation(project(":core:common"))

    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    ksp(libs.room.compiler)

    testImplementation(libs.room.testing)
}
