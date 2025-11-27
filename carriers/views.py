"""
Carrier views for Send-Pakket Platform
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet
from django.db.models import Q, Count
from decimal import Decimal
from django.utils import timezone
from .models import Carrier, CarrierService, CarrierCredentials, CarrierPricing, CarrierWebhook
from .serializers import (
    CarrierSerializer, CarrierListSerializer, CarrierServiceSerializer,
    CarrierServiceListSerializer, CarrierCredentialsSerializer,
    CarrierPricingSerializer, CarrierWebhookSerializer
)


class CarrierViewSet(viewsets.ModelViewSet):
    """ViewSet for carrier management"""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'is_featured', 'international_shipping']

    def get_queryset(self):
        """Filter carriers by user's company"""
        return Carrier.objects.all()

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CarrierListSerializer
        return CarrierSerializer

    @action(detail=True, methods=['get'])
    def services(self, request, pk=None):
        """Get all services for a specific carrier"""
        carrier = self.get_object()
        services = carrier.services.filter(is_active=True)
        serializer = CarrierServiceSerializer(services, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured carriers"""
        carriers = self.get_queryset().filter(is_featured=True, is_active=True)
        serializer = CarrierListSerializer(carriers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_country(self, request):
        """Get carriers serving specific countries"""
        countries = request.query_params.getlist('country')
        if not countries:
            return Response({'error': 'Country parameter required'}, status=400)

        carriers = self.get_queryset().filter(
            Q(countries_served__overlap=countries) | Q(international_shipping=True),
            is_active=True
        ).distinct()
        serializer = CarrierListSerializer(carriers, many=True)
        return Response(serializer.data)


class CarrierServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for carrier service management"""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['carrier', 'service_type', 'is_active', 'is_featured',
                       'domestic_only', 'international_only']

    def get_queryset(self):
        """Filter services by user's company if needed"""
        return CarrierService.objects.select_related('carrier').all()

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CarrierServiceListSerializer
        return CarrierServiceSerializer

    @action(detail=False, methods=['get'])
    def by_carrier(self, request):
        """Get services grouped by carrier"""
        carrier_id = request.query_params.get('carrier_id')
        if not carrier_id:
            return Response({'error': 'carrier_id parameter required'}, status=400)

        services = self.get_queryset().filter(carrier_id=carrier_id, is_active=True)
        serializer = CarrierServiceSerializer(services, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def available_for_shipment(self, request):
        """Get services available for a specific shipment criteria"""
        # This would be expanded with actual shipment logic
        origin_country = request.query_params.get('origin_country')
        destination_country = request.query_params.get('destination_country')
        weight_kg = request.query_params.get('weight_kg', 0)

        queryset = self.get_queryset().filter(is_active=True)

        if origin_country and destination_country:
            if origin_country == destination_country:
                # Domestic shipping
                queryset = queryset.filter(
                    Q(domestic_only=True) | Q(international_only=False)
                ).exclude(international_only=True)
            else:
                # International shipping
                queryset = queryset.filter(
                    Q(international_only=True) | Q(domestic_only=False)
                ).exclude(domestic_only=True)

                # Filter by country availability
                queryset = queryset.filter(
                    Q(countries_available__contains=[destination_country]) |
                    Q(countries_available__len=0)  # No restrictions
                ).exclude(countries_excluded__contains=[destination_country])

        # Filter by weight limits
        if weight_kg:
            queryset = queryset.filter(
                Q(max_weight_kg__isnull=True) | Q(max_weight_kg__gte=weight_kg)
            )

        serializer = CarrierServiceListSerializer(queryset, many=True)
        return Response(serializer.data)


class CarrierCredentialsViewSet(viewsets.ModelViewSet):
    """ViewSet for carrier credentials management"""

    serializer_class = CarrierCredentialsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['carrier', 'is_active', 'is_verified']

    def get_queryset(self):
        """Filter credentials by user's company"""
        return CarrierCredentials.objects.filter(
            company=self.request.user.company
        ).select_related('carrier', 'company')

    def perform_create(self, serializer):
        """Set company when creating credentials"""
        serializer.save(company=self.request.user.company)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify carrier credentials"""
        credentials = self.get_object()

        # Here you would implement actual API verification logic
        # For now, we'll just mark as verified
        credentials.is_verified = True
        credentials.last_verified_at = timezone.now()
        credentials.verification_error = ''
        credentials.save()

        serializer = self.get_serializer(credentials)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test connection to carrier API"""
        credentials = self.get_object()

        # Here you would implement actual API connection test
        # For now, return success
        return Response({'status': 'success', 'message': 'Connection test successful'})


class CarrierPricingViewSet(viewsets.ModelViewSet):
    """ViewSet for carrier pricing management"""

    serializer_class = CarrierPricingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['carrier_service', 'origin_country', 'destination_country',
                       'currency', 'is_active']

    def get_queryset(self):
        """Return all pricing rules (admin functionality)"""
        return CarrierPricing.objects.select_related(
            'carrier_service__carrier'
        ).filter(is_active=True)

    @action(detail=False, methods=['get'])
    def calculate_rate(self, request):
        """Calculate shipping rate based on parameters"""
        carrier_service_id = request.query_params.get('carrier_service_id')
        origin_country = request.query_params.get('origin_country')
        destination_country = request.query_params.get('destination_country')
        weight_kg = request.query_params.get('weight_kg')

        if not all([carrier_service_id, origin_country, destination_country, weight_kg]):
            return Response({
                'error': 'carrier_service_id, origin_country, destination_country, and weight_kg are required'
            }, status=400)

        try:
            weight_kg = float(weight_kg)
        except ValueError:
            return Response({'error': 'Invalid weight_kg value'}, status=400)

        # Find applicable pricing rule
        pricing_rule = CarrierPricing.objects.filter(
            carrier_service_id=carrier_service_id,
            origin_country=origin_country,
            destination_country=destination_country,
            weight_from_kg__lte=weight_kg,
            is_active=True
        ).filter(
            Q(weight_to_kg__isnull=True) | Q(weight_to_kg__gte=weight_kg)
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=timezone.now())
        ).first()

        if not pricing_rule:
            return Response({'error': 'No pricing rule found for given criteria'}, status=404)

        # Calculate rate
        base_price = pricing_rule.base_price
        weight_from_kg = Decimal(str(pricing_rule.weight_from_kg))
        price_per_kg = pricing_rule.price_per_kg
        weight_price = (Decimal(str(weight_kg)) - weight_from_kg) * price_per_kg
        fuel_surcharge = (base_price + weight_price) * (pricing_rule.fuel_surcharge_percent / 100)
        total_price = base_price + weight_price + fuel_surcharge + pricing_rule.remote_area_surcharge + pricing_rule.oversized_surcharge

        return Response({
            'carrier_service_id': carrier_service_id,
            'origin_country': origin_country,
            'destination_country': destination_country,
            'weight_kg': weight_kg,
            'base_price': base_price,
            'weight_price': weight_price,
            'fuel_surcharge': fuel_surcharge,
            'remote_area_surcharge': pricing_rule.remote_area_surcharge,
            'oversized_surcharge': pricing_rule.oversized_surcharge,
            'total_price': total_price,
            'currency': pricing_rule.currency
        })


class CarrierWebhookViewSet(viewsets.ModelViewSet):
    """ViewSet for carrier webhook management"""

    serializer_class = CarrierWebhookSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['carrier', 'is_active']

    def get_queryset(self):
        """Filter webhooks by user's company"""
        return CarrierWebhook.objects.filter(
            company=self.request.user.company
        ).select_related('carrier', 'company')

    def perform_create(self, serializer):
        """Set company when creating webhook"""
        serializer.save(company=self.request.user.company)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test webhook by sending a test payload"""
        webhook = self.get_object()

        # Here you would implement actual webhook testing
        # For now, return success
        return Response({'status': 'success', 'message': 'Webhook test sent'})
