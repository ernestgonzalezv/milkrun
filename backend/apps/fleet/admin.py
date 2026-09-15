from django.contrib import admin

from .models import Depot, DriverProfile, Vehicle


@admin.register(Depot)
class DepotAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "latitude", "longitude", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "address")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("code", "plate", "depot", "capacity", "max_shift_minutes", "is_active")
    list_filter = ("depot", "is_active")
    search_fields = ("code", "plate")


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "depot", "default_vehicle", "is_available")
    list_filter = ("depot", "is_available")
    autocomplete_fields = ("user",)
