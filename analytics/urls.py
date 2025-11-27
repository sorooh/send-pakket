"""
Analytics App URLs
URL patterns for the analytics app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PerformanceMetricViewSet, CarrierPerformanceViewSet,
    CustomerInsightViewSet, RevenueAnalyticsViewSet,
    APIUsageStatsViewSet
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'performance-metrics', PerformanceMetricViewSet, basename='performance-metrics')
router.register(r'carrier-performance', CarrierPerformanceViewSet, basename='carrier-performance')
router.register(r'customer-insights', CustomerInsightViewSet, basename='customer-insights')
router.register(r'revenue-analytics', RevenueAnalyticsViewSet, basename='revenue-analytics')
router.register(r'api-usage-stats', APIUsageStatsViewSet, basename='api-usage-stats')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]