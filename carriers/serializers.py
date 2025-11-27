"""
Carrier serializers for Send-Pakket Platform
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Carrier, CarrierService, CarrierCredentials, CarrierPricing, CarrierWebhook


class CarrierServiceSerializer(serializers.ModelSerializer):
    """Serializer for carrier services"""

    class Meta:
        model = CarrierService
        fields = [
            'id', 'carrier', 'name', 'code', 'display_name', 'description',
            'service_type', 'delivery_days_min', 'delivery_days_max', 'cutoff_time',
            'domestic_only', 'international_only', 'countries_available', 'countries_excluded',
            'max_weight_kg', 'max_length_cm', 'max_width_cm', 'max_height_cm', 'max_girth_cm',
            'requires_signature', 'includes_tracking', 'includes_insurance', 'supports_cod',
            'supports_pickup_points', 'pricing_type', 'is_active', 'is_featured',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CarrierSerializer(serializers.ModelSerializer):
    """Serializer for carriers with nested services"""

    services = CarrierServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Carrier
        fields = [
            'id', 'name', 'code', 'display_name', 'website', 'logo', 'description',
            'countries_served', 'international_shipping', 'api_endpoint', 'api_version',
            'supports_tracking', 'supports_labels', 'supports_pickup', 'supports_webhooks',
            'integration_type', 'is_active', 'is_featured', 'priority',
            'requires_account', 'requires_api_key', 'account_signup_url',
            'documentation_url', 'setup_instructions', 'services',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CarrierCredentialsSerializer(serializers.ModelSerializer):
    """Serializer for carrier credentials"""

    carrier_name = serializers.CharField(source='carrier.display_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = CarrierCredentials
        fields = [
            'id', 'company', 'carrier', 'carrier_name', 'company_name',
            'api_key', 'api_secret', 'username', 'password', 'customer_number',
            'sandbox_mode', 'additional_config', 'is_active', 'is_verified',
            'last_verified_at', 'verification_error', 'last_used_at',
            'total_shipments', 'total_cost', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'carrier_name', 'company_name', 'last_verified_at',
                          'last_used_at', 'total_shipments', 'total_cost',
                          'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True},
            'username': {'write_only': True},
            'password': {'write_only': True},
        }


class CarrierPricingSerializer(serializers.ModelSerializer):
    """Serializer for carrier pricing rules"""

    carrier_name = serializers.CharField(source='carrier_service.carrier.display_name', read_only=True)
    service_name = serializers.CharField(source='carrier_service.display_name', read_only=True)

    class Meta:
        model = CarrierPricing
        fields = [
            'id', 'carrier_service', 'carrier_name', 'service_name',
            'origin_country', 'destination_country', 'origin_postal_codes',
            'destination_postal_codes', 'weight_from_kg', 'weight_to_kg',
            'base_price', 'price_per_kg', 'currency', 'fuel_surcharge_percent',
            'remote_area_surcharge', 'oversized_surcharge', 'effective_from',
            'effective_to', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'carrier_name', 'service_name', 'created_at', 'updated_at']


class CarrierWebhookSerializer(serializers.ModelSerializer):
    """Serializer for carrier webhooks"""

    carrier_name = serializers.CharField(source='carrier.display_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = CarrierWebhook
        fields = [
            'id', 'carrier', 'company', 'carrier_name', 'company_name',
            'webhook_url', 'secret_key', 'event_types', 'is_active',
            'last_triggered_at', 'total_calls', 'failed_calls',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'carrier_name', 'company_name', 'last_triggered_at',
                          'total_calls', 'failed_calls', 'created_at', 'updated_at']
        extra_kwargs = {
            'secret_key': {'write_only': True},
        }


class CarrierListSerializer(serializers.ModelSerializer):
    """Simplified serializer for carrier listing"""

    services_count = serializers.SerializerMethodField()
    active_services_count = serializers.SerializerMethodField()

    class Meta:
        model = Carrier
        fields = [
            'id', 'name', 'code', 'display_name', 'countries_served',
            'international_shipping', 'supports_tracking', 'supports_labels',
            'integration_type', 'is_active', 'is_featured', 'priority',
            'services_count', 'active_services_count', 'created_at'
        ]

    def get_services_count(self, obj):
        return obj.services.count()

    def get_active_services_count(self, obj):
        return obj.services.filter(is_active=True).count()


class CarrierServiceListSerializer(serializers.ModelSerializer):
    """Simplified serializer for service listing"""

    carrier_name = serializers.CharField(source='carrier.display_name', read_only=True)
    carrier_code = serializers.CharField(source='carrier.code', read_only=True)

    class Meta:
        model = CarrierService
        fields = [
            'id', 'carrier', 'carrier_name', 'carrier_code', 'name', 'code',
            'display_name', 'service_type', 'delivery_days_min', 'delivery_days_max',
            'domestic_only', 'international_only', 'max_weight_kg',
            'requires_signature', 'includes_tracking', 'includes_insurance',
            'pricing_type', 'is_active', 'is_featured'
        ]