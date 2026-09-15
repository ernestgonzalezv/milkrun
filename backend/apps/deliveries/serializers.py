"""Serializers de entrega.

Trabajan sobre entidades del dominio, no sobre modelos: por eso son
`Serializer` y no `ModelSerializer`. El precio es declarar los campos a mano;
la ganancia es que la forma de la API deja de estar atada a la del esquema.
"""

from __future__ import annotations

from rest_framework import serializers

from domain.entities import DeliveryEvent, LocationPing, Stop
from domain.values import Coordinates, EventKind, FailureReason, StopStatus

MAX_BATCH = 200  # a whole day of offline queue fits with room to spare

# These duplicate the model's choice labels on purpose: the public tracking
# view reads domain values, which know nothing about Django, so it cannot call
# get_status_display(). Keeping the map here means the customer-facing wording
# can change without touching the model.
STATUS_LABELS = {
    StopStatus.PENDING: "Pending",
    StopStatus.PLANNED: "Planned",
    StopStatus.IN_TRANSIT: "In transit",
    StopStatus.DELIVERED: "Delivered",
    StopStatus.FAILED: "Failed",
    StopStatus.CANCELLED: "Cancelled",
}

EVENT_LABELS = {
    EventKind.DEPARTED: "Departed for the stop",
    EventKind.ARRIVED: "Arrived at the stop",
    EventKind.DELIVERED: "Delivered",
    EventKind.FAILED: "Delivery failed",
    EventKind.NOTE: "Note",
}


class StopSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    tracking_code = serializers.CharField(read_only=True)
    depot = serializers.IntegerField(source="depot_id")
    customer_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    address = serializers.CharField(max_length=255)
    latitude = serializers.FloatField(source="coordinates.latitude")
    longitude = serializers.FloatField(source="coordinates.longitude")
    demand = serializers.FloatField(required=False, default=1.0, min_value=0)
    service_minutes = serializers.IntegerField(required=False, default=5, min_value=0)
    scheduled_date = serializers.DateField(required=False)
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    created_at = serializers.DateTimeField(read_only=True)

    def get_status_display(self, stop: Stop) -> str:
        return STATUS_LABELS[stop.status]

    def to_entity(self, *, stop_id: int | None = None, today=None) -> Stop:
        data = self.validated_data
        coordinates = data["coordinates"]
        return Stop(
            id=stop_id,
            tracking_code="",
            depot_id=data["depot_id"],
            customer_name=data["customer_name"],
            address=data["address"],
            coordinates=Coordinates(coordinates["latitude"], coordinates["longitude"]),
            scheduled_date=data.get("scheduled_date") or today,
            demand=data.get("demand", 1.0),
            service_minutes=data.get("service_minutes", 5),
            phone=data.get("phone", ""),
            notes=data.get("notes", ""),
        )


class DeliveryEventSerializer(serializers.Serializer):
    stop = serializers.IntegerField(source="stop_id")
    client_event_id = serializers.UUIDField()
    kind = serializers.ChoiceField(choices=[k.value for k in EventKind])
    reason = serializers.ChoiceField(
        choices=[r.value for r in FailureReason], required=False, allow_blank=True, default=""
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")
    latitude = serializers.FloatField(required=False, allow_null=True, default=None)
    longitude = serializers.FloatField(required=False, allow_null=True, default=None)
    occurred_at = serializers.DateTimeField()

    def validate(self, attrs: dict) -> dict:
        if attrs.get("kind") == EventKind.FAILED and not attrs.get("reason"):
            raise serializers.ValidationError({"reason": "Una entrega fallida necesita motivo."})
        return attrs


class EventBatchSerializer(serializers.Serializer):
    """Tanda de hechos que la app movil tenia en cola.

    Se validan todos antes de escribir ninguno: si el chofer manda cuarenta y
    el numero doce viene corrupto, es mejor rechazar la tanda con un error
    claro que dejar once escritos y perder el resto en silencio.
    """

    events = DeliveryEventSerializer(many=True, allow_empty=False, max_length=MAX_BATCH)

    def to_entities(self, driver_id: int) -> list[DeliveryEvent]:
        return [
            DeliveryEvent(
                id=None,
                stop_id=item["stop_id"],
                driver_id=driver_id,
                client_event_id=item["client_event_id"],
                kind=EventKind(item["kind"]),
                occurred_at=item["occurred_at"],
                reason=FailureReason(item["reason"]) if item.get("reason") else None,
                note=item.get("note", ""),
                coordinates=_coordinates(item),
            )
            for item in self.validated_data["events"]
        ]


class LocationPingSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    accuracy_m = serializers.FloatField(required=False, allow_null=True, default=None)
    speed_kmh = serializers.FloatField(required=False, allow_null=True, default=None)
    recorded_at = serializers.DateTimeField()


class PingBatchSerializer(serializers.Serializer):
    pings = LocationPingSerializer(many=True, allow_empty=False, max_length=MAX_BATCH)

    def to_entities(self, driver_id: int) -> list[LocationPing]:
        return [
            LocationPing(
                driver_id=driver_id,
                coordinates=Coordinates(item["latitude"], item["longitude"]),
                recorded_at=item["recorded_at"],
                accuracy_m=item.get("accuracy_m"),
                speed_kmh=item.get("speed_kmh"),
            )
            for item in self.validated_data["pings"]
        ]


class PublicEventSerializer(serializers.Serializer):
    """Vista publica de un hecho: sin chofer, sin coordenadas, sin motivo."""

    kind = serializers.CharField()
    kind_display = serializers.SerializerMethodField()
    occurred_at = serializers.DateTimeField()

    def get_kind_display(self, event: DeliveryEvent) -> str:
        return EVENT_LABELS[event.kind]


class PublicTrackingSerializer(serializers.Serializer):
    """Lo que ve cualquiera con el codigo de seguimiento.

    Expone el minimo indispensable: sin telefono, sin direccion, sin notas y
    con los apellidos enmascarados. El codigo circula por WhatsApp.
    """

    tracking_code = serializers.CharField()
    customer_name = serializers.SerializerMethodField()
    status = serializers.CharField()
    status_display = serializers.SerializerMethodField()
    scheduled_date = serializers.DateField()
    timeline = serializers.SerializerMethodField()

    def get_customer_name(self, shipment) -> str:
        return shipment.stop.masked_customer_name()

    def get_status(self, shipment) -> str:
        return shipment.stop.status.value

    def get_status_display(self, shipment) -> str:
        return STATUS_LABELS[shipment.stop.status]

    def get_timeline(self, shipment) -> list[dict]:
        return PublicEventSerializer(shipment.timeline, many=True).data

    def to_representation(self, shipment) -> dict:
        return {
            "tracking_code": shipment.stop.tracking_code,
            "customer_name": self.get_customer_name(shipment),
            "status": shipment.stop.status.value,
            "status_display": self.get_status_display(shipment),
            "scheduled_date": shipment.stop.scheduled_date,
            "timeline": self.get_timeline(shipment),
        }


def _coordinates(item: dict) -> Coordinates | None:
    if item.get("latitude") is None or item.get("longitude") is None:
        return None
    return Coordinates(item["latitude"], item["longitude"])
