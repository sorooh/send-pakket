"""
Shipping API URLs - Send-Pakket Platform
"""

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

# Create a router for the shipping API
router = DefaultRouter()
router.register(r'shipments', views.ShipmentViewSet, basename='shipment')
router.register(r'tracking-events', views.TrackingEventViewSet, basename='tracking-event')
router.register(r'shipment-documents', views.ShipmentDocumentViewSet, basename='shipment-document')
router.register(r'shipment-rates', views.ShipmentRateViewSet, basename='shipment-rate')

urlpatterns = [
    path('', include(router.urls)),
]