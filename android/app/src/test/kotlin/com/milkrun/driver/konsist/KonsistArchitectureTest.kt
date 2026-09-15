package com.milkrun.driver.konsist

import com.lemonappdev.konsist.api.Konsist
import com.lemonappdev.konsist.api.ext.list.modifierprovider.withPublicOrDefaultModifier
import com.lemonappdev.konsist.api.ext.list.properties
import com.lemonappdev.konsist.api.ext.list.withNameEndingWith
import com.lemonappdev.konsist.api.verify.assertFalse
import com.lemonappdev.konsist.api.verify.assertTrue
import org.junit.jupiter.api.Test

/**
 * The architecture rules, enforced.
 *
 * A convention that lives only in a document erodes on the first hurried afternoon. These fail
 * the build instead. When one fails, fix the code — never the test.
 */
class KonsistArchitectureTest {

    private val scope = Konsist.scopeFromProject()

    @Test
    fun `domain layer is pure Kotlin - no Android dependencies`() {
        scope
            .files
            .filter { it.path.contains("/domain/") && it.path.contains("/src/main/") }
            .assertFalse { file ->
                file.imports.any {
                    it.name.startsWith("android.") || it.name.startsWith("androidx.")
                }
            }
    }

    @Test
    fun `domain layer does not know the DI container, the network or the database`() {
        scope
            .files
            .filter { it.path.contains("/domain/") && it.path.contains("/src/main/") }
            .assertFalse { file ->
                file.imports.any {
                    it.name.startsWith("org.koin") ||
                        it.name.startsWith("io.ktor") ||
                        it.name.startsWith("com.milkrun.core.network") ||
                        it.name.startsWith("com.milkrun.core.database")
                }
            }
    }

    @Test
    fun `presentation layer speaks domain models, never network DTOs`() {
        scope
            .files
            .filter { it.path.contains("/presentation/") && it.path.contains("/src/main/") }
            .assertFalse { file -> file.imports.any { it.name.contains(".network.dto.") } }
    }

    @Test
    fun `feature modules never import another feature`() {
        scope
            .files
            .filter { it.path.contains("/feature/") && it.path.contains("/src/main/") }
            .assertFalse { file ->
                val own = file.path.substringAfter("/feature/").substringBefore("/")
                file.imports.any { import ->
                    val match = Regex("""com\.milkrun\.feature\.(\w+)""").find(import.name)
                    match != null && match.groupValues[1] != own
                }
            }
    }

    @Test
    fun `core modules never depend on features`() {
        scope
            .files
            .filter { it.path.contains("/core/") && it.path.contains("/src/main/") }
            .assertFalse { file ->
                file.imports.any { it.name.startsWith("com.milkrun.feature") }
            }
    }

    @Test
    fun `no Hilt or javax inject - Koin only`() {
        scope
            .files
            .assertFalse { file ->
                file.imports.any {
                    it.name.startsWith("javax.inject.") || it.name.startsWith("dagger.")
                }
            }
    }

    @Test
    fun `no LiveData - StateFlow only`() {
        scope
            .files
            .assertFalse { file ->
                file.imports.any {
                    it.name.startsWith("androidx.lifecycle.LiveData") ||
                        it.name.startsWith("androidx.lifecycle.MutableLiveData")
                }
            }
    }

    @Test
    fun `view models expose immutable state - MutableStateFlow is never public`() {
        scope
            .classes()
            .withNameEndingWith("ViewModel")
            .properties()
            .withPublicOrDefaultModifier()
            .assertFalse { property ->
                property.type?.name?.startsWith("MutableStateFlow") == true ||
                    property.type?.name?.startsWith("MutableSharedFlow") == true
            }
    }

    @Test
    fun `view models own no Compose state - no mutableStateOf`() {
        scope
            .classes()
            .withNameEndingWith("ViewModel")
            .assertFalse { it.text.contains("mutableStateOf(") }
    }

    @Test
    fun `repository interfaces live in domain and implementations in data`() {
        scope
            .interfaces()
            .withNameEndingWith("Repository")
            .assertTrue { it.resideInPackage("..domain.repository..") }

        scope
            .classes()
            .withNameEndingWith("RepositoryImpl")
            .assertTrue { it.resideInPackage("..data.repository..") }
    }

    @Test
    fun `raw colour literals stay inside the design system module`() {
        scope
            .files
            .filter { it.path.contains("/src/main/") }
            .filterNot { it.path.contains("/core/ui/") }
            .assertFalse { it.text.contains(Regex("""Color\(0x[0-9A-Fa-f]{8}\)""")) }
    }

    @Test
    fun `production code logs through Timber, never through android Log`() {
        scope
            .files
            .filter { it.path.contains("/src/main/") }
            .assertFalse { file -> file.imports.any { it.name == "android.util.Log" } }
    }
}
