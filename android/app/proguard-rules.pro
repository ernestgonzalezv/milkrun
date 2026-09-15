# kotlinx.serialization resolves serializers by class name at runtime; without this R8 renames
# them and parsing breaks only in release builds.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**
-keepclassmembers class com.milkrun.core.network.dto.** {
    *** Companion;
}
-keepclasseswithmembers class com.milkrun.core.network.dto.** {
    kotlinx.serialization.KSerializer serializer(...);
}
