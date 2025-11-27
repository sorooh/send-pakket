"""
Serializers for the central core
"""

from rest_framework import serializers
from django.utils import timezone
from .models import (
    PlatformCore, MerchantCore, CoreService,
    MerchantService, CoreConfiguration, CoreEvent, CoreMetric
)


class PlatformCoreSerializer(serializers.ModelSerializer):
    """
    Serializer for the platform central core
    """

    class Meta:
        model = PlatformCore
        fields = [
            'id', 'platform_name', 'platform_version', 'platform_domain',
            'is_maintenance_mode', 'maintenance_message',
            'max_login_attempts', 'session_timeout_minutes', 'password_min_length',
            'max_concurrent_requests', 'rate_limit_per_minute', 'cache_timeout_seconds',
            'supported_currencies', 'supported_languages', 'supported_countries',
            'email_notifications_enabled', 'sms_notifications_enabled', 'push_notifications_enabled',
            'backup_frequency_hours', 'backup_retention_days',
            'total_merchants', 'total_shipments', 'total_revenue',
            'system_status', 'features_enabled', 'custom_settings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_merchants', 'total_shipments', 'total_revenue']

    def validate_platform_version(self, value):
        """Validate version number"""
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', value):
            raise serializers.ValidationError("Platform version must be in format x.y.z")
        return value

    def validate_supported_currencies(self, value):
        """Validate supported currencies"""
        valid_currencies = ['EUR', 'USD', 'GBP', 'CAD', 'AUD', 'CHF', 'SEK', 'NOK', 'DKK', 'PLN']
        if not all(currency in valid_currencies for currency in value):
            raise serializers.ValidationError(f"Unsupported currencies. Valid options: {valid_currencies}")
        return value

    def validate_supported_languages(self, value):
        """Validate supported languages"""
        valid_languages = ['en', 'nl', 'de', 'fr', 'es', 'it', 'pt', 'ar', 'zh', 'ja']
        if not all(lang in valid_languages for lang in value):
            raise serializers.ValidationError(f"Unsupported languages. Valid options: {valid_languages}")
        return value


class MerchantCoreSerializer(serializers.ModelSerializer):
    """
    Serializer for merchant core
    """

    platform_core_name = serializers.CharField(source='platform_core.platform_name', read_only=True)
    is_active_status = serializers.SerializerMethodField()
    can_create_shipment = serializers.SerializerMethodField()

    class Meta:
        model = MerchantCore
        fields = [
            'id', 'platform_core', 'platform_core_name',
            'merchant_id', 'name', 'business_type', 'status',
            'settings', 'preferences',
            'monthly_shipment_limit', 'api_rate_limit', 'storage_limit_mb',
            'total_shipments', 'total_revenue', 'active_shipments',
            'integrations', 'security_settings',
            'is_active_status', 'can_create_shipment',
            'created_at', 'updated_at', 'activated_at', 'suspended_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'activated_at', 'suspended_at']

    def get_is_active_status(self, obj):
        return obj.is_active()

    def get_can_create_shipment(self, obj):
        return obj.can_create_shipment()

    def validate_merchant_id(self, value):
        """Validate merchant ID"""
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', value):
            raise serializers.ValidationError("Merchant ID can only contain letters, numbers, hyphens, and underscores")
        if len(value) < 3 or len(value) > 50:
            raise serializers.ValidationError("Merchant ID must be between 3 and 50 characters")
        return value

    def validate_monthly_shipment_limit(self, value):
        """Validate monthly shipment limit"""
        if value < 1 or value > 100000:
            raise serializers.ValidationError("Monthly shipment limit must be between 1 and 100,000")
        return value


class CoreServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for central core services
    """

    is_available = serializers.SerializerMethodField()

    class Meta:
        model = CoreService
        fields = [
            'id', 'service_name', 'display_name', 'description',
            'service_type', 'status', 'configuration', 'version',
            'max_requests_per_minute', 'max_requests_per_hour',
            'total_requests', 'active_users', 'is_available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_requests', 'active_users']

    def get_is_available(self, obj):
        return obj.is_available()


class MerchantServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for merchant services
    """

    service_name = serializers.CharField(source='core_service.service_name', read_only=True)
    service_display_name = serializers.CharField(source='core_service.display_name', read_only=True)
    service_type = serializers.CharField(source='core_service.service_type', read_only=True)
    merchant_name = serializers.CharField(source='merchant_core.name', read_only=True)

    class Meta:
        model = MerchantService
        fields = [
            'id', 'merchant_core', 'merchant_name', 'core_service',
            'service_name', 'service_display_name', 'service_type',
            'is_enabled', 'merchant_config', 'custom_limits',
            'usage_count', 'last_used_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'usage_count', 'last_used_at']


class CoreConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for core configurations
    """

    merchant_name = serializers.CharField(source='merchant_core.name', read_only=True)
    service_name = serializers.CharField(source='core_service.service_name', read_only=True)

    class Meta:
        model = CoreConfiguration
        fields = [
            'id', 'scope', 'config_key', 'config_value', 'description',
            'is_editable', 'requires_restart',
            'merchant_core', 'merchant_name', 'core_service', 'service_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_config_key(self, value):
        """Validate configuration key"""
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError("Config key must start with letter or underscore and contain only alphanumeric characters and underscores")
        return value


class CoreEventSerializer(serializers.ModelSerializer):
    """
    Serializer for core events
    """

    merchant_name = serializers.CharField(source='merchant_core.name', read_only=True)
    service_name = serializers.CharField(source='core_service.service_name', read_only=True)

    class Meta:
        model = CoreEvent
        fields = [
            'id', 'event_type', 'level', 'title', 'description', 'metadata',
            'merchant_core', 'merchant_name', 'core_service', 'service_name',
            'source_ip', 'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CoreMetricSerializer(serializers.ModelSerializer):
    """
    Serializer for core metrics
    """

    merchant_name = serializers.CharField(source='merchant_core.name', read_only=True)
    service_name = serializers.CharField(source='core_service.service_name', read_only=True)

    class Meta:
        model = CoreMetric
        fields = [
            'id', 'metric_type', 'metric_name', 'metric_value', 'unit',
            'merchant_core', 'merchant_name', 'core_service', 'service_name',
            'tags', 'metadata', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']


# Serializers for special operations

class MerchantCoreCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new merchant core
    """

    class Meta:
        model = MerchantCore
        fields = [
            'merchant_id', 'name', 'business_type',
            'settings', 'preferences',
            'monthly_shipment_limit', 'api_rate_limit', 'storage_limit_mb'
        ]

    def create(self, validated_data):
        from .services import MerchantCoreService
        return MerchantCoreService.create_merchant_core(validated_data)


class MerchantCoreUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating merchant core
    """

    class Meta:
        model = MerchantCore
        fields = [
            'name', 'business_type', 'status',
            'settings', 'preferences',
            'monthly_shipment_limit', 'api_rate_limit', 'storage_limit_mb',
            'integrations', 'security_settings'
        ]


class CoreConfigurationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating configurations
    """

    class Meta:
        model = CoreConfiguration
        fields = ['config_value', 'description', 'is_editable', 'requires_restart']


class PlatformStatsSerializer(serializers.Serializer):
    """
    Serializer for platform statistics
    """

    total_merchants = serializers.IntegerField()
    total_shipments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    active_merchants = serializers.IntegerField()
    system_status = serializers.CharField()
    uptime_percentage = serializers.FloatField()


class MerchantLimitsSerializer(serializers.Serializer):
    """
    Serializer for merchant limits
    """

    can_create_shipment = serializers.BooleanField()
    within_shipment_limit = serializers.BooleanField()
    is_active = serializers.BooleanField()
    current_shipments = serializers.IntegerField()
    max_shipments = serializers.IntegerField()
    api_rate_limit = serializers.IntegerField()
    storage_limit_mb = serializers.IntegerField()