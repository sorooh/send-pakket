"""
Central Core of Send-Pakket Platform
The central core that manages all basic operations of the platform
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json


class PlatformCore(models.Model):
    """
    Platform Core - Basic system settings
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic platform information
    platform_name = models.CharField(max_length=255, default="Send-Pakket")
    platform_version = models.CharField(max_length=50, default="1.0.0")
    platform_domain = models.CharField(max_length=255, default="sendpakket.com")

    # System settings
    is_maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)

    # Security settings
    max_login_attempts = models.IntegerField(default=5)
    session_timeout_minutes = models.IntegerField(default=60)
    password_min_length = models.IntegerField(default=8)

    # Performance settings
    max_concurrent_requests = models.IntegerField(default=1000)
    rate_limit_per_minute = models.IntegerField(default=100)
    cache_timeout_seconds = models.IntegerField(default=3600)

    # Integration settings
    supported_currencies = models.JSONField(default=list, help_text="Supported currencies")
    supported_languages = models.JSONField(default=list, help_text="Supported languages")
    supported_countries = models.JSONField(default=list, help_text="Supported countries")

    # Notification settings
    email_notifications_enabled = models.BooleanField(default=True)
    sms_notifications_enabled = models.BooleanField(default=False)
    push_notifications_enabled = models.BooleanField(default=True)

    # Backup settings
    backup_frequency_hours = models.IntegerField(default=24)
    backup_retention_days = models.IntegerField(default=30)

    # System statistics
    total_merchants = models.IntegerField(default=0)
    total_shipments = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # System status
    system_status = models.CharField(max_length=20, choices=[
        ('operational', 'Operational'),
        ('degraded', 'Degraded'),
        ('maintenance', 'Maintenance'),
        ('down', 'Down'),
    ], default='operational')

    # Advanced settings
    features_enabled = models.JSONField(default=dict, help_text="Enabled features")
    custom_settings = models.JSONField(default=dict, help_text="Custom settings")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'platform_core'
        verbose_name = 'Platform Core'
        verbose_name_plural = 'Platform Core'

    def __str__(self):
        return f"{self.platform_name} v{self.platform_version}"

    def save(self, *args, **kwargs):
        if not self.supported_currencies:
            self.supported_currencies = ['EUR', 'USD', 'GBP']
        if not self.supported_languages:
            self.supported_languages = ['en', 'nl', 'de', 'fr']
        if not self.supported_countries:
            self.supported_countries = ['NL', 'DE', 'BE', 'FR', 'GB']
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Get platform core instance (Singleton)"""
        instance, created = cls.objects.get_or_create(
            defaults={'platform_name': 'Send-Pakket'}
        )
        return instance


class MerchantCore(models.Model):
    """
    Merchant Core - Each merchant has an independent core linked to the central core
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to central core
    platform_core = models.ForeignKey(PlatformCore, on_delete=models.CASCADE)

    # Basic merchant information
    merchant_id = models.CharField(max_length=50, unique=True, help_text="Unique merchant identifier")
    name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=100, choices=[
        ('ecommerce', 'E-commerce'),
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('dropshipping', 'Dropshipping'),
        ('marketplace', 'Marketplace'),
    ])

    # Merchant status
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Merchant settings
    settings = models.JSONField(default=dict, help_text="Merchant custom settings")
    preferences = models.JSONField(default=dict, help_text="Merchant preferences")

    # Usage limits
    monthly_shipment_limit = models.IntegerField(default=1000)
    api_rate_limit = models.IntegerField(default=100)
    storage_limit_mb = models.IntegerField(default=1000)

    # Merchant statistics
    total_shipments = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    active_shipments = models.IntegerField(default=0)

    # Merchant integrations
    integrations = models.JSONField(default=dict, help_text="Enabled integrations")

    # Security settings
    security_settings = models.JSONField(default=dict, help_text="Security settings")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'merchant_cores'
        verbose_name = 'Merchant Core'
        verbose_name_plural = 'Merchant Cores'
        indexes = [
            models.Index(fields=['merchant_id']),
            models.Index(fields=['status']),
            models.Index(fields=['business_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.merchant_id})"

    def activate(self):
        """Activate merchant"""
        self.status = 'active'
        self.activated_at = timezone.now()
        self.save()

    def suspend(self):
        """Suspend merchant"""
        self.status = 'suspended'
        self.suspended_at = timezone.now()
        self.save()

    def terminate(self):
        """Terminate merchant"""
        self.status = 'terminated'
        self.save()

    def is_active(self):
        """Check merchant status"""
        return self.status == 'active'

    def can_create_shipment(self):
        """Check if can create new shipment"""
        if not self.is_active():
            return False
        return self.active_shipments < self.monthly_shipment_limit


class CoreService(models.Model):
    """
    Core Services - Basic services provided by the platform
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Service information
    service_name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField()

    # Service type
    SERVICE_TYPES = [
        ('shipping', 'Shipping'),
        ('payment', 'Payment'),
        ('analytics', 'Analytics'),
        ('notification', 'Notification'),
        ('storage', 'Storage'),
        ('integration', 'Integration'),
    ]
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)

    # Service status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('disabled', 'Disabled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Service configuration
    configuration = models.JSONField(default=dict)
    version = models.CharField(max_length=20, default='1.0.0')

    # Service limits
    max_requests_per_minute = models.IntegerField(default=1000)
    max_requests_per_hour = models.IntegerField(default=10000)

    # Usage statistics
    total_requests = models.BigIntegerField(default=0)
    active_users = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_services'
        verbose_name = 'Core Service'
        verbose_name_plural = 'Core Services'

    def __str__(self):
        return f"{self.display_name} ({self.service_type})"

    def is_available(self):
        """Check if service is available"""
        return self.status == 'active'


class MerchantService(models.Model):
    """
    Merchant Services - Services enabled for each merchant
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to merchant and service
    merchant_core = models.ForeignKey(MerchantCore, on_delete=models.CASCADE)
    core_service = models.ForeignKey(CoreService, on_delete=models.CASCADE)

    # Merchant settings for service
    is_enabled = models.BooleanField(default=True)
    merchant_config = models.JSONField(default=dict, help_text="Merchant settings for this service")

    # Custom limits for merchant
    custom_limits = models.JSONField(default=dict, help_text="Custom limits for merchant")

    # Usage statistics
    usage_count = models.BigIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'merchant_services'
        verbose_name = 'Merchant Service'
        verbose_name_plural = 'Merchant Services'
        unique_together = ['merchant_core', 'core_service']

    def __str__(self):
        return f"{self.merchant_core.name} - {self.core_service.display_name}"

    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save()


class CoreConfiguration(models.Model):
    """
    Core Configurations - Customizable settings
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Configuration scope
    CONFIG_SCOPES = [
        ('global', 'Global'),
        ('merchant', 'Merchant'),
        ('service', 'Service'),
        ('regional', 'Regional'),
    ]
    scope = models.CharField(max_length=20, choices=CONFIG_SCOPES, default='global')

    # Configuration information
    config_key = models.CharField(max_length=100)
    config_value = models.JSONField()
    description = models.TextField(blank=True)

    # Permissions
    is_editable = models.BooleanField(default=True)
    requires_restart = models.BooleanField(default=False)

    # Link to merchant or service
    merchant_core = models.ForeignKey(
        MerchantCore,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    core_service = models.ForeignKey(
        CoreService,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_configurations'
        verbose_name = 'Core Configuration'
        verbose_name_plural = 'Core Configurations'
        unique_together = ['scope', 'config_key', 'merchant_core', 'core_service']

    def __str__(self):
        scope_info = f" ({self.merchant_core.name})" if self.merchant_core else ""
        return f"{self.config_key}{scope_info}"


class CoreEvent(models.Model):
    """
    Core Events - Logging all important events
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Event type
    EVENT_TYPES = [
        ('system', 'System Event'),
        ('merchant', 'Merchant Event'),
        ('service', 'Service Event'),
        ('security', 'Security Event'),
        ('performance', 'Performance Event'),
    ]
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)

    # Event level
    EVENT_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    level = models.CharField(max_length=20, choices=EVENT_LEVELS, default='info')

    # Event details
    title = models.CharField(max_length=255)
    description = models.TextField()
    metadata = models.JSONField(default=dict)

    # Link to components
    merchant_core = models.ForeignKey(
        MerchantCore,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    core_service = models.ForeignKey(
        CoreService,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Additional information
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_events'
        verbose_name = 'Core Event'
        verbose_name_plural = 'Core Events'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['level', 'created_at']),
            models.Index(fields=['merchant_core', 'created_at']),
        ]

    def __str__(self):
        return f"{self.level.upper()}: {self.title}"


class CoreMetric(models.Model):
    """
    Core Metrics - System performance monitoring
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Metric type
    METRIC_TYPES = [
        ('performance', 'Performance'),
        ('usage', 'Usage'),
        ('error', 'Error'),
        ('business', 'Business'),
    ]
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)

    # Metric name
    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=15, decimal_places=4)

    # Unit
    unit = models.CharField(max_length=20, default='count')

    # Link to components
    merchant_core = models.ForeignKey(
        MerchantCore,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    core_service = models.ForeignKey(
        CoreService,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Additional data
    tags = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)

    # Timestamp
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_metrics'
        verbose_name = 'Core Metric'
        verbose_name_plural = 'Core Metrics'
        indexes = [
            models.Index(fields=['metric_type', 'recorded_at']),
            models.Index(fields=['metric_name', 'recorded_at']),
            models.Index(fields=['merchant_core', 'recorded_at']),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.unit}"
