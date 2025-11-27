"""
Analytics App URLs
URL patterns for the analytics app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PerformanceMetricViewSet, CarrierPerformanceViewSet,
    CustomerInsightViewSet, RevenueAnalyticsViewSet,
    APIUsageStatsViewSet, PredictiveAnalyticsViewSet,
    CustomerSegmentationViewSet, PerformanceOptimizationViewSet
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'performance-metrics', PerformanceMetricViewSet, basename='performance-metrics')
router.register(r'carrier-performance', CarrierPerformanceViewSet, basename='carrier-performance')
router.register(r'customer-insights', CustomerInsightViewSet, basename='customer-insights')
router.register(r'revenue-analytics', RevenueAnalyticsViewSet, basename='revenue-analytics')
router.register(r'api-usage-stats', APIUsageStatsViewSet, basename='api-usage-stats')

# Additional viewsets (not using router for custom actions)
predictive_urls = [
    path('predictive/', PredictiveAnalyticsViewSet.as_view({
        'post': 'predict_delivery_time'
    }), name='predictive-delivery-time'),
    path('predictive/delivery-time/', PredictiveAnalyticsViewSet.as_view({
        'post': 'predict_delivery_time'
    }), name='predictive-delivery-time'),
    path('predictive/churn/', PredictiveAnalyticsViewSet.as_view({
        'post': 'predict_customer_churn'
    }), name='predictive-churn'),
    path('predictive/revenue-forecast/', PredictiveAnalyticsViewSet.as_view({
        'get': 'forecast_revenue'
    }), name='predictive-revenue-forecast'),
    path('predictive/carrier-optimization/', PredictiveAnalyticsViewSet.as_view({
        'post': 'optimize_carrier_selection'
    }), name='predictive-carrier-optimization'),
]

segmentation_urls = [
    path('segmentation/', CustomerSegmentationViewSet.as_view({
        'get': 'segments'
    }), name='customer-segments'),
    path('segmentation/<int:pk>/recommendations/', CustomerSegmentationViewSet.as_view({
        'get': 'personalized_recommendations'
    }), name='personalized-recommendations'),
]

optimization_urls = [
    path('optimization/bottlenecks/', PerformanceOptimizationViewSet.as_view({
        'get': 'bottlenecks'
    }), name='performance-bottlenecks'),
    path('optimization/recommendations/', PerformanceOptimizationViewSet.as_view({
        'get': 'optimization_recommendations'
    }), name='optimization-recommendations'),
]

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
] + predictive_urls + segmentation_urls + optimization_urls