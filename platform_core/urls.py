"""
URLs for the central core
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlatformCoreViewSet, MerchantCoreViewSet, CoreServiceViewSet,
    MerchantServiceViewSet, CoreConfigurationViewSet, CoreEventViewSet,
    CoreMetricViewSet
)

# Create Router for APIs
router = DefaultRouter()

# Register ViewSets
router.register(r'platform-core', PlatformCoreViewSet, basename='platform-core')
router.register(r'merchant-cores', MerchantCoreViewSet, basename='merchant-cores')
router.register(r'core-services', CoreServiceViewSet, basename='core-services')
router.register(r'merchant-services', MerchantServiceViewSet, basename='merchant-services')
router.register(r'core-configurations', CoreConfigurationViewSet, basename='core-configurations')
router.register(r'core-events', CoreEventViewSet, basename='core-events')
router.register(r'core-metrics', CoreMetricViewSet, basename='core-metrics')

# Additional URL patterns
urlpatterns = [
    # Include automatic URLs from Router
    path('', include(router.urls)),

    # Additional URLs for special operations
    path('platform-core/stats/', PlatformCoreViewSet.as_view({'get': 'stats'}), name='platform-core-stats'),
    path('platform-core/maintenance-mode/', PlatformCoreViewSet.as_view({'post': 'maintenance_mode'}), name='platform-core-maintenance'),
    path('platform-core/update-stats/', PlatformCoreViewSet.as_view({'post': 'update_stats'}), name='platform-core-update-stats'),

    # URLs for merchants
    path('merchant-cores/<uuid:pk>/activate/', MerchantCoreViewSet.as_view({'post': 'activate'}), name='merchant-core-activate'),
    path('merchant-cores/<uuid:pk>/suspend/', MerchantCoreViewSet.as_view({'post': 'suspend'}), name='merchant-core-suspend'),
    path('merchant-cores/<uuid:pk>/limits/', MerchantCoreViewSet.as_view({'get': 'limits'}), name='merchant-core-limits'),
    path('merchant-cores/<uuid:pk>/update-stats/', MerchantCoreViewSet.as_view({'post': 'update_stats'}), name='merchant-core-update-stats'),

    # URLs for services
    path('core-services/available/', CoreServiceViewSet.as_view({'get': 'available'}), name='core-services-available'),
    path('core-services/<uuid:pk>/update-usage/', CoreServiceViewSet.as_view({'post': 'update_usage'}), name='core-service-update-usage'),

    # URLs for merchant services
    path('merchant-services/<uuid:pk>/toggle/', MerchantServiceViewSet.as_view({'post': 'toggle'}), name='merchant-service-toggle'),

    # URLs for configurations
    path('configurations/get-value/', CoreConfigurationViewSet.as_view({'get': 'get_value'}), name='core-configurations-get-value'),
    path('configurations/set-value/', CoreConfigurationViewSet.as_view({'post': 'set_value'}), name='core-configurations-set-value'),

    # URLs for metrics
    path('core-metrics/summary/', CoreMetricViewSet.as_view({'get': 'summary'}), name='core-metrics-summary'),
]