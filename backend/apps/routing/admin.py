from django.contrib import admin

from .models import Route, RouteStop


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 0
    readonly_fields = ("leg_distance_km", "eta_minutes")
    autocomplete_fields = ("stop",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        "date", "vehicle", "driver", "status", "planned_distance_km", "planned_duration_minutes",
    )
    list_filter = ("status", "date", "depot")
    inlines = (RouteStopInline,)
    readonly_fields = ("optimizer_metrics", "created_at")
