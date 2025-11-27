"""
ViewSets for the central core
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache

from core.permissions import IsCompanyMember, IsCompanyAdmin
from .models import (
    PlatformCore, MerchantCore, CoreService,
    MerchantService, CoreConfiguration, CoreEvent, CoreMetric
)
from .serializers import (
    PlatformCoreSerializer, MerchantCoreSerializer, CoreServiceSerializer,
    MerchantServiceSerializer, CoreConfigurationSerializer, CoreEventSerializer,
    CoreMetricSerializer, MerchantCoreCreateSerializer, MerchantCoreUpdateSerializer,
    CoreConfigurationUpdateSerializer, PlatformStatsSerializer, MerchantLimitsSerializer
)
from .services import (
    PlatformCoreService, MerchantCoreService, CoreServiceManager,
    CoreConfigurationService, CoreEventService, CoreMetricsService
)


class PlatformCoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for the central platform core
    """
    queryset = PlatformCore.objects.all()
    serializer_class = PlatformCoreSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    http_method_names = ['get', 'put', 'patch']

    def get_queryset(self):
        """Get the central core (single instance only)"""
        return PlatformCore.objects.all()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get platform statistics"""
        platform_core = PlatformCoreService.get_platform_core()

        # Calculate additional statistics
        active_merchants = MerchantCore.objects.filter(status='active').count()

        # Calculate uptime percentage (simplified)
        uptime_percentage = 99.9  # Can be improved later

        stats_data = {
            'total_merchants': platform_core.total_merchants,
            'total_shipments': platform_core.total_shipments,
            'total_revenue': platform_core.total_revenue,
            'active_merchants': active_merchants,
            'system_status': platform_core.system_status,
            'uptime_percentage': uptime_percentage
        }

        serializer = PlatformStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def maintenance_mode(self, request):
        """Enable/disable maintenance mode"""
        enabled = request.data.get('enabled', False)
        message = request.data.get('message', '')

        PlatformCoreService.set_maintenance_mode(enabled, message)

        return Response({
            'message': f'Maintenance mode {"enabled" if enabled else "disabled"}',
            'enabled': enabled,
            'message': message
        })

    @action(detail=False, methods=['post'])
    def update_stats(self, request):
        """Update platform statistics"""
        PlatformCoreService.update_platform_stats()

        platform_core = PlatformCoreService.get_platform_core()
        serializer = self.get_serializer(platform_core)

        return Response({
            'message': 'Platform statistics updated successfully',
            'data': serializer.data
        })


class MerchantCoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for merchant cores
    """
    queryset = MerchantCore.objects.all()
    serializer_class = MerchantCoreSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'business_type', 'platform_core']
    search_fields = ['merchant_id', 'name']
    ordering_fields = ['created_at', 'name', 'total_shipments']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return MerchantCoreCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MerchantCoreUpdateSerializer
        return MerchantCoreSerializer

    def get_queryset(self):
        """Filter merchant cores by company"""
        queryset = super().get_queryset()

        # Filter by company if not a general admin
        if not self.request.user.is_superuser:
            # Get merchant core associated with user's company
            if hasattr(self.request.user, 'company') and self.request.user.company:
                merchant_core = self.request.user.company.merchant_core
                if merchant_core:
                    queryset = queryset.filter(id=merchant_core.id)
                else:
                    # If no merchant core exists, return empty queryset
                    queryset = queryset.none()

        return queryset

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate merchant"""
        merchant_core = self.get_object()

        if merchant_core.status == 'active':
            return Response(
                {'error': 'Merchant is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        MerchantCoreService.activate_merchant(
            merchant_core,
            activated_by=request.user.username
        )

        serializer = self.get_serializer(merchant_core)
        return Response({
            'message': 'Merchant activated successfully',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend merchant"""
        merchant_core = self.get_object()
        reason = request.data.get('reason', '')

        if merchant_core.status == 'suspended':
            return Response(
                {'error': 'Merchant is already suspended'},
                status=status.HTTP_400_BAD_REQUEST
            )

        MerchantCoreService.suspend_merchant(
            merchant_core,
            reason=reason,
            suspended_by=request.user.username
        )

        serializer = self.get_serializer(merchant_core)
        return Response({
            'message': 'Merchant suspended successfully',
            'data': serializer.data
        })

    @action(detail=True, methods=['get'])
    def limits(self, request, pk=None):
        """Check merchant limits"""
        merchant_core = self.get_object()

        limits_status = MerchantCoreService.check_merchant_limits(merchant_core)

        limits_data = {
            'can_create_shipment': limits_status['can_create_shipment'],
            'within_shipment_limit': limits_status['within_shipment_limit'],
            'is_active': limits_status['is_active'],
            'current_shipments': merchant_core.active_shipments,
            'max_shipments': merchant_core.monthly_shipment_limit,
            'api_rate_limit': merchant_core.api_rate_limit,
            'storage_limit_mb': merchant_core.storage_limit_mb
        }

        serializer = MerchantLimitsSerializer(limits_data)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_stats(self, request, pk=None):
        """Update merchant statistics"""
        merchant_core = self.get_object()

        MerchantCoreService.update_merchant_stats(merchant_core)

        serializer = self.get_serializer(merchant_core)
        return Response({
            'message': 'Merchant statistics updated successfully',
            'data': serializer.data
        })


class CoreServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for central core services
    """
    queryset = CoreService.objects.all()
    serializer_class = CoreServiceSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['service_type', 'status']
    search_fields = ['service_name', 'display_name']
    ordering_fields = ['service_name', 'created_at']
    ordering = ['service_name']

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available services"""
        services = CoreServiceManager.get_available_services()
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_usage(self, request, pk=None):
        """Update service usage"""
        service = self.get_object()
        merchant_id = request.data.get('merchant_id')

        merchant_core = None
        if merchant_id:
            try:
                merchant_core = MerchantCore.objects.get(merchant_id=merchant_id)
            except MerchantCore.DoesNotExist:
                return Response(
                    {'error': 'Merchant not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Check limits before updating
        if not CoreServiceManager.check_service_limits(service, merchant_core):
            return Response(
                {'error': 'Service limits exceeded'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        CoreServiceManager.update_service_usage(service, merchant_core)

        serializer = self.get_serializer(service)
        return Response({
            'message': 'Service usage updated successfully',
            'data': serializer.data
        })


class MerchantServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for merchant services
    """
    queryset = MerchantService.objects.all()
    serializer_class = MerchantServiceSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_enabled', 'merchant_core', 'core_service']
    ordering_fields = ['created_at', 'usage_count']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter merchant services"""
        queryset = super().get_queryset()

        # Filter by merchant
        merchant_id = self.request.query_params.get('merchant_id')
        if merchant_id:
            queryset = queryset.filter(merchant_core__merchant_id=merchant_id)

        return queryset

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Enable/disable service for merchant"""
        merchant_service = self.get_object()

        merchant_service.is_enabled = not merchant_service.is_enabled
        merchant_service.save()

        # Log event
        CoreEventService.log_event(
            event_type='service',
            level='info',
            title=f'Service {"Enabled" if merchant_service.is_enabled else "Disabled"}',
            description=f'Service {merchant_service.core_service.display_name} {"enabled" if merchant_service.is_enabled else "disabled"} for merchant {merchant_service.merchant_core.name}',
            merchant_core=merchant_service.merchant_core,
            core_service=merchant_service.core_service,
            metadata={'enabled': merchant_service.is_enabled}
        )

        serializer = self.get_serializer(merchant_service)
        return Response({
            'message': f'Service {"enabled" if merchant_service.is_enabled else "disabled"} successfully',
            'data': serializer.data
        })


class CoreConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for core configurations
    """
    queryset = CoreConfiguration.objects.all()
    serializer_class = CoreConfigurationSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['scope', 'is_editable', 'merchant_core', 'core_service']
    search_fields = ['config_key', 'description']
    ordering_fields = ['config_key', 'scope', 'created_at']
    ordering = ['scope', 'config_key']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return CoreConfigurationUpdateSerializer
        return CoreConfigurationSerializer

    def get_queryset(self):
        """Filter configurations by scope and merchant"""
        queryset = super().get_queryset()

        # Filter by merchant if not a general admin
        if not self.request.user.is_superuser:
            if hasattr(self.request.user, 'company') and self.request.user.company:
                merchant_core = self.request.user.company.merchant_core
                if merchant_core:
                    # Show global configs and merchant-specific configs
                    queryset = queryset.filter(
                        Q(merchant_core=merchant_core) | Q(scope='global')
                    )
                else:
                    # If no merchant core exists, only show global configs
                    queryset = queryset.filter(scope='global')

        return queryset

    @action(detail=False, methods=['get'])
    def get_value(self, request):
        """Get specific configuration value"""
        config_key = request.query_params.get('key')
        scope = request.data.get('scope', 'global')
        merchant_id = request.query_params.get('merchant_id')
        service_name = request.query_params.get('service_name')

        if not config_key:
            return Response(
                {'error': 'Config key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        merchant_core = None
        if merchant_id:
            try:
                merchant_core = MerchantCore.objects.get(merchant_id=merchant_id)
            except MerchantCore.DoesNotExist:
                return Response(
                    {'error': 'Merchant not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        core_service = None
        if service_name:
            core_service = CoreServiceManager.get_service_by_name(service_name)
            if not core_service:
                return Response(
                    {'error': 'Service not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        value = CoreConfigurationService.get_config_value(
            config_key, scope, merchant_core, core_service
        )

        if value is None:
            return Response(
                {'error': 'Configuration not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'config_key': config_key,
            'scope': scope,
            'value': value
        })

    @action(detail=False, methods=['post'])
    def set_value(self, request):
        """Set configuration value"""
        config_key = request.data.get('key')
        config_value = request.data.get('value')
        scope = request.data.get('scope', 'global')
        description = request.data.get('description', '')
        merchant_id = request.data.get('merchant_id')
        service_name = request.data.get('service_name')

        if not config_key or config_value is None:
            return Response(
                {'error': 'Config key and value are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        merchant_core = None
        if merchant_id:
            try:
                merchant_core = MerchantCore.objects.get(merchant_id=merchant_id)
            except MerchantCore.DoesNotExist:
                return Response(
                    {'error': 'Merchant not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        core_service = None
        if service_name:
            core_service = CoreServiceManager.get_service_by_name(service_name)
            if not core_service:
                return Response(
                    {'error': 'Service not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        CoreConfigurationService.set_config_value(
            config_key, config_value, scope, merchant_core, core_service, description
        )

        return Response({
            'message': 'Configuration updated successfully',
            'config_key': config_key,
            'scope': scope,
            'value': config_value
        })


class CoreEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for core events (read-only)
    """
    queryset = CoreEvent.objects.all()
    serializer_class = CoreEventSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'level', 'merchant_core', 'core_service']
    ordering_fields = ['created_at', 'level', 'event_type']
    ordering = ['-created_at']
    pagination_class = None  # Remove pagination for events

    def get_queryset(self):
        """Filter events by merchant"""
        queryset = super().get_queryset()

        # Filter by merchant if not a general admin
        if not self.request.user.is_superuser:
            if hasattr(self.request.user, 'company') and self.request.user.company:
                merchant_core = self.request.user.company.merchant_core
                if merchant_core:
                    queryset = queryset.filter(merchant_core=merchant_core)
                else:
                    # If no merchant core exists, return empty queryset
                    queryset = queryset.none()

        # Filter by merchant if specified in query params (for admins)
        merchant_id = self.request.query_params.get('merchant_id')
        if merchant_id and self.request.user.is_superuser:
            queryset = queryset.filter(merchant_core__merchant_id=merchant_id)

        # Filter by time period
        hours = self.request.query_params.get('hours')
        if hours:
            try:
                hours = int(hours)
                queryset = queryset.filter(
                    created_at__gte=timezone.now() - timezone.timedelta(hours=hours)
                )
            except ValueError:
                pass

        return queryset[:100]  # Max 100 events


class CoreMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for core metrics (read-only)
    """
    queryset = CoreMetric.objects.all()
    serializer_class = CoreMetricSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['metric_type', 'merchant_core', 'core_service']
    search_fields = ['metric_name']
    ordering_fields = ['recorded_at', 'metric_value']
    ordering = ['-recorded_at']

    def get_queryset(self):
        """Filter metrics by merchant"""
        queryset = super().get_queryset()

        # Filter by merchant if not a general admin
        if not self.request.user.is_superuser:
            if hasattr(self.request.user, 'company') and self.request.user.company:
                merchant_core = self.request.user.company.merchant_core
                if merchant_core:
                    queryset = queryset.filter(merchant_core=merchant_core)
                else:
                    # If no merchant core exists, return empty queryset
                    queryset = queryset.none()

        # Filter by merchant if specified in query params (for admins)
        merchant_id = self.request.query_params.get('merchant_id')
        if merchant_id and self.request.user.is_superuser:
            queryset = queryset.filter(merchant_core__merchant_id=merchant_id)

        # Filter by time period
        hours = self.request.query_params.get('hours', 24)
        try:
            hours = int(hours)
            queryset = queryset.filter(
                recorded_at__gte=timezone.now() - timezone.timedelta(hours=hours)
            )
        except ValueError:
            pass

        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get metrics summary"""
        metric_name = request.query_params.get('metric_name')
        metric_type = request.query_params.get('metric_type')
        merchant_id = request.query_params.get('merchant_id')
        hours = request.query_params.get('hours', 24)

        merchant_core = None
        if merchant_id:
            try:
                merchant_core = MerchantCore.objects.get(merchant_id=merchant_id)
            except MerchantCore.DoesNotExist:
                return Response(
                    {'error': 'Merchant not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        try:
            hours = int(hours)
        except ValueError:
            hours = 24

        summary = CoreMetricsService.get_metrics_summary(
            metric_name=metric_name,
            metric_type=metric_type,
            merchant_core=merchant_core,
            hours=hours
        )

        return Response({
            'summary': summary,
            'filters': {
                'metric_name': metric_name,
                'metric_type': metric_type,
                'merchant_id': merchant_id,
                'hours': hours
            }
        })
