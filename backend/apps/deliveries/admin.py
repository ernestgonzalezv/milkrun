from django.contrib import admin

from .models import DeliveryEvent, LocationPing, Stop


class DeliveryEventInline(admin.TabularInline):
    model = DeliveryEvent
    extra = 0
    can_delete = False  # la bitacora es append-only tambien desde el admin
    readonly_fields = ("kind", "reason", "note", "driver", "occurred_at", "received_at")

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ("tracking_code", "customer_name", "address", "scheduled_date", "status")
    list_filter = ("status", "scheduled_date", "depot")
    search_fields = ("tracking_code", "customer_name", "address", "phone")
    readonly_fields = ("tracking_code", "status", "created_at", "updated_at")
    inlines = (DeliveryEventInline,)


@admin.register(DeliveryEvent)
class DeliveryEventAdmin(admin.ModelAdmin):
    list_display = ("stop", "kind", "driver", "occurred_at", "received_at")
    list_filter = ("kind", "reason")
    search_fields = ("stop__tracking_code",)
    readonly_fields = tuple(f.name for f in DeliveryEvent._meta.fields)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


@admin.register(LocationPing)
class LocationPingAdmin(admin.ModelAdmin):
    list_display = ("driver", "recorded_at", "latitude", "longitude", "speed_kmh")
    list_filter = ("driver",)
