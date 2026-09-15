plugins {
    `kotlin-dsl`
}

dependencies {
    compileOnly(libs.plugins.android.library.toDep())
    compileOnly(libs.plugins.kotlin.compose.toDep())
    compileOnly(libs.plugins.kotlin.serialization.toDep())
    compileOnly(libs.plugins.ksp.toDep())
    compileOnly(libs.plugins.detekt.toDep())
    compileOnly(libs.plugins.spotless.toDep())
}

fun Provider<PluginDependency>.toDep() = map {
    "${it.pluginId}:${it.pluginId}.gradle.plugin:${it.version}"
}

gradlePlugin {
    plugins {
        register("androidLibrary") {
            id = "milkrun.android.library"
            implementationClass = "AndroidLibraryConventionPlugin"
        }
        register("androidCompose") {
            id = "milkrun.android.compose"
            implementationClass = "AndroidComposeConventionPlugin"
        }
        register("androidFeature") {
            id = "milkrun.android.feature"
            implementationClass = "AndroidFeatureConventionPlugin"
        }
        register("androidTest") {
            id = "milkrun.android.test"
            implementationClass = "AndroidTestConventionPlugin"
        }
        register("androidQuality") {
            id = "milkrun.android.quality"
            implementationClass = "AndroidQualityConventionPlugin"
        }
    }
}
