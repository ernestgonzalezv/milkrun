from rest_framework import serializers

from .models import Depot, DriverProfile, Vehicle


class DepotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depot
        fields = ("id", "name", "address", "latitude", "longitude", "is_active")


class VehicleSerializer(serializers.ModelSerializer):
    depot_name = serializers.CharField(source="depot.name", read_only=True)

    class Meta:
        model = Vehicle
        fields = (
            "id", "depot", "depot_name", "code", "plate", "capacity",
            "max_shift_minutes", "avg_speed_kmh", "is_active",
        )


class DriverProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = DriverProfile
        fields = (
            "id", "user", "username", "full_name", "depot",
            "default_vehicle", "license_number", "is_available",
        )
