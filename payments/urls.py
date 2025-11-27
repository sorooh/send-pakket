"""
Payment API URLs for Send-Pakket Platform
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionViewSet, InvoiceViewSet, InvoiceItemViewSet,
    PaymentViewSet, UsageRecordViewSet, ShipmentTransactionViewSet
)
from .webhooks import stripe_webhook

# Create a router for the payment APIs
router = DefaultRouter()

# Register viewsets
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-items', InvoiceItemViewSet, basename='invoice-item')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'usage-records', UsageRecordViewSet, basename='usage-record')
router.register(r'shipment-transactions', ShipmentTransactionViewSet, basename='shipment-transaction')

# URL patterns
urlpatterns = [
    path('webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
] + router.urls