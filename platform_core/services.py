"""
Central Core Services
Services for managing the central core, merchants, and services
"""

import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction, models
from django.conf import settings

from .models import (
    PlatformCore, MerchantCore, CoreService,
    MerchantService, CoreConfiguration, CoreEvent, CoreMetric
)

logger = logging.getLogger(__name__)


class PlatformCoreService:
    """
    Platform Core Management Service
    """

    CACHE_KEY_PLATFORM_CORE = 'platform_core_instance'
    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def get_platform_core(cls) -> PlatformCore:
        """
        Get platform core instance with caching
        """
        try:
            platform_core = cache.get(cls.CACHE_KEY_PLATFORM_CORE)
            if not platform_core:
                platform_core = PlatformCore.get_instance()
                cache.set(cls.CACHE_KEY_PLATFORM_CORE, platform_core, cls.CACHE_TIMEOUT)
        except Exception as e:
            # Fallback to database if cache fails
            logger.warning(f"Cache unavailable, falling back to database: {e}")
            platform_core = PlatformCore.get_instance()
        return platform_core

    @classmethod
    def update_platform_stats(cls):
        """
        Update platform statistics
        """
        platform_core = cls.get_platform_core()

        # Calculate merchant statistics
        total_merchants = MerchantCore.objects.filter(status='active').count()
        total_shipments = MerchantCore.objects.aggregate(
            total=models.Sum('total_shipments')
        )['total'] or 0
        total_revenue = MerchantCore.objects.aggregate(
            total=models.Sum('total_revenue')
        )['total'] or 0

        platform_core.total_merchants = total_merchants
        platform_core.total_shipments = total_shipments
        platform_core.total_revenue = total_revenue
        platform_core.save()

        # Update cache
        try:
            cache.set(cls.CACHE_KEY_PLATFORM_CORE, platform_core, cls.CACHE_TIMEOUT)
        except Exception as e:
            logger.warning(f"Failed to update cache: {e}")

        logger.info(f"Platform stats updated: {total_merchants} merchants, {total_shipments} shipments")

    @classmethod
    def set_maintenance_mode(cls, enabled: bool, message: str = ""):
        """
        Enable/disable maintenance mode
        """
        platform_core = cls.get_platform_core()
        platform_core.is_maintenance_mode = enabled
        platform_core.maintenance_message = message
        platform_core.system_status = 'maintenance' if enabled else 'operational'
        platform_core.save()

        # Update cache
        try:
            cache.set(cls.CACHE_KEY_PLATFORM_CORE, platform_core, cls.CACHE_TIMEOUT)
        except Exception as e:
            logger.warning(f"Failed to update cache: {e}")

        # Log event
        CoreEvent.objects.create(
            event_type='system',
            level='warning' if enabled else 'info',
            title='Maintenance Mode ' + ('Enabled' if enabled else 'Disabled'),
            description=f"Platform maintenance mode {'enabled' if enabled else 'disabled'}: {message}",
            metadata={'maintenance_mode': enabled, 'message': message}
        )

        logger.info(f"Maintenance mode {'enabled' if enabled else 'disabled'}")


class MerchantCoreService:
    """
    Merchant Cores Management Service
    """

    @staticmethod
    def get_merchant_core(company) -> Optional[MerchantCore]:
        """
        Get merchant core for a company
        """
        try:
            return company.merchant_core
        except MerchantCore.DoesNotExist:
            return None

    @staticmethod
    def create_merchant_core(merchant_data: Dict[str, Any]) -> MerchantCore:
        """
        Create new merchant core
        """
        platform_core = PlatformCoreService.get_platform_core()

        with transaction.atomic():
            merchant_core = MerchantCore.objects.create(
                platform_core=platform_core,
                merchant_id=merchant_data['merchant_id'],
                name=merchant_data['name'],
                business_type=merchant_data.get('business_type', 'ecommerce'),
                settings=merchant_data.get('settings', {}),
                preferences=merchant_data.get('preferences', {}),
                monthly_shipment_limit=merchant_data.get('monthly_shipment_limit', 1000),
                api_rate_limit=merchant_data.get('api_rate_limit', 100),
                storage_limit_mb=merchant_data.get('storage_limit_mb', 1000),
            )

            # Create default services for merchant
            MerchantCoreService._create_default_services(merchant_core)

            # Log event
            CoreEvent.objects.create(
                event_type='merchant',
                level='info',
                title='Merchant Core Created',
                description=f"New merchant core created: {merchant_core.name}",
                merchant_core=merchant_core,
                metadata={'merchant_id': merchant_core.merchant_id}
            )

            logger.info(f"Created merchant core: {merchant_core.merchant_id}")

        return merchant_core

    @staticmethod
    def _create_default_services(merchant_core: MerchantCore):
        """
        Create default services for new merchant
        """
        default_services = [
            {'service_name': 'shipping', 'display_name': 'Shipping Service', 'service_type': 'shipping'},
            {'service_name': 'payment', 'display_name': 'Payment Service', 'service_type': 'payment'},
            {'service_name': 'analytics', 'display_name': 'Analytics Service', 'service_type': 'analytics'},
            {'service_name': 'notification', 'display_name': 'Notification Service', 'service_type': 'notification'},
        ]

        for service_data in default_services:
            service, created = CoreService.objects.get_or_create(
                service_name=service_data['service_name'],
                defaults=service_data
            )

            MerchantService.objects.create(
                merchant_core=merchant_core,
                core_service=service,
                is_enabled=True,
                merchant_config={}
            )

    @staticmethod
    def activate_merchant(merchant_core: MerchantCore, activated_by: str = None):
        """
        Activate merchant
        """
        merchant_core.activate()

        # Log event
        CoreEvent.objects.create(
            event_type='merchant',
            level='info',
            title='Merchant Activated',
            description=f"Merchant {merchant_core.name} has been activated",
            merchant_core=merchant_core,
            metadata={'activated_by': activated_by}
        )

        # Record metric
        CoreMetric.objects.create(
            metric_type='business',
            metric_name='merchant_activated',
            metric_value=1,
            merchant_core=merchant_core,
            tags={'action': 'activation'}
        )

        logger.info(f"Activated merchant: {merchant_core.merchant_id}")

    @staticmethod
    def suspend_merchant(merchant_core: MerchantCore, reason: str = "", suspended_by: str = None):
        """
        Suspend merchant
        """
        merchant_core.suspend()

        # Log event
        CoreEvent.objects.create(
            event_type='merchant',
            level='warning',
            title='Merchant Suspended',
            description=f"Merchant {merchant_core.name} has been suspended: {reason}",
            merchant_core=merchant_core,
            metadata={'reason': reason, 'suspended_by': suspended_by}
        )

        logger.warning(f"Suspended merchant: {merchant_core.merchant_id}, reason: {reason}")

    @staticmethod
    def check_merchant_limits(merchant_core: MerchantCore) -> Dict[str, bool]:
        """
        Check merchant limits
        """
        limits_status = {
            'can_create_shipment': merchant_core.can_create_shipment(),
            'within_shipment_limit': merchant_core.active_shipments < merchant_core.monthly_shipment_limit,
            'is_active': merchant_core.is_active(),
        }

        return limits_status

    @staticmethod
    def update_merchant_stats(merchant_core: MerchantCore):
        """
        Update merchant statistics
        """
        # This function will be updated later when connected to other apps
        # like payments and logistics
        pass


class CoreServiceManager:
    """
    Central Core Services Manager
    """

    @staticmethod
    def get_available_services() -> List[CoreService]:
        """
        Get available services
        """
        return CoreService.objects.filter(status='active')

    @staticmethod
    def get_service_by_name(service_name: str) -> Optional[CoreService]:
        """
        Get service by name
        """
        try:
            return CoreService.objects.get(service_name=service_name, status='active')
        except CoreService.DoesNotExist:
            return None

    @staticmethod
    def update_service_usage(service: CoreService, merchant_core: MerchantCore = None):
        """
        Update service usage
        """
        service.total_requests += 1
        service.save()

        if merchant_core:
            merchant_service, created = MerchantService.objects.get_or_create(
                merchant_core=merchant_core,
                core_service=service,
                defaults={'is_enabled': True}
            )
            merchant_service.increment_usage()

    @staticmethod
    def check_service_limits(service: CoreService, merchant_core: MerchantCore = None) -> bool:
        """
        Check service limits
        """
        # Check general service limits
        if service.total_requests >= service.max_requests_per_hour:
            return False

        # Check merchant limits if specified
        if merchant_core:
            try:
                merchant_service = MerchantService.objects.get(
                    merchant_core=merchant_core,
                    core_service=service
                )
                custom_limits = merchant_service.custom_limits

                if custom_limits.get('max_requests_per_hour'):
                    if merchant_service.usage_count >= custom_limits['max_requests_per_hour']:
                        return False

            except MerchantService.DoesNotExist:
                return False

        return True


class CoreConfigurationService:
    """
    Core Configuration Management Service
    """

    CACHE_KEY_CONFIG = 'core_config_{}'
    CACHE_TIMEOUT = 1800  # 30 minutes

    @staticmethod
    def get_config_value(config_key: str, scope: str = 'global',
                        merchant_core: MerchantCore = None,
                        core_service: CoreService = None) -> Any:
        """
        Get configuration value
        """
        cache_key = CoreConfigurationService.CACHE_KEY_CONFIG.format(
            f"{scope}_{config_key}_{merchant_core.id if merchant_core else 'global'}_{core_service.id if core_service else 'global'}"
        )

        try:
            value = cache.get(cache_key)
            if value is not None:
                return value
        except Exception as e:
            logger.warning(f"Cache unavailable for config {config_key}: {e}")

        try:
            config = CoreConfiguration.objects.get(
                scope=scope,
                config_key=config_key,
                merchant_core=merchant_core,
                core_service=core_service
            )
            value = config.config_value
            try:
                cache.set(cache_key, value, CoreConfigurationService.CACHE_TIMEOUT)
            except Exception as e:
                logger.warning(f"Failed to set cache for config {config_key}: {e}")
            return value
        except CoreConfiguration.DoesNotExist:
            return None

    @staticmethod
    def set_config_value(config_key: str, config_value: Any, scope: str = 'global',
                        merchant_core: MerchantCore = None, core_service: CoreService = None,
                        description: str = ""):
        """
        Set configuration value
        """
        config, created = CoreConfiguration.objects.update_or_create(
            scope=scope,
            config_key=config_key,
            merchant_core=merchant_core,
            core_service=core_service,
            defaults={
                'config_value': config_value,
                'description': description
            }
        )

        # Update cache
        cache_key = CoreConfigurationService.CACHE_KEY_CONFIG.format(
            f"{scope}_{config_key}_{merchant_core.id if merchant_core else 'global'}_{core_service.id if core_service else 'global'}"
        )
        try:
            cache.set(cache_key, config_value, CoreConfigurationService.CACHE_TIMEOUT)
        except Exception as e:
            logger.warning(f"Failed to set cache for config {config_key}: {e}")

        # Log event
        CoreEvent.objects.create(
            event_type='system',
            level='info',
            title='Configuration Updated',
            description=f"Configuration {config_key} updated in scope {scope}",
            merchant_core=merchant_core,
            core_service=core_service,
            metadata={
                'config_key': config_key,
                'scope': scope,
                'old_value': config.config_value if not created else None,
                'new_value': config_value
            }
        )

        return config


class CoreEventService:
    """
    Core Events Management Service
    """

    @staticmethod
    def log_event(event_type: str, level: str, title: str, description: str,
                  merchant_core: MerchantCore = None, core_service: CoreService = None,
                  metadata: Dict = None, source_ip: str = None, user_agent: str = None):
        """
        Log event in core
        """
        event = CoreEvent.objects.create(
            event_type=event_type,
            level=level,
            title=title,
            description=description,
            merchant_core=merchant_core,
            core_service=core_service,
            metadata=metadata or {},
            source_ip=source_ip,
            user_agent=user_agent
        )

        # Log in general log
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, f"Core Event: {title} - {description}")

        return event

    @staticmethod
    def get_recent_events(limit: int = 50, event_type: str = None,
                         merchant_core: MerchantCore = None) -> List[CoreEvent]:
        """
        Get recent events
        """
        queryset = CoreEvent.objects.all()

        if event_type:
            queryset = queryset.filter(event_type=event_type)

        if merchant_core:
            queryset = queryset.filter(merchant_core=merchant_core)

        return queryset.order_by('-created_at')[:limit]


class CoreMetricsService:
    """
    Core Metrics Management Service
    """

    @staticmethod
    def record_metric(metric_type: str, metric_name: str, metric_value: float,
                     unit: str = 'count', merchant_core: MerchantCore = None,
                     core_service: CoreService = None, tags: Dict = None,
                     metadata: Dict = None):
        """
        Record metric
        """
        metric = CoreMetric.objects.create(
            metric_type=metric_type,
            metric_name=metric_name,
            metric_value=metric_value,
            unit=unit,
            merchant_core=merchant_core,
            core_service=core_service,
            tags=tags or {},
            metadata=metadata or {}
        )

        logger.debug(f"Metric recorded: {metric_name} = {metric_value} {unit}")

        return metric

    @staticmethod
    def get_metrics_summary(metric_name: str = None, metric_type: str = None,
                           merchant_core: MerchantCore = None, hours: int = 24) -> Dict:
        """
        Get metrics summary
        """
        from django.db.models import Avg, Max, Min, Count
        from django.utils import timezone

        queryset = CoreMetric.objects.filter(
            recorded_at__gte=timezone.now() - timezone.timedelta(hours=hours)
        )

        if metric_name:
            queryset = queryset.filter(metric_name=metric_name)

        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)

        if merchant_core:
            queryset = queryset.filter(merchant_core=merchant_core)

        summary = queryset.aggregate(
            avg_value=Avg('metric_value'),
            max_value=Max('metric_value'),
            min_value=Min('metric_value'),
            count=Count('id')
        )

        return summary

    @staticmethod
    def increment_metric(metric_name: str, value: float = 1, source: str = None,
                        merchant_core: MerchantCore = None, core_service: CoreService = None,
                        metadata: Dict = None):
        """
        Increment metric value
        """
        # Get last metric value
        last_metric = CoreMetric.objects.filter(
            metric_name=metric_name,
            merchant_core=merchant_core,
            core_service=core_service
        ).order_by('-recorded_at').first()

        current_value = last_metric.metric_value if last_metric else 0
        new_value = current_value + value

        return CoreMetricsService.record_metric(
            metric_type='usage',
            metric_name=metric_name,
            metric_value=new_value,
            unit='count',
            merchant_core=merchant_core,
            core_service=core_service,
            tags={'source': source} if source else {},
            metadata=metadata or {}
        )

    @staticmethod
    def decrement_metric(metric_name: str, value: float = 1, source: str = None,
                        merchant_core: MerchantCore = None, core_service: CoreService = None,
                        metadata: Dict = None):
        """
        Decrement metric value
        """
        # Get last metric value
        last_metric = CoreMetric.objects.filter(
            metric_name=metric_name,
            merchant_core=merchant_core,
            core_service=core_service
        ).order_by('-recorded_at').first()

        current_value = last_metric.metric_value if last_metric else 0
        new_value = max(0, current_value - value)  # Don't allow negative values

        return CoreMetricsService.record_metric(
            metric_type='usage',
            metric_name=metric_name,
            metric_value=new_value,
            unit='count',
            merchant_core=merchant_core,
            core_service=core_service,
            tags={'source': source} if source else {},
            metadata=metadata or {}
        )