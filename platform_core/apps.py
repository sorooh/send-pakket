"""
تكوين تطبيق النواة المركزية
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class PlatformCoreConfig(AppConfig):
    """
    تكوين تطبيق النواة المركزية للمنصة
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'platform_core'
    verbose_name = 'Platform Core'

    def ready(self):
        """
        إعداد التطبيق عند بدء التشغيل
        """
        # استيراد الإشارات
        from . import signals

        # إنشاء البيانات الأولية بعد الترحيل
        post_migrate.connect(self.create_initial_data, sender=self)

    def create_initial_data(self, **kwargs):
        """
        إنشاء البيانات الأولية للنواة المركزية
        """
        try:
            from .services import PlatformCoreService
            from .models import CoreService

            # إنشاء النواة المركزية إذا لم تكن موجودة
            platform_core = PlatformCoreService.get_platform_core()

            # إنشاء الخدمات الأساسية
            self.create_core_services()
        except Exception as e:
            # في حالة فشل إنشاء البيانات الأولية (مثل عدم توفر Redis)
            # سنسجل الخطأ ولكن لن نفشل في الترحيل
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create initial data: {e}")
            # سننشئ البيانات الأساسية بدون استخدام cache
            self.create_core_services_fallback()

    def create_core_services_fallback(self):
        """
        إنشاء الخدمات الأساسية بدون استخدام cache
        """
        from .models import CoreService, PlatformCore

        # إنشاء النواة المركزية إذا لم تكن موجودة
        platform_core, created = PlatformCore.objects.get_or_create(
            platform_name='Send-Pakket Platform Core',
            defaults={
                'platform_version': '1.0.0',
                'platform_domain': 'sendpakket.com',
                'is_maintenance_mode': False,
                'max_login_attempts': 5,
                'session_timeout_minutes': 60,
                'password_min_length': 8,
                'max_concurrent_requests': 1000,
                'rate_limit_per_minute': 100,
                'cache_timeout_seconds': 3600,
                'supported_currencies': ['EUR', 'USD', 'GBP'],
                'supported_languages': ['en', 'nl', 'ar'],
                'supported_countries': ['NL', 'BE', 'DE', 'FR'],
                'email_notifications_enabled': True,
                'sms_notifications_enabled': False,
                'push_notifications_enabled': True,
                'backup_frequency_hours': 24,
                'backup_retention_days': 30,
                'system_status': 'active',
                'total_merchants': 0,
                'total_shipments': 0,
                'total_revenue': 0.0,
                'custom_settings': {},
                'features_enabled': ['shipping', 'payment', 'analytics']
            }
        )

        # إنشاء الخدمات الأساسية
        core_services_data = [
            {
                'service_name': 'shipping',
                'display_name': 'Shipping Service',
                'description': 'خدمة الشحن والتوصيل',
                'service_type': 'shipping',
                'configuration': {
                    'max_shipments_per_day': 10000,
                    'supported_carriers': ['dhl', 'fedex', 'ups', 'postnl'],
                    'tracking_enabled': True
                }
            },
            {
                'service_name': 'payment',
                'display_name': 'Payment Service',
                'description': 'خدمة المعالجة المالية والمدفوعات',
                'service_type': 'payment',
                'configuration': {
                    'supported_gateways': ['stripe', 'paypal'],
                    'auto_capture': True,
                    'refund_window_days': 30
                }
            },
            {
                'service_name': 'analytics',
                'display_name': 'Analytics Service',
                'description': 'خدمة التحليلات والتقارير',
                'service_type': 'analytics',
                'configuration': {
                    'retention_days': 365,
                    'real_time_enabled': True,
                    'custom_dashboards': True
                }
            },
            {
                'service_name': 'notification',
                'display_name': 'Notification Service',
                'description': 'خدمة الإشعارات والتنبيهات',
                'service_type': 'notification',
                'configuration': {
                    'email_enabled': True,
                    'sms_enabled': False,
                    'push_enabled': True,
                    'webhook_enabled': True
                }
            },
            {
                'service_name': 'storage',
                'display_name': 'Storage Service',
                'description': 'خدمة التخزين والملفات',
                'service_type': 'storage',
                'configuration': {
                    'max_file_size_mb': 10,
                    'allowed_extensions': ['pdf', 'jpg', 'png', 'doc', 'xls'],
                    'backup_enabled': True
                }
            },
            {
                'service_name': 'integration',
                'display_name': 'Integration Service',
                'description': 'خدمة التكامل مع الأنظمة الخارجية',
                'service_type': 'integration',
                'configuration': {
                    'webhook_timeout_seconds': 30,
                    'retry_attempts': 3,
                    'supported_apis': ['rest', 'soap', 'graphql']
                }
            }
        ]

        for service_data in core_services_data:
            CoreService.objects.get_or_create(
                service_name=service_data['service_name'],
                defaults=service_data
            )

    def create_core_services(self):
        """
        إنشاء الخدمات الأساسية للنواة
        """
        from .models import CoreService

        core_services_data = [
            {
                'service_name': 'shipping',
                'display_name': 'Shipping Service',
                'description': 'خدمة الشحن والتوصيل',
                'service_type': 'shipping',
                'configuration': {
                    'max_shipments_per_day': 10000,
                    'supported_carriers': ['dhl', 'fedex', 'ups', 'postnl'],
                    'tracking_enabled': True
                }
            },
            {
                'service_name': 'payment',
                'display_name': 'Payment Service',
                'description': 'خدمة المعالجة المالية والمدفوعات',
                'service_type': 'payment',
                'configuration': {
                    'supported_gateways': ['stripe', 'paypal'],
                    'auto_capture': True,
                    'refund_window_days': 30
                }
            },
            {
                'service_name': 'analytics',
                'display_name': 'Analytics Service',
                'description': 'خدمة التحليلات والتقارير',
                'service_type': 'analytics',
                'configuration': {
                    'retention_days': 365,
                    'real_time_enabled': True,
                    'custom_dashboards': True
                }
            },
            {
                'service_name': 'notification',
                'display_name': 'Notification Service',
                'description': 'خدمة الإشعارات والتنبيهات',
                'service_type': 'notification',
                'configuration': {
                    'email_enabled': True,
                    'sms_enabled': False,
                    'push_enabled': True,
                    'webhook_enabled': True
                }
            },
            {
                'service_name': 'storage',
                'display_name': 'Storage Service',
                'description': 'خدمة التخزين والملفات',
                'service_type': 'storage',
                'configuration': {
                    'max_file_size_mb': 10,
                    'allowed_extensions': ['pdf', 'jpg', 'png', 'doc', 'xls'],
                    'backup_enabled': True
                }
            },
            {
                'service_name': 'integration',
                'display_name': 'Integration Service',
                'description': 'خدمة التكامل مع الأنظمة الخارجية',
                'service_type': 'integration',
                'configuration': {
                    'webhook_timeout_seconds': 30,
                    'retry_attempts': 3,
                    'supported_apis': ['rest', 'soap', 'graphql']
                }
            }
        ]

        for service_data in core_services_data:
            CoreService.objects.get_or_create(
                service_name=service_data['service_name'],
                defaults=service_data
            )
