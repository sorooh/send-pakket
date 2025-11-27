"""
Core app signals
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Company


@receiver(post_save, sender=Company)
def company_saved(sender, instance, created, **kwargs):
    """
    Signal to handle company creation/update
    """
    if created and not instance.merchant_core:
        # Create merchant core for new company
        from platform_core.services import MerchantCoreService
        # Create merchant core with company data
        merchant_data = {
            'merchant_id': f"company_{instance.id}",
            'name': f"{instance.name} Core",
            'business_type': 'ecommerce',  # Default business type
            'settings': {
                'industry': getattr(instance, 'industry', ''),
                'employee_count': getattr(instance, 'employee_count', 0),
                'annual_revenue': str(getattr(instance, 'annual_revenue', 0))
            }
        }
        merchant_core = MerchantCoreService.create_merchant_core(merchant_data)
        # Update the company instance directly in the database to avoid recursion
        Company.objects.filter(id=instance.id).update(merchant_core=merchant_core)
        # Refresh the instance to reflect the database changes
        instance.refresh_from_db()