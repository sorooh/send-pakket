"""
Payment models for Send-Pakket Platform
"""

from django.db import models
from decimal import Decimal
import uuid


class Subscription(models.Model):
    """Subscription plans for companies"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField('core.Company', on_delete=models.CASCADE, related_name='subscription')
    
    # Plan details
    PLAN_TYPES = (
        ('free', 'Free'),
        ('starter', 'Starter'),
        ('business', 'Business'),
        ('enterprise', 'Enterprise'),
        ('custom', 'Custom'),
    )
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='free')
    
    # Billing
    BILLING_CYCLES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='monthly')
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Limits and features
    monthly_shipment_limit = models.IntegerField(null=True, blank=True)  # null = unlimited
    api_calls_per_minute = models.IntegerField(default=60)
    included_features = models.JSONField(default=list)  # List of feature codes
    
    # Status
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Billing dates
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_start = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # External billing integration
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    
    # Usage tracking
    current_period_shipments = models.IntegerField(default=0)
    total_shipments = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.company.name} - {self.plan_type} ({self.status})"

    def is_within_limits(self):
        """Check if company is within shipment limits"""
        if self.monthly_shipment_limit is None:
            return True
        return self.current_period_shipments < self.monthly_shipment_limit


class Invoice(models.Model):
    """Invoices for subscriptions and usage"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True)
    
    # Billing period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Status
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Payment details
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    # External references
    stripe_invoice_id = models.CharField(max_length=255, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    
    # Files
    pdf_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.company.name}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from datetime import datetime
        year_month = datetime.now().strftime('%Y%m')
        count = Invoice.objects.filter(created_at__year=datetime.now().year, 
                                     created_at__month=datetime.now().month).count() + 1
        return f"INV-{year_month}-{count:04d}"


class InvoiceItem(models.Model):
    """Line items for invoices"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    
    # Item details
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Type of charge
    ITEM_TYPES = (
        ('subscription', 'Subscription Fee'),
        ('usage', 'Usage Fee'),
        ('overage', 'Overage Fee'),
        ('setup', 'Setup Fee'),
        ('addon', 'Add-on Feature'),
        ('discount', 'Discount'),
    )
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='subscription')
    
    # Related objects
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'invoice_items'
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'

    def __str__(self):
        return f"{self.description} - €{self.total_price}"


class Payment(models.Model):
    """Payment records"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Payment method
    PAYMENT_METHODS = (
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('ideal', 'iDEAL'),
        ('paypal', 'PayPal'),
        ('sepa_debit', 'SEPA Direct Debit'),
        ('other', 'Other'),
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    
    # Status
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # External references
    stripe_payment_id = models.CharField(max_length=255, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_client_secret = models.CharField(max_length=255, blank=True)
    gateway_transaction_id = models.CharField(max_length=255, blank=True)
    
    # Additional details
    failure_reason = models.TextField(blank=True)
    gateway_response = models.JSONField(null=True, blank=True)
    
    # Timestamps
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['invoice']),
        ]

    def __str__(self):
        return f"Payment €{self.amount} for {self.invoice.invoice_number}"


class UsageRecord(models.Model):
    """Track usage for billing purposes"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='usage_records')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='usage_records')
    
    # Usage details
    USAGE_TYPES = (
        ('shipment', 'Shipment Created'),
        ('api_call', 'API Call'),
        ('webhook', 'Webhook Delivery'),
        ('storage', 'Document Storage'),
        ('premium_feature', 'Premium Feature Usage'),
    )
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    
    # Billing
    unit_price = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_billable = models.BooleanField(default=True)
    is_included_in_plan = models.BooleanField(default=False)
    
    # Related objects
    shipment = models.ForeignKey('shipping.Shipment', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Billing period
    billing_period_start = models.DateTimeField()
    billing_period_end = models.DateTimeField()
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'usage_records'
        verbose_name = 'Usage Record'
        verbose_name_plural = 'Usage Records'
        indexes = [
            models.Index(fields=['company', 'billing_period_start', 'billing_period_end']),
            models.Index(fields=['subscription', 'usage_type']),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.usage_type} x{self.quantity}"


class ShipmentTransaction(models.Model):
    """Financial transactions for individual shipments"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='shipment_transactions')
    shipment = models.OneToOneField('shipping.Shipment', on_delete=models.CASCADE, related_name='transaction', null=True, blank=True)
    
    # Costs
    carrier_cost = models.DecimalField(max_digits=10, decimal_places=2)  # What we pay carrier
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Our fee
    customer_charge = models.DecimalField(max_digits=10, decimal_places=2)  # What customer pays
    
    # Profit calculation
    gross_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit_margin_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Currency
    currency = models.CharField(max_length=3, default='EUR')
    
    # Billing status
    BILLING_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('billed', 'Billed'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    )
    billing_status = models.CharField(max_length=20, choices=BILLING_STATUS_CHOICES, default='pending')
    
    # Payment details
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    billed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shipment_transactions'
        verbose_name = 'Shipment Transaction'
        verbose_name_plural = 'Shipment Transactions'
        indexes = [
            models.Index(fields=['company', 'billing_status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Transaction for {self.shipment.shipment_number}"

    def save(self, *args, **kwargs):
        # Calculate profit metrics
        self.gross_profit = self.customer_charge - self.carrier_cost - self.platform_fee
        if self.customer_charge > 0:
            self.profit_margin_percent = (self.gross_profit / self.customer_charge) * 100
        super().save(*args, **kwargs)
