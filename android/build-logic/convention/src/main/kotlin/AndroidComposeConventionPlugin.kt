import com.android.build.api.dsl.LibraryExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

class AndroidComposeConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply("org.jetbrains.kotlin.plugin.compose")

            extensions.configure<LibraryExtension> {
                buildFeatures {
                    compose = true
                }
            }

            val bom = dependencies.platform(libs.findLibrary("androidx-compose-bom").get())

            dependencies {
                "implementation"(bom)
                "implementation"(libs.findLibrary("androidx-ui").get())
                "implementation"(libs.findLibrary("androidx-ui-graphics").get())
                "implementation"(libs.findLibrary("androidx-ui-tooling-preview").get())
                "implementation"(libs.findLibrary("androidx-material3").get())
                "debugImplementation"(libs.findLibrary("androidx-ui-tooling").get())
            }
        }
    }
}
