"""
Shipping models for Send-Pakket Platform
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid


class Shipment(models.Model):
    """Core shipment model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='shipments')
    
    # Shipment identification
    shipment_number = models.CharField(max_length=50, unique=True)
    reference = models.CharField(max_length=100, blank=True)  # Customer reference
    order_number = models.CharField(max_length=100, blank=True)  # E-commerce order number
    
    # Carrier information
    carrier = models.ForeignKey('carriers.Carrier', on_delete=models.PROTECT)
    service = models.ForeignKey('carriers.CarrierService', on_delete=models.PROTECT)
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier_shipment_id = models.CharField(max_length=100, blank=True)
    
    # Addresses
    sender_address = models.ForeignKey('core.Address', on_delete=models.PROTECT, related_name='sent_shipments')
    recipient_address = models.JSONField()  # Store recipient address as JSON
    return_address = models.ForeignKey('core.Address', on_delete=models.PROTECT, related_name='return_shipments', null=True, blank=True)
    
    # Package information
    weight = models.DecimalField(max_digits=8, decimal_places=3)  # in kg
    length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # in cm
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)   # in cm
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # in cm
    
    # Contents
    description = models.TextField()
    contents = models.JSONField(default=list)  # List of items
    declared_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Customs (for international shipments)
    customs_info = models.JSONField(null=True, blank=True)
    is_documents_only = models.BooleanField(default=False)
    
    # Delivery options
    DELIVERY_TYPES = (
        ('standard', 'Standard Delivery'),
        ('express', 'Express Delivery'),
        ('overnight', 'Overnight'),
        ('economy', 'Economy'),
        ('pickup_point', 'Pickup Point'),
    )
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPES, default='standard')
    
    # Special services
    requires_signature = models.BooleanField(default=False)
    is_fragile = models.BooleanField(default=False)
    insurance_required = models.BooleanField(default=False)
    insurance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Delivery instructions
    delivery_instructions = models.TextField(blank=True)
    pickup_location = models.JSONField(null=True, blank=True)
    
    # Status tracking
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('created', 'Created'),
        ('booked', 'Booked with Carrier'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed_delivery', 'Failed Delivery'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
        ('error', 'Error'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    status_updated_at = models.DateTimeField(auto_now_add=True)
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # What we pay carrier
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # What customer pays
    markup = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Markup percentage
    
    # Labels and documents
    label_url = models.URLField(blank=True)
    label_pdf = models.FileField(upload_to='labels/', blank=True)
    commercial_invoice_url = models.URLField(blank=True)
    
    # Timestamps
    shipped_at = models.DateTimeField(null=True, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # API source
    created_via_api = models.BooleanField(default=False)
    api_key = models.ForeignKey('core.APIKey', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'shipments'
        verbose_name = 'Shipment'
        verbose_name_plural = 'Shipments'
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['tracking_number']),
            models.Index(fields=['shipment_number']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Shipment {self.shipment_number} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.shipment_number:
            self.shipment_number = self.generate_shipment_number()
        super().save(*args, **kwargs)

    def generate_shipment_number(self):
        """Generate unique shipment number"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d')
        count = Shipment.objects.filter(created_at__date=timezone.now().date()).count() + 1
        return f"SP{timestamp}{count:04d}"


class TrackingEvent(models.Model):
    """Tracking events for shipments"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_events')
    
    # Event details
    event_code = models.CharField(max_length=50)
    event_description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    
    # Event data from carrier
    carrier_event_id = models.CharField(max_length=100, blank=True)
    carrier_raw_data = models.JSONField(null=True, blank=True)
    
    # Timestamps
    event_timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tracking_events'
        verbose_name = 'Tracking Event'
        verbose_name_plural = 'Tracking Events'
        ordering = ['-event_timestamp']
        indexes = [
            models.Index(fields=['shipment', 'event_timestamp']),
        ]

    def __str__(self):
        return f"{self.shipment.shipment_number} - {self.event_description}"


class ShipmentItem(models.Model):
    """Items within a shipment"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='items')
    
    # Item details
    sku = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Quantity and pricing
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Physical properties
    weight = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    country_of_origin = models.CharField(max_length=2, blank=True)  # ISO country code
    hs_code = models.CharField(max_length=20, blank=True)  # Harmonized System code
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'shipment_items'
        verbose_name = 'Shipment Item'
        verbose_name_plural = 'Shipment Items'

    def __str__(self):
        return f"{self.name} x{self.quantity}"


class ShipmentDocument(models.Model):
    """Documents associated with shipments"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='documents')
    
    # Document details
    DOCUMENT_TYPES = (
        ('shipping_label', 'Shipping Label'),
        ('commercial_invoice', 'Commercial Invoice'),
        ('customs_declaration', 'Customs Declaration'),
        ('delivery_receipt', 'Delivery Receipt'),
        ('return_label', 'Return Label'),
        ('other', 'Other'),
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    name = models.CharField(max_length=255)
    
    # File storage
    file = models.FileField(upload_to='shipment_documents/')
    file_url = models.URLField(blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Source
    generated_by_carrier = models.BooleanField(default=False)
    carrier_document_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'shipment_documents'
        verbose_name = 'Shipment Document'
        verbose_name_plural = 'Shipment Documents'

    def __str__(self):
        return f"{self.shipment.shipment_number} - {self.name}"


class ShipmentRate(models.Model):
    """Rate quotes for shipments"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE)
    
    # Quote details
    quote_id = models.CharField(max_length=100, unique=True)
    carrier = models.ForeignKey('carriers.Carrier', on_delete=models.CASCADE)
    service = models.ForeignKey('carriers.CarrierService', on_delete=models.CASCADE)
    
    # Addresses (stored as JSON for quotes)
    origin = models.JSONField()
    destination = models.JSONField()
    
    # Package details
    weight = models.DecimalField(max_digits=8, decimal_places=3)
    dimensions = models.JSONField()  # {length, width, height}
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Service details
    estimated_delivery_days = models.IntegerField(null=True, blank=True)
    service_features = models.JSONField(default=list)
    
    # Quote validity
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_for_shipment = models.ForeignKey(Shipment, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'shipment_rates'
        verbose_name = 'Shipment Rate'
        verbose_name_plural = 'Shipment Rates'
        indexes = [
            models.Index(fields=['company', 'created_at']),
            models.Index(fields=['quote_id']),
        ]

    def __str__(self):
        return f"Quote {self.quote_id} - {self.carrier.name} {self.service.name}"

    def is_expired(self):
        return timezone.now() > self.expires_at
