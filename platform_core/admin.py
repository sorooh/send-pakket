"""
Django Admin model management for the central core
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    PlatformCore, MerchantCore, CoreService,
    MerchantService, CoreConfiguration, CoreEvent, CoreMetric
)


@admin.register(PlatformCore)
class PlatformCoreAdmin(admin.ModelAdmin):
    """
    Platform central core management
    """

    list_display = [
        'platform_name', 'platform_version', 'system_status',
        'total_merchants', 'total_shipments', 'total_revenue',
        'is_maintenance_mode', 'updated_at'
    ]

    list_filter = ['system_status', 'is_maintenance_mode']
    search_fields = ['platform_name', 'platform_domain']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Platform Information', {
            'fields': ('platform_name', 'platform_version', 'platform_domain')
        }),
        ('System Settings', {
            'fields': ('is_maintenance_mode', 'maintenance_message', 'system_status')
        }),
        ('Security Settings', {
            'fields': ('max_login_attempts', 'session_timeout_minutes', 'password_min_length')
        }),
        ('Performance Settings', {
            'fields': ('max_concurrent_requests', 'rate_limit_per_minute', 'cache_timeout_seconds')
        }),
        ('Integration Settings', {
            'fields': ('supported_currencies', 'supported_languages', 'supported_countries')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications_enabled', 'sms_notifications_enabled', 'push_notifications_enabled')
        }),
        ('Backup Settings', {
            'fields': ('backup_frequency_hours', 'backup_retention_days')
        }),
        ('System Statistics', {
            'fields': ('total_merchants', 'total_shipments', 'total_revenue'),
            'classes': ('collapse',)
        }),
        ('Advanced Settings', {
            'fields': ('features_enabled', 'custom_settings'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent adding more than one central core"""
        return not PlatformCore.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the central core"""
        return False


@admin.register(MerchantCore)
class MerchantCoreAdmin(admin.ModelAdmin):
    """
    Merchant cores management
    """

    list_display = [
        'merchant_id', 'name', 'business_type', 'status',
        'total_shipments', 'total_revenue', 'active_shipments',
        'created_at', 'activated_at'
    ]

    list_filter = ['status', 'business_type', 'created_at', 'activated_at']
    search_fields = ['merchant_id', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'activated_at', 'suspended_at']

    fieldsets = (
        ('Basic Merchant Information', {
            'fields': ('platform_core', 'merchant_id', 'name', 'business_type', 'status')
        }),
        ('Merchant Settings', {
            'fields': ('settings', 'preferences'),
            'classes': ('collapse',)
        }),
        ('Usage Limits', {
            'fields': ('monthly_shipment_limit', 'api_rate_limit', 'storage_limit_mb')
        }),
        ('Merchant Statistics', {
            'fields': ('total_shipments', 'total_revenue', 'active_shipments'),
            'classes': ('collapse',)
        }),
        ('Merchant Integrations', {
            'fields': ('integrations', 'security_settings'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'activated_at', 'suspended_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_merchants', 'suspend_merchants']

    def activate_merchants(self, request, queryset):
        """Activate selected merchants"""
        for merchant in queryset:
            if merchant.status == 'pending':
                merchant.activate()
        self.message_user(request, f'Activated {queryset.count()} merchants')
    activate_merchants.short_description = "Activate selected merchants"

    def suspend_merchants(self, request, queryset):
        """Suspend selected merchants"""
        for merchant in queryset:
            if merchant.status == 'suspended':
                merchant.suspend()
        self.message_user(request, f'Suspended {queryset.count()} merchants')
    suspend_merchants.short_description = "Suspend selected merchants"


@admin.register(CoreService)
class CoreServiceAdmin(admin.ModelAdmin):
    """
    Core services management
    """

    list_display = [
        'service_name', 'display_name', 'service_type', 'status',
        'version', 'total_requests', 'active_users', 'is_available'
    ]

    list_filter = ['service_type', 'status']
    search_fields = ['service_name', 'display_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_requests']

    fieldsets = (
        ('Service Information', {
            'fields': ('service_name', 'display_name', 'description', 'service_type')
        }),
        ('Service Status', {
            'fields': ('status', 'version')
        }),
        ('Service Settings', {
            'fields': ('configuration',),
            'classes': ('collapse',)
        }),
        ('Service Limits', {
            'fields': ('max_requests_per_minute', 'max_requests_per_hour')
        }),
        ('Usage Statistics', {
            'fields': ('total_requests', 'active_users'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MerchantService)
class MerchantServiceAdmin(admin.ModelAdmin):
    """
    Merchant services management
    """

    list_display = [
        'merchant_name', 'service_display_name', 'service_type',
        'is_enabled', 'usage_count', 'last_used_at'
    ]

    list_filter = ['is_enabled', 'core_service__service_type', 'last_used_at']
    search_fields = ['merchant_core__name', 'merchant_core__merchant_id', 'core_service__display_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'usage_count', 'last_used_at']

    fieldsets = (
        ('Connection', {
            'fields': ('merchant_core', 'core_service')
        }),
        ('Merchant Service Settings', {
            'fields': ('is_enabled', 'merchant_config', 'custom_limits')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used_at'),
            'classes': ('collapse',)
        }),
    )

    def merchant_name(self, obj):
        return obj.merchant_core.name
    merchant_name.short_description = "Merchant"

    def service_display_name(self, obj):
        return obj.core_service.display_name
    service_display_name.short_description = "Service"

    def service_type(self, obj):
        return obj.core_service.service_type
    service_type.short_description = "Service Type"


@admin.register(CoreConfiguration)
class CoreConfigurationAdmin(admin.ModelAdmin):
    """
    Core configurations management
    """

    list_display = [
        'config_key', 'scope', 'config_value_preview',
        'merchant_name', 'service_name', 'is_editable', 'updated_at'
    ]

    list_filter = ['scope', 'is_editable', 'requires_restart']
    search_fields = ['config_key', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Configuration Information', {
            'fields': ('scope', 'config_key', 'config_value', 'description')
        }),
        ('Permissions', {
            'fields': ('is_editable', 'requires_restart')
        }),
        ('Connection', {
            'fields': ('merchant_core', 'core_service'),
            'classes': ('collapse',)
        }),
    )

    def config_value_preview(self, obj):
        """Configuration value preview"""
        value_str = str(obj.config_value)
        if len(value_str) > 50:
            return value_str[:47] + "..."
        return value_str
    config_value_preview.short_description = "Value"

    def merchant_name(self, obj):
        return obj.merchant_core.name if obj.merchant_core else "-"
    merchant_name.short_description = "Merchant"

    def service_name(self, obj):
        return obj.core_service.service_name if obj.core_service else "-"
    service_name.short_description = "Service"


@admin.register(CoreEvent)
class CoreEventAdmin(admin.ModelAdmin):
    """
    Core events management
    """

    list_display = [
        'level_colored', 'event_type', 'title', 'merchant_name',
        'service_name', 'created_at'
    ]

    list_filter = ['event_type', 'level', 'created_at']
    search_fields = ['title', 'description', 'merchant_core__name']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'level', 'title', 'description')
        }),
        ('Additional Data', {
            'fields': ('metadata', 'source_ip', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Connection', {
            'fields': ('merchant_core', 'core_service'),
            'classes': ('collapse',)
        }),
    )

    def level_colored(self, obj):
        """Display event level with colors"""
        colors = {
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.level, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.level.upper()
        )
    level_colored.short_description = "Level"

    def merchant_name(self, obj):
        return obj.merchant_core.name if obj.merchant_core else "-"
    merchant_name.short_description = "Merchant"

    def service_name(self, obj):
        return obj.core_service.service_name if obj.core_service else "-"
    service_name.short_description = "Service"

    def has_add_permission(self, request):
        """Prevent manual event addition"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent event deletion"""
        return False


@admin.register(CoreMetric)
class CoreMetricAdmin(admin.ModelAdmin):
    """
    Core metrics management
    """

    list_display = [
        'metric_name', 'metric_type', 'metric_value', 'unit',
        'merchant_name', 'service_name', 'recorded_at'
    ]

    list_filter = ['metric_type', 'recorded_at']
    search_fields = ['metric_name', 'merchant_core__name']
    readonly_fields = ['id', 'recorded_at']
    ordering = ['-recorded_at']

    fieldsets = (
        ('Metric Information', {
            'fields': ('metric_type', 'metric_name', 'metric_value', 'unit')
        }),
        ('Additional Data', {
            'fields': ('tags', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Connection', {
            'fields': ('merchant_core', 'core_service'),
            'classes': ('collapse',)
        }),
    )

    def merchant_name(self, obj):
        return obj.merchant_core.name if obj.merchant_core else "-"
    merchant_name.short_description = "Merchant"

    def service_name(self, obj):
        return obj.core_service.service_name if obj.core_service else "-"
    service_name.short_description = "Service"

    def has_add_permission(self, request):
        """Prevent manual metric addition"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent metric deletion"""
        return False
