plugins {
    id("milkrun.android.library")
    alias(libs.plugins.ksp)
}

android {
    namespace = "com.milkrun.core.database"
}

// Room's schema is exported to a versioned JSON so migration tests can assert against the real
// previous shape instead of a reconstruction from memory.
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
