"""
Central Core Signals
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PlatformCore, MerchantCore, CoreEvent, CoreMetric
from .services import CoreEventService, CoreMetricsService

# Variable to prevent signal recursion
_signal_lock = False


@receiver(post_save, sender=PlatformCore)
def platform_core_saved(sender, instance, created, **kwargs):
    """
    Signal when platform core is saved
    """
    global _signal_lock
    if _signal_lock:
        return

    _signal_lock = True
    try:
        event_type = 'platform_core_created' if created else 'platform_core_updated'
        description = f"Platform Core {'created' if created else 'updated'}: {instance.platform_name}"

        CoreEventService.log_event(
            event_type=event_type,
            level='info',
            title=f"Platform Core {'Created' if created else 'Updated'}",
            description=description,
            merchant_core=None,
            core_service=None,
            metadata={
                'platform_core_id': str(instance.id),
                'platform_name': instance.platform_name,
                'platform_version': instance.platform_version,
                'system_status': instance.system_status
            },
            source_ip=None,
            user_agent=None
        )
    finally:
        _signal_lock = False


@receiver(post_save, sender=MerchantCore)
def merchant_core_saved(sender, instance, created, **kwargs):
    """
    Signal when merchant core is saved
    """
    global _signal_lock
    if _signal_lock:
        return

    _signal_lock = True
    try:
        event_type = 'merchant_core_created' if created else 'merchant_core_updated'
        description = f"Merchant Core {'created' if created else 'updated'}: {instance.name}"

        CoreEventService.log_event(
            event_type=event_type,
            level='info',
            title=f"Merchant Core {'Created' if created else 'Updated'}",
            description=description,
            merchant_core=instance,
            core_service=None,
            metadata={
                'merchant_core_id': str(instance.id),
                'merchant_name': instance.name,
                'platform_core_id': str(instance.platform_core.id) if instance.platform_core else None,
                'status': instance.status
            },
            source_ip=None,
            user_agent=None
        )

        # Update metrics
        if created:
            CoreMetricsService.increment_metric(
                metric_name='total_merchants',
                value=1,
                source='merchant_core',
                metadata={'merchant_core_id': str(instance.id)}
            )
    finally:
        _signal_lock = False


@receiver(post_delete, sender=MerchantCore)
def merchant_core_deleted(sender, instance, **kwargs):
    """
    Signal when merchant core is deleted
    """
    global _signal_lock
    if _signal_lock:
        return

    _signal_lock = True
    try:
        CoreEventService.log_event(
            event_type='merchant_core_deleted',
            level='warning',
            title="Merchant Core Deleted",
            description=f"Merchant Core deleted: {instance.name}",
            merchant_core=None,  # Cannot access object after deletion
            core_service=None,
            metadata={
                'merchant_core_id': str(instance.id),
                'merchant_name': instance.name,
                'platform_core_id': str(instance.platform_core.id) if instance.platform_core else None
            },
            source_ip=None,
            user_agent=None
        )

        # Update metrics
        CoreMetricsService.decrement_metric(
            metric_name='total_merchants',
            value=1,
            source='merchant_core',
            metadata={'merchant_core_id': str(instance.id)}
        )
    finally:
        _signal_lock = False


@receiver(post_save, sender=CoreEvent)
def core_event_saved(sender, instance, created, **kwargs):
    """
    Signal when core event is saved
    """
    global _signal_lock
    if _signal_lock or not created:
        return

    _signal_lock = True
    try:
        # Update event metrics
        CoreMetricsService.increment_metric(
            metric_name='total_events',
            value=1,
            source='core_event',
            metadata={
                'event_type': instance.event_type,
                'level': instance.level
            }
        )
    finally:
        _signal_lock = False


@receiver(post_save, sender=CoreMetric)
def core_metric_saved(sender, instance, created, **kwargs):
    """
    Signal when core metric is saved
    """
    global _signal_lock
    if _signal_lock or not created:
        return

    _signal_lock = True
    try:
        CoreEventService.log_event(
            event_type='metric_recorded',
            level='info',
            title="Core Metric Recorded",
            description=f"Core metric recorded: {instance.metric_name}",
            merchant_core=None,
            core_service=None,
            metadata={
                'metric_name': instance.metric_name,
                'value': float(instance.metric_value),
                'source': instance.tags.get('source', 'unknown') if instance.tags else 'unknown'
            },
            source_ip=None,
            user_agent=None
        )
    finally:
        _signal_lock = False