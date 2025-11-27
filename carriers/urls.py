"""
Carrier URLs for Send-Pakket Platform
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for the carriers app
router = DefaultRouter()
router.register(r'carriers', views.CarrierViewSet, basename='carrier')
router.register(r'services', views.CarrierServiceViewSet, basename='carrier-service')
router.register(r'credentials', views.CarrierCredentialsViewSet, basename='carrier-credentials')
router.register(r'pricing', views.CarrierPricingViewSet, basename='carrier-pricing')
router.register(r'webhooks', views.CarrierWebhookViewSet, basename='carrier-webhook')

# Additional URL patterns for analytics and optimization
analytics_patterns = [
    path('analytics/<int:pk>/performance/', views.CarrierAnalyticsViewSet.as_view({'get': 'performance'}), name='carrier-analytics-performance'),
    path('analytics/compare/', views.CarrierAnalyticsViewSet.as_view({'get': 'compare'}), name='carrier-analytics-compare'),
]

optimization_patterns = [
    path('optimization/rates/', views.CarrierOptimizationViewSet.as_view({'post': 'get_rates'}), name='carrier-optimization-rates'),
    path('optimization/select/', views.CarrierOptimizationViewSet.as_view({'post': 'optimize_selection'}), name='carrier-optimization-select'),
    path('optimization/bulk/', views.CarrierOptimizationViewSet.as_view({'post': 'bulk_rate_calculation'}), name='carrier-optimization-bulk'),
]

# URL patterns
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    # Analytics endpoints
    path('', include(analytics_patterns)),
    # Optimization endpoints
    path('', include(optimization_patterns)),
]