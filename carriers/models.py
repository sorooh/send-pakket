"""
Carrier models for Send-Pakket Platform
"""

from django.db import models
from decimal import Decimal
import uuid


class Carrier(models.Model):
    """Shipping carrier model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic information
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)  # e.g., 'postnl', 'dhl', 'ups'
    display_name = models.CharField(max_length=255)
    
    # Carrier details
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='carrier_logos/', blank=True)
    description = models.TextField(blank=True)
    
    # Coverage
    countries_served = models.JSONField(default=list)  # List of ISO country codes
    international_shipping = models.BooleanField(default=False)
    
    # API Integration
    api_endpoint = models.URLField(blank=True)
    api_version = models.CharField(max_length=20, blank=True)
    supports_tracking = models.BooleanField(default=True)
    supports_labels = models.BooleanField(default=True)
    supports_pickup = models.BooleanField(default=False)
    supports_webhooks = models.BooleanField(default=False)
    
    # Features
    INTEGRATION_TYPES = (
        ('api', 'API Integration'),
        ('file_upload', 'File Upload'),
        ('manual', 'Manual'),
    )
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPES, default='api')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    priority = models.IntegerField(default=100)  # Lower number = higher priority
    
    # Requirements
    requires_account = models.BooleanField(default=True)
    requires_api_key = models.BooleanField(default=True)
    account_signup_url = models.URLField(blank=True)
    
    # Documentation
    documentation_url = models.URLField(blank=True)
    setup_instructions = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carriers'
        verbose_name = 'Carrier'
        verbose_name_plural = 'Carriers'
        ordering = ['priority', 'name']

    def __str__(self):
        return self.display_name


class CarrierService(models.Model):
    """Services offered by carriers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE, related_name='services')
    
    # Service details
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)  # Carrier's service code
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Service type
    SERVICE_TYPES = (
        ('standard', 'Standard'),
        ('express', 'Express'),
        ('overnight', 'Overnight'),
        ('economy', 'Economy'),
        ('premium', 'Premium'),
    )
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, default='standard')
    
    # Delivery timing
    delivery_days_min = models.IntegerField(null=True, blank=True)
    delivery_days_max = models.IntegerField(null=True, blank=True)
    cutoff_time = models.TimeField(null=True, blank=True)  # Daily cutoff for next-day service
    
    # Geographic coverage
    domestic_only = models.BooleanField(default=False)
    international_only = models.BooleanField(default=False)
    countries_available = models.JSONField(default=list)  # ISO country codes
    countries_excluded = models.JSONField(default=list)
    
    # Size and weight limits
    max_weight_kg = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    max_length_cm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    max_width_cm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    max_height_cm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    max_girth_cm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Features
    requires_signature = models.BooleanField(default=False)
    includes_tracking = models.BooleanField(default=True)
    includes_insurance = models.BooleanField(default=False)
    supports_cod = models.BooleanField(default=False)  # Cash on Delivery
    supports_pickup_points = models.BooleanField(default=False)
    
    # Pricing structure
    PRICING_TYPES = (
        ('flat_rate', 'Flat Rate'),
        ('weight_based', 'Weight Based'),
        ('zone_based', 'Zone Based'),
        ('dimensional', 'Dimensional Weight'),
    )
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPES, default='weight_based')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carrier_services'
        verbose_name = 'Carrier Service'
        verbose_name_plural = 'Carrier Services'
        unique_together = ['carrier', 'code']

    def __str__(self):
        return f"{self.carrier.name} - {self.display_name}"


class CarrierCredentials(models.Model):
    """Carrier API credentials for companies"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='carrier_credentials')
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE)
    
    # Credentials
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    customer_number = models.CharField(max_length=100, blank=True)
    
    # Additional configuration
    sandbox_mode = models.BooleanField(default=True)
    additional_config = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    verification_error = models.TextField(blank=True)
    
    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    total_shipments = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carrier_credentials'
        verbose_name = 'Carrier Credentials'
        verbose_name_plural = 'Carrier Credentials'
        unique_together = ['company', 'carrier']

    def __str__(self):
        return f"{self.company.name} - {self.carrier.name}"


class CarrierPricing(models.Model):
    """Pricing rules for carrier services"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carrier_service = models.ForeignKey(CarrierService, on_delete=models.CASCADE, related_name='pricing_rules')
    
    # Geographic scope
    origin_country = models.CharField(max_length=2, blank=True)  # ISO code
    destination_country = models.CharField(max_length=2, blank=True)  # ISO code
    origin_postal_codes = models.JSONField(default=list, blank=True)
    destination_postal_codes = models.JSONField(default=list, blank=True)
    
    # Weight ranges
    weight_from_kg = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    weight_to_kg = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Surcharges
    fuel_surcharge_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    remote_area_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    oversized_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Validity
    effective_from = models.DateTimeField()
    effective_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carrier_pricing'
        verbose_name = 'Carrier Pricing'
        verbose_name_plural = 'Carrier Pricing'
        indexes = [
            models.Index(fields=['carrier_service', 'origin_country', 'destination_country']),
            models.Index(fields=['effective_from', 'effective_to']),
        ]

    def __str__(self):
        return f"{self.carrier_service} - {self.origin_country} to {self.destination_country}"


class CarrierWebhook(models.Model):
    """Webhook configurations for carriers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE, related_name='webhooks')
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='carrier_webhooks')
    
    # Webhook details
    webhook_url = models.URLField()
    secret_key = models.CharField(max_length=255, blank=True)
    
    # Events to listen for
    EVENT_TYPES = (
        ('shipment_created', 'Shipment Created'),
        ('shipment_picked_up', 'Shipment Picked Up'),
        ('shipment_in_transit', 'Shipment In Transit'),
        ('shipment_delivered', 'Shipment Delivered'),
        ('shipment_failed', 'Delivery Failed'),
        ('shipment_returned', 'Shipment Returned'),
        ('all', 'All Events'),
    )
    event_types = models.JSONField(default=list)  # List of event types to listen for
    
    # Status
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    total_calls = models.IntegerField(default=0)
    failed_calls = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carrier_webhooks'
        verbose_name = 'Carrier Webhook'
        verbose_name_plural = 'Carrier Webhooks'

    def __str__(self):
        return f"{self.carrier.name} webhook for {self.company.name}"


class CarrierAPILog(models.Model):
    """Log of API calls to carriers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, null=True, blank=True)
    
    # Request details
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)  # GET, POST, PUT, DELETE
    request_data = models.JSONField(null=True, blank=True)
    
    # Response details
    status_code = models.IntegerField()
    response_data = models.JSONField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    
    # Related objects
    shipment = models.ForeignKey('shipping.Shipment', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'carrier_api_logs'
        verbose_name = 'Carrier API Log'
        verbose_name_plural = 'Carrier API Logs'
        indexes = [
            models.Index(fields=['carrier', 'created_at']),
            models.Index(fields=['company', 'created_at']),
            models.Index(fields=['status_code', 'created_at']),
        ]

    def __str__(self):
        return f"{self.carrier.name} {self.method} {self.endpoint} - {self.status_code}"
