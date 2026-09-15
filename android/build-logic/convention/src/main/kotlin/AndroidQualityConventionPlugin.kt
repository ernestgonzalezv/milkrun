import com.diffplug.gradle.spotless.SpotlessExtension
import dev.detekt.gradle.Detekt
import dev.detekt.gradle.extensions.DetektExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.withType

class AndroidQualityConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("dev.detekt")
                apply("com.diffplug.spotless")
            }

            extensions.configure<DetektExtension> {
                buildUponDefaultConfig.set(true)
                config.setFrom(rootProject.files("config/detekt/detekt.yml"))
                parallel.set(true)
            }

            tasks.withType<Detekt>().configureEach {
                reports {
                    html.required.set(true)
                    sarif.required.set(true)
                }
            }

            val ktlintVersion = libs.findVersion("ktlint").get().toString()
            val editorConfig = mapOf(
                "max_line_length" to "120",
                "ktlint_code_style" to "android_studio",
                // Composables are PascalCase by Compose contract, not a naming violation.
                "ktlint_function_naming_ignore_when_annotated_with" to "Composable",
            )

            extensions.configure<SpotlessExtension> {
                kotlin {
                    target("**/*.kt")
                    targetExclude("**/build/**")
                    ktlint(ktlintVersion).editorConfigOverride(editorConfig)
                    trimTrailingWhitespace()
                    endWithNewline()
                }
                kotlinGradle {
                    target("**/*.gradle.kts")
                    targetExclude("**/build/**")
                    ktlint(ktlintVersion).editorConfigOverride(editorConfig)
                }
            }
        }
    }
}
