"""
Shipping API Views - Send-Pakket Platform
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from .models import Shipment, TrackingEvent, ShipmentItem, ShipmentDocument, ShipmentRate
from .serializers import (
    ShipmentSerializer, ShipmentCreateSerializer, TrackingEventSerializer,
    ShipmentDocumentSerializer, ShipmentRateSerializer, ShipmentRateCreateSerializer,
    TrackingUpdateSerializer
)


class ShipmentViewSet(viewsets.ModelViewSet):
    """Shipment management viewset"""

    permission_classes = [IsAuthenticated]
    serializer_class = ShipmentSerializer

    def get_queryset(self):
        """Filter shipments by user's company"""
        user = self.request.user
        if hasattr(user, 'company'):
            return Shipment.objects.filter(company=user.company)
        return Shipment.objects.none()

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ShipmentCreateSerializer
        return ShipmentSerializer

    def perform_create(self, serializer):
        """Set company when creating shipment"""
        user = self.request.user
        if hasattr(user, 'company'):
            serializer.save(company=user.company)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """Mark shipment as shipped"""
        shipment = self.get_object()

        if shipment.status != 'label_created':
            return Response(
                {'error': 'Shipment must be in label_created status to ship'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shipment.status = 'shipped'
        shipment.shipped_at = timezone.now()
        shipment.save()

        serializer = self.get_serializer(shipment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """Mark shipment as delivered"""
        shipment = self.get_object()

        if shipment.status not in ['shipped', 'in_transit', 'out_for_delivery']:
            return Response(
                {'error': 'Shipment must be in shipped, in_transit, or out_for_delivery status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shipment.status = 'delivered'
        shipment.delivered_at = timezone.now()
        shipment.save()

        serializer = self.get_serializer(shipment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel shipment"""
        shipment = self.get_object()

        if shipment.status in ['delivered', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel delivered or already cancelled shipment'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shipment.status = 'cancelled'
        shipment.save()

        serializer = self.get_serializer(shipment)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """Get shipment tracking information"""
        shipment = self.get_object()
        tracking_events = shipment.tracking_events.order_by('-event_timestamp')

        serializer = TrackingEventSerializer(tracking_events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_tracking(self, request, pk=None):
        """Update shipment tracking information"""
        shipment = self.get_object()
        serializer = TrackingUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tracking_number = serializer.validated_data['tracking_number']
        carrier_events = serializer.validated_data.get('carrier_events', [])

        # Update tracking number if provided
        if tracking_number:
            shipment.tracking_number = tracking_number
            shipment.save()

        # Create tracking events
        for event_data in carrier_events:
            TrackingEvent.objects.create(
                shipment=shipment,
                event_code=event_data['event_code'],
                event_description=event_data['event_description'],
                location=event_data.get('location'),
                event_timestamp=event_data['event_timestamp'],
                carrier_event_id=event_data.get('carrier_event_id'),
                carrier_raw_data=event_data.get('carrier_raw_data')
            )

        return Response({'message': 'Tracking updated successfully'})

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get shipment documents"""
        shipment = self.get_object()
        documents = shipment.documents.all()

        serializer = ShipmentDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def generate_label(self, request, pk=None):
        """Generate shipping label"""
        shipment = self.get_object()

        if shipment.status != 'created':
            return Response(
                {'error': 'Label can only be generated for created shipments'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Integrate with carrier API to generate label
        # For now, just update status
        shipment.status = 'label_created'
        shipment.save()

        return Response({'message': 'Label generation initiated'})

    @action(detail=False, methods=['post'])
    def get_rates(self, request):
        """Get shipping rates for a shipment"""
        serializer = ShipmentRateCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # TODO: Integrate with carrier APIs to get rates
        # For now, return mock rates
        mock_rates = [
            {
                'carrier': 'DHL',
                'service': 'Express',
                'cost_price': 25.50,
                'selling_price': 32.00,
                'currency': 'EUR',
                'estimated_delivery_days': 1
            },
            {
                'carrier': 'UPS',
                'service': 'Standard',
                'cost_price': 18.75,
                'selling_price': 24.00,
                'currency': 'EUR',
                'estimated_delivery_days': 3
            }
        ]

        return Response(mock_rates)


class TrackingEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Tracking event viewset"""

    permission_classes = [IsAuthenticated]
    serializer_class = TrackingEventSerializer

    def get_queryset(self):
        """Filter tracking events by user's company shipments"""
        user = self.request.user
        if hasattr(user, 'company'):
            return TrackingEvent.objects.filter(shipment__company=user.company)
        return TrackingEvent.objects.none()


class ShipmentDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """Shipment document viewset"""

    permission_classes = [IsAuthenticated]
    serializer_class = ShipmentDocumentSerializer

    def get_queryset(self):
        """Filter documents by user's company shipments"""
        user = self.request.user
        if hasattr(user, 'company'):
            return ShipmentDocument.objects.filter(shipment__company=user.company)
        return ShipmentDocument.objects.none()


class ShipmentRateViewSet(viewsets.ReadOnlyModelViewSet):
    """Shipment rate viewset"""

    permission_classes = [IsAuthenticated]
    serializer_class = ShipmentRateSerializer

    def get_queryset(self):
        """Filter rates by user's company"""
        user = self.request.user
        if hasattr(user, 'company'):
            return ShipmentRate.objects.filter(company=user.company)
        return ShipmentRate.objects.none()
