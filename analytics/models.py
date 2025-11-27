"""
Analytics models for Send-Pakket Platform
"""

from django.db import models
from decimal import Decimal
import uuid


class PerformanceMetric(models.Model):
    """Daily performance metrics"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='metrics', null=True, blank=True)
    
    # Time period
    date = models.DateField()
    
    # Shipment metrics
    total_shipments = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    returned_shipments = models.IntegerField(default=0)
    cancelled_shipments = models.IntegerField(default=0)
    
    # Performance metrics
    avg_delivery_time_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    delivery_success_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Financial metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_profit_per_shipment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Volume metrics by carrier
    carrier_volumes = models.JSONField(default=dict, blank=True)  # {carrier_id: volume}
    carrier_costs = models.JSONField(default=dict, blank=True)    # {carrier_id: total_cost}
    
    # Geographic distribution
    country_volumes = models.JSONField(default=dict, blank=True)  # {country_code: volume}
    
    # API usage
    api_calls_total = models.IntegerField(default=0)
    api_calls_successful = models.IntegerField(default=0)
    api_errors = models.IntegerField(default=0)
    avg_api_response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Customer metrics
    new_customers = models.IntegerField(default=0)
    active_customers = models.IntegerField(default=0)
    churned_customers = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'performance_metrics'
        verbose_name = 'Performance Metric'
        verbose_name_plural = 'Performance Metrics'
        unique_together = ['company', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['company', 'date']),
        ]

    def __str__(self):
        company_name = self.company.name if self.company else 'Platform-wide'
        return f"{company_name} metrics for {self.date}"


class CarrierPerformance(models.Model):
    """Carrier performance tracking"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carrier = models.ForeignKey('carriers.Carrier', on_delete=models.CASCADE, related_name='performance_metrics')
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='carrier_performance', null=True, blank=True)
    
    # Time period
    date = models.DateField()
    
    # Volume metrics
    total_shipments = models.IntegerField(default=0)
    total_weight_kg = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Performance metrics
    delivered_shipments = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    delivery_success_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Timing metrics
    avg_pickup_time_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    avg_delivery_time_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Cost metrics
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_cost_per_kg = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    avg_cost_per_shipment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # API performance
    api_calls = models.IntegerField(default=0)
    api_errors = models.IntegerField(default=0)
    avg_api_response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    api_uptime_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Quality metrics
    damage_claims = models.IntegerField(default=0)
    lost_packages = models.IntegerField(default=0)
    customer_complaints = models.IntegerField(default=0)
    
    # Rating (calculated)
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)  # 1-5 scale
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carrier_performance'
        verbose_name = 'Carrier Performance'
        verbose_name_plural = 'Carrier Performance'
        unique_together = ['carrier', 'company', 'date']
        indexes = [
            models.Index(fields=['carrier', 'date']),
            models.Index(fields=['company', 'date']),
        ]

    def __str__(self):
        company_name = self.company.name if self.company else 'Platform-wide'
        return f"{self.carrier.name} performance for {company_name} on {self.date}"


class CustomerInsight(models.Model):
    """Customer behavior and insights"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField('core.Company', on_delete=models.CASCADE, related_name='insights')
    
    # Account metrics
    account_age_days = models.IntegerField(default=0)
    total_shipments = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avg_monthly_shipments = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_monthly_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Behavior patterns
    preferred_carriers = models.JSONField(default=dict, blank=True)  # {carrier_id: usage_count}
    preferred_services = models.JSONField(default=dict, blank=True)  # {service_id: usage_count}
    shipping_countries = models.JSONField(default=dict, blank=True)  # {country: shipment_count}
    
    # Usage patterns
    peak_shipping_hours = models.JSONField(default=list, blank=True)  # [hour_of_day]
    peak_shipping_days = models.JSONField(default=list, blank=True)   # [day_of_week]
    avg_package_weight = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    avg_package_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Growth metrics
    GROWTH_STAGES = (
        ('new', 'New Customer'),
        ('growing', 'Growing'),
        ('stable', 'Stable'),
        ('declining', 'Declining'),
        ('churning', 'Churning'),
        ('churned', 'Churned'),
    )
    growth_stage = models.CharField(max_length=20, choices=GROWTH_STAGES, default='new')
    monthly_growth_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Risk assessment
    RISK_LEVELS = (
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    )
    churn_risk_level = models.CharField(max_length=20, choices=RISK_LEVELS, default='low')
    churn_probability = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Customer satisfaction
    avg_delivery_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    support_tickets_count = models.IntegerField(default=0)
    complaints_count = models.IntegerField(default=0)
    
    # Last activity
    last_shipment_date = models.DateTimeField(null=True, blank=True)
    last_api_call_date = models.DateTimeField(null=True, blank=True)
    days_since_last_activity = models.IntegerField(null=True, blank=True)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'customer_insights'
        verbose_name = 'Customer Insight'
        verbose_name_plural = 'Customer Insights'

    def __str__(self):
        return f"Insights for {self.company.name}"


class RevenueAnalytics(models.Model):
    """Revenue analytics and forecasting"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Time period
    period_type = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ])
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Revenue breakdown
    subscription_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transaction_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    platform_fees = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Costs breakdown
    carrier_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    operational_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Profit metrics
    gross_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gross_margin_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Volume metrics
    total_shipments = models.IntegerField(default=0)
    total_customers = models.IntegerField(default=0)
    new_customers = models.IntegerField(default=0)
    
    # KPIs
    revenue_per_shipment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    revenue_per_customer = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    customer_acquisition_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    customer_lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Growth metrics
    revenue_growth_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    customer_growth_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Forecasting
    forecasted_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    forecast_accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'revenue_analytics'
        verbose_name = 'Revenue Analytics'
        verbose_name_plural = 'Revenue Analytics'
        unique_together = ['period_type', 'period_start', 'period_end']
        indexes = [
            models.Index(fields=['period_type', 'period_start']),
        ]

    def __str__(self):
        return f"{self.period_type} revenue analytics for {self.period_start.date()}"


class APIUsageStats(models.Model):
    """API usage statistics"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='api_stats', null=True, blank=True)
    api_key = models.ForeignKey('core.APIKey', on_delete=models.CASCADE, related_name='usage_stats', null=True, blank=True)
    
    # Time period
    date = models.DateField()
    hour = models.IntegerField(null=True, blank=True)  # 0-23, null for daily stats
    
    # Request metrics
    total_requests = models.IntegerField(default=0)
    successful_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    rate_limited_requests = models.IntegerField(default=0)
    
    # Endpoint breakdown
    endpoint_stats = models.JSONField(default=dict, blank=True)  # {endpoint: request_count}
    
    # Response time metrics
    avg_response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    p95_response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    p99_response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Error breakdown
    error_codes = models.JSONField(default=dict, blank=True)  # {error_code: count}
    
    # Data transfer
    bytes_sent = models.BigIntegerField(default=0)
    bytes_received = models.BigIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'api_usage_stats'
        verbose_name = 'API Usage Stats'
        verbose_name_plural = 'API Usage Stats'
        unique_together = ['company', 'api_key', 'date', 'hour']
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['api_key', 'date']),
        ]

    def __str__(self):
        period = f"{self.date} {self.hour}:00" if self.hour is not None else str(self.date)
        return f"API usage for {self.company.name if self.company else 'Platform'} - {period}"
