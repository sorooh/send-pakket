"""
Shipping API Serializers - Send-Pakket Platform
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Shipment, TrackingEvent, ShipmentItem, ShipmentDocument, ShipmentRate


class ShipmentItemSerializer(serializers.ModelSerializer):
    """Shipment item serializer"""

    class Meta:
        model = ShipmentItem
        fields = [
            'id', 'sku', 'name', 'description', 'quantity',
            'unit_price', 'total_price', 'weight', 'country_of_origin',
            'hs_code', 'metadata'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        # Calculate total_price if not provided
        if 'total_price' not in validated_data:
            quantity = validated_data.get('quantity', 1)
            unit_price = validated_data.get('unit_price', 0)
            validated_data['total_price'] = quantity * unit_price
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Recalculate total_price if quantity or unit_price changed
        if 'quantity' in validated_data or 'unit_price' in validated_data:
            quantity = validated_data.get('quantity', instance.quantity)
            unit_price = validated_data.get('unit_price', instance.unit_price)
            validated_data['total_price'] = quantity * unit_price
        return super().update(instance, validated_data)


class TrackingEventSerializer(serializers.ModelSerializer):
    """Tracking event serializer"""

    class Meta:
        model = TrackingEvent
        fields = [
            'id', 'event_code', 'event_description', 'location',
            'event_timestamp', 'carrier_event_id', 'carrier_raw_data'
        ]
        read_only_fields = ['id']


class ShipmentDocumentSerializer(serializers.ModelSerializer):
    """Shipment document serializer"""

    class Meta:
        model = ShipmentDocument
        fields = [
            'id', 'document_type', 'name', 'file', 'file_url',
            'file_size', 'mime_type', 'generated_by_carrier',
            'carrier_document_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ShipmentSerializer(serializers.ModelSerializer):
    """Shipment serializer"""

    items = ShipmentItemSerializer(many=True, read_only=True)
    tracking_events = TrackingEventSerializer(many=True, read_only=True)
    documents = ShipmentDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'shipment_number', 'reference', 'order_number',
            'carrier', 'service', 'tracking_number', 'carrier_shipment_id',
            'sender_address', 'recipient_address', 'return_address',
            'weight', 'length', 'width', 'height',
            'description', 'contents', 'declared_value', 'currency',
            'customs_info', 'is_documents_only',
            'delivery_type', 'requires_signature', 'is_fragile',
            'insurance_required', 'insurance_amount',
            'delivery_instructions', 'pickup_location',
            'status', 'status_updated_at',
            'cost_price', 'selling_price', 'markup',
            'label_url', 'label_pdf', 'commercial_invoice_url',
            'shipped_at', 'estimated_delivery', 'delivered_at',
            'created_at', 'updated_at',
            'items', 'tracking_events', 'documents'
        ]
        read_only_fields = [
            'id', 'shipment_number', 'tracking_number', 'carrier_shipment_id',
            'status', 'status_updated_at', 'label_url', 'label_pdf',
            'commercial_invoice_url', 'shipped_at', 'delivered_at',
            'created_at', 'updated_at'
        ]


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """Shipment creation serializer"""

    items = ShipmentItemSerializer(many=True, required=False)

    class Meta:
        model = Shipment
        fields = [
            'reference', 'order_number', 'carrier', 'service',
            'sender_address', 'recipient_address', 'return_address',
            'weight', 'length', 'width', 'height',
            'description', 'contents', 'declared_value', 'currency',
            'customs_info', 'is_documents_only',
            'delivery_type', 'requires_signature', 'is_fragile',
            'insurance_required', 'insurance_amount',
            'delivery_instructions', 'pickup_location',
            'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        shipment = Shipment.objects.create(**validated_data)

        # Create shipment items
        for item_data in items_data:
            ShipmentItem.objects.create(shipment=shipment, **item_data)

        return shipment


class ShipmentRateSerializer(serializers.ModelSerializer):
    """Shipment rate serializer"""

    carrier_name = serializers.CharField(source='carrier.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = ShipmentRate
        fields = [
            'id', 'quote_id', 'carrier', 'carrier_name', 'service', 'service_name',
            'origin', 'destination', 'weight', 'dimensions',
            'cost_price', 'selling_price', 'currency',
            'estimated_delivery_days', 'service_features',
            'expires_at', 'is_used', 'created_at'
        ]
        read_only_fields = ['id', 'quote_id', 'is_used', 'created_at']


class ShipmentRateCreateSerializer(serializers.Serializer):
    """Serializer for requesting shipment rates"""

    origin = serializers.JSONField()
    destination = serializers.JSONField()
    weight = serializers.DecimalField(max_digits=8, decimal_places=3)
    dimensions = serializers.JSONField(required=False)
    contents = serializers.JSONField(required=False)
    delivery_type = serializers.ChoiceField(
        choices=['standard', 'express', 'overnight', 'economy', 'pickup_point'],
        default='standard'
    )
    special_services = serializers.JSONField(required=False)

    def validate_origin(self, value):
        """Validate origin address format"""
        required_fields = ['country', 'postal_code', 'city']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Origin address must include '{field}'")
        return value

    def validate_destination(self, value):
        """Validate destination address format"""
        required_fields = ['country', 'postal_code', 'city']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Destination address must include '{field}'")
        return value


class TrackingUpdateSerializer(serializers.Serializer):
    """Serializer for updating tracking information"""

    tracking_number = serializers.CharField(max_length=100)
    carrier_events = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    def validate_carrier_events(self, value):
        """Validate carrier events format"""
        for event in value:
            required_fields = ['event_code', 'event_description', 'event_timestamp']
            for field in required_fields:
                if field not in event:
                    raise serializers.ValidationError(f"Each carrier event must include '{field}'")
        return value