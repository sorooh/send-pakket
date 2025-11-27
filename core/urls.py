"""
Core API URLs - Send-Pakket Platform
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register(r'addresses', views.AddressViewSet, basename='address')
router.register(r'api-keys', views.APIKeyViewSet, basename='apikey')
router.register(r'activity-logs', views.ActivityLogViewSet, basename='activitylog')

# URL patterns
urlpatterns = [
    path('api/', include(router.urls)),
]