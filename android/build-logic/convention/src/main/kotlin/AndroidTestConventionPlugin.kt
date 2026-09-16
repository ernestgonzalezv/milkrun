import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.tasks.testing.Test
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.register
import org.gradle.kotlin.dsl.withType
import org.gradle.testing.jacoco.plugins.JacocoTaskExtension
import org.gradle.testing.jacoco.tasks.JacocoReport

/**
 * JUnit 5 plus JaCoCo for every module that has tests.
 *
 * The exclusions below are generated code: Compose singletons, Room implementations,
 * Koin modules, R and BuildConfig. Counting them measures the code generators, not
 * the code anyone wrote.
 */
private val GENERATED = listOf(
    "**/R.class",
    "**/R\$*.class",
    "**/BuildConfig.*",
    "**/Manifest*.*",
    "**/*Test*.*",
    "**/*_Impl*.*",
    "**/ComposableSingletons*.*",
    "**/*\$\$serializer*.*",
    "**/*Preview*.*",
    "**/di/**",
)

class AndroidTestConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply("jacoco")

            tasks.withType<Test>().configureEach {
                useJUnitPlatform()
                extensions.configure(JacocoTaskExtension::class.java) {
                    isIncludeNoLocationClasses = true
                    excludes = listOf("jdk.internal.*")
                }
            }

            tasks.register<JacocoReport>("coverageReport") {
                group = "verification"
                description = "JaCoCo coverage for the debug unit tests of this module"
                dependsOn("testDebugUnitTest")

                reports {
                    xml.required.set(true)
                    html.required.set(true)
                    csv.required.set(false)
                }

                // AGP 9 compiles with its built-in Kotlin compiler and writes to
                // built_in_kotlinc. The other patterns cover older layouts, so the
                // report does not come out empty after a toolchain bump.
                classDirectories.setFrom(
                    layout.buildDirectory.map { build ->
                        fileTree(build) {
                            include(
                                "intermediates/built_in_kotlinc/debug/compileDebugKotlin/classes/**/*.class",
                                "tmp/kotlin-classes/debug/**/*.class",
                                "intermediates/javac/debug/**/*.class",
                            )
                            exclude(GENERATED)
                        }
                    },
                )
                sourceDirectories.setFrom(files("src/main/kotlin", "src/main/java"))
                executionData.setFrom(
                    layout.buildDirectory.map { dir ->
                        fileTree(dir) { include("**/*.exec") }
                    },
                )
            }

            dependencies {
                "testImplementation"(libs.findLibrary("junit-jupiter-api").get())
                "testImplementation"(libs.findLibrary("junit-jupiter-params").get())
                "testImplementation"(libs.findLibrary("mockito-kotlin").get())
                "testImplementation"(libs.findLibrary("kotlinx-coroutines-test").get())
                "testImplementation"(libs.findLibrary("turbine").get())
                "testRuntimeOnly"(libs.findLibrary("junit-jupiter-engine").get())
                "testRuntimeOnly"(libs.findLibrary("junit-platform-launcher").get())
            }
        }
    }
}
