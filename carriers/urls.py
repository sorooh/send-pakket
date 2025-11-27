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

# URL patterns
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]