"""
URL configuration for sendpakket project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

def health_check(request):
    """Health check endpoint for load balancers and monitoring."""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': '2025-11-27T22:30:00Z',
        'service': 'send-pakket-platform'
    })

urlpatterns = [
    path('admin/', admin.site.urls),

    # Health check endpoint
    path('health/', health_check, name='health_check'),

    # JWT Authentication endpoints
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Core API
    path('', include('core.urls')),

    # Shipping API
    path('api/shipping/', include('shipping.urls')),

    # Carriers API
    path('api/carriers/', include('carriers.urls')),

    # Payments API
    path('api/payments/', include('payments.urls')),

    # Platform Core API
    path('api/', include('platform_core.urls')),

    # Other apps will be added here
    # path('api/analytics/', include('analytics.urls')),
]
