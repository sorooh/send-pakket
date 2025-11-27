"""
Core models for Send-Pakket Platform
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Extended User model with additional fields for business users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Business information
    company_name = models.CharField(max_length=255, blank=True)
    company_vat_number = models.CharField(max_length=50, blank=True)
    
    # Account type
    ACCOUNT_TYPES = (
        ('individual', 'Individual'),
        ('business', 'Business'),
        ('enterprise', 'Enterprise'),
    )
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='individual')
    
    # Verification status
    is_email_verified = models.BooleanField(default=False)
    is_business_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.email} ({self.company_name or 'Individual'})"


class Company(models.Model):
    """Company model for business accounts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    
    # Platform core integration
    merchant_core = models.OneToOneField('platform_core.MerchantCore', on_delete=models.SET_NULL, null=True, blank=True, related_name='company')
    
    # Company details
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, unique=True)
    vat_number = models.CharField(max_length=50, unique=True)
    
    # Address information
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default='NL')  # ISO country code
    
    # Contact information
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    
    # Business information
    industry = models.CharField(max_length=100, blank=True)
    employee_count = models.IntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_documents = models.JSONField(default=dict, blank=True)
    
    # Payment integration
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name

    def get_merchant_core(self):
        """Get or create merchant core for this company"""
        if not self.merchant_core:
            from platform_core.services import MerchantCoreService
            # Create merchant core with company data
            merchant_data = {
                'merchant_id': f"company_{self.id}",
                'name': self.name,
                'business_type': 'ecommerce',  # Default business type
                'settings': {
                    'industry': self.industry or '',
                    'employee_count': self.employee_count or 0,
                    'annual_revenue': str(self.annual_revenue) if self.annual_revenue else '0'
                }
            }
            self.merchant_core = MerchantCoreService.create_merchant_core(merchant_data)
            self.save(update_fields=['merchant_core'])
        return self.merchant_core

    def get_merchant_limits(self):
        """Get merchant limits from merchant core"""
        merchant_core = self.get_merchant_core()
        return {
            'monthly_shipment_limit': merchant_core.monthly_shipment_limit,
            'api_rate_limit': merchant_core.api_rate_limit,
            'storage_limit_mb': merchant_core.storage_limit_mb
        }


class Address(models.Model):
    """Address model for shipping addresses"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='addresses')
    
    # Address details
    name = models.CharField(max_length=255)  # Address name/label
    contact_person = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    
    # Address fields
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    state_province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2)  # ISO country code
    
    # Address type
    ADDRESS_TYPES = (
        ('pickup', 'Pickup Address'),
        ('return', 'Return Address'),
        ('billing', 'Billing Address'),
        ('warehouse', 'Warehouse'),
    )
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES)
    
    # Settings
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Validation
    is_validated = models.BooleanField(default=False)
    validation_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'addresses'
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        unique_together = ['company', 'address_type', 'is_default']

    def __str__(self):
        return f"{self.name} - {self.company.name}"


class APIKey(models.Model):
    """API Key model for authentication"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='api_keys')
    
    # Key details
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=64, unique=True)
    secret = models.CharField(max_length=128)
    
    # Permissions
    PERMISSION_LEVELS = (
        ('read', 'Read Only'),
        ('write', 'Read Write'),
        ('admin', 'Administrator'),
    )
    permission_level = models.CharField(max_length=20, choices=PERMISSION_LEVELS, default='read')
    
    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    # Settings
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Rate limiting
    rate_limit_per_minute = models.IntegerField(default=100)
    rate_limit_per_hour = models.IntegerField(default=1000)
    rate_limit_per_day = models.IntegerField(default=10000)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'api_keys'
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'

    def __str__(self):
        return f"{self.name} - {self.company.name}"

    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class ActivityLog(models.Model):
    """Activity log for auditing"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Action details
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100, blank=True)
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Result
    SUCCESS_CHOICES = (
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('error', 'Error'),
    )
    status = models.CharField(max_length=20, choices=SUCCESS_CHOICES)
    error_message = models.TextField(blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_logs'
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['company', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self):
        return f"{self.action} by {self.user or self.api_key} at {self.created_at}"
