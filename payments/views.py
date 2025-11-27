"""
Payment API Views for Send-Pakket Platform
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    Subscription, Invoice, InvoiceItem, Payment,
    UsageRecord, ShipmentTransaction
)
from .serializers import (
    SubscriptionSerializer, InvoiceSerializer, InvoiceItemSerializer,
    PaymentSerializer, UsageRecordSerializer, ShipmentTransactionSerializer,
    SubscriptionCreateSerializer, InvoiceCreateSerializer, PaymentCreateSerializer
)
from core.models import Company


class CompanyFilterMixin:
    """Mixin to filter querysets by user's company"""

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'company'):
            return queryset.filter(company=self.request.user.company)
        return queryset.none()


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing subscriptions"""

    queryset = Subscription.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'plan_type', 'billing_cycle']

    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer

    def get_queryset(self):
        try:
            company = self.request.user.company
            return Subscription.objects.filter(company=company).select_related('company')
        except AttributeError:
            # Fallback if company relationship fails
            try:
                company = Company.objects.get(user=self.request.user)
                return Subscription.objects.filter(company=company).select_related('company')
            except Company.DoesNotExist:
                return Subscription.objects.none()

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a subscription using Stripe"""
        subscription = self.get_object()

        if subscription.status != 'active':
            return Response(
                {'error': 'Subscription is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .stripe_service import StripePaymentService
            stripe_service = StripePaymentService()

            stripe_service.cancel_subscription(subscription)

            subscription.status = 'cancelled'
            subscription.cancelled_at = timezone.now()
            subscription.save()

            serializer = self.get_serializer(subscription)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': 'Cancellation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a cancelled subscription using Stripe"""
        subscription = self.get_object()

        if subscription.status != 'cancelled':
            return Response(
                {'error': 'Subscription is not cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .stripe_service import StripePaymentService
            stripe_service = StripePaymentService()

            stripe_service.reactivate_subscription(subscription)

            subscription.status = 'active'
            subscription.cancelled_at = None
            subscription.save()

            serializer = self.get_serializer(subscription)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': 'Reactivation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def usage(self, request, pk=None):
        """Get usage statistics for subscription"""
        subscription = self.get_object()

        # Current period usage
        current_usage = UsageRecord.objects.filter(
            subscription=subscription,
            billing_period_start__lte=timezone.now(),
            billing_period_end__gte=timezone.now()
        ).aggregate(
            total_cost=Sum('total_cost'),
            total_quantity=Sum('quantity')
        )

        return Response({
            'current_period': {
                'shipments': subscription.current_period_shipments,
                'cost': current_usage.get('total_cost', 0),
                'quantity': current_usage.get('total_quantity', 0)
            },
            'limits': {
                'monthly_shipment_limit': subscription.monthly_shipment_limit,
                'usage_percentage': subscription.current_period_shipments / subscription.monthly_shipment_limit * 100 if subscription.monthly_shipment_limit else 0
            }
        })


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing invoices"""

    queryset = Invoice.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'currency']

    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceSerializer

    def get_queryset(self):
        try:
            company = self.request.user.company
            return Invoice.objects.filter(company=company).select_related(
                'company', 'subscription'
            ).prefetch_related('items')
        except AttributeError:
            # Fallback if company relationship fails
            try:
                company = Company.objects.get(user=self.request.user)
                return Invoice.objects.filter(company=company).select_related(
                    'company', 'subscription'
                ).prefetch_related('items')
            except Company.DoesNotExist:
                return Invoice.objects.none()

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid"""
        invoice = self.get_object()

        if invoice.status == 'paid':
            return Response(
                {'error': 'Invoice is already paid'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        invoice.payment_method = request.data.get('payment_method', 'manual')
        invoice.save()

        serializer = self.get_serializer(invoice)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue invoices"""
        overdue_invoices = self.get_queryset().filter(
            status__in=['pending', 'draft'],
            due_date__lt=timezone.now().date()
        )

        serializer = self.get_serializer(overdue_invoices, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get invoice summary for company"""
        queryset = self.get_queryset()

        summary = queryset.aggregate(
            total_invoiced=Sum('total_amount'),
            total_paid=Sum('total_amount', filter=Q(status='paid')),
            total_pending=Sum('total_amount', filter=Q(status__in=['pending', 'draft'])),
            total_overdue=Sum('total_amount', filter=Q(
                status__in=['pending', 'draft'],
                due_date__lt=timezone.now().date()
            ))
        )

        # Count by status
        status_counts = queryset.values('status').annotate(
            count=models.Count('id')
        ).order_by('status')

        return Response({
            'financial_summary': summary,
            'status_counts': {item['status']: item['count'] for item in status_counts}
        })


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing invoice items"""

    queryset = InvoiceItem.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceItemSerializer

    def get_queryset(self):
        try:
            company = self.request.user.company
            return InvoiceItem.objects.select_related(
                'invoice__company', 'subscription'
            ).filter(invoice__company=company)
        except AttributeError:
            # Fallback if company relationship fails
            try:
                company = Company.objects.get(user=self.request.user)
                return InvoiceItem.objects.select_related(
                    'invoice__company', 'subscription'
                ).filter(invoice__company=company)
            except Company.DoesNotExist:
                return InvoiceItem.objects.none()


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payments"""

    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method', 'currency']

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer

    def get_queryset(self):
        try:
            company = self.request.user.company
            return Payment.objects.filter(company=company).select_related(
                'company', 'invoice'
            )
        except AttributeError:
            # Fallback if company relationship fails
            try:
                company = Company.objects.get(user=self.request.user)
                return Payment.objects.filter(company=company).select_related(
                    'company', 'invoice'
                )
            except Company.DoesNotExist:
                return Payment.objects.none()

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process a payment using Stripe"""
        payment = self.get_object()

        if payment.status != 'pending':
            return Response(
                {'error': 'Payment is not in pending status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .stripe_service import StripePaymentService
            stripe_service = StripePaymentService()

            # Create payment intent if not exists
            if not payment.stripe_payment_intent_id:
                intent = stripe_service.create_payment_intent(payment)
            else:
                intent = stripe_service.confirm_payment(payment.stripe_payment_intent_id)

            # Check payment status
            if intent.status == 'succeeded':
                payment.status = 'succeeded'
                payment.processed_at = timezone.now()
                payment.gateway_transaction_id = intent.id
                payment.save()

                # Mark invoice as paid if this covers the full amount
                if payment.invoice and payment.amount >= payment.invoice.total_amount:
                    payment.invoice.status = 'paid'
                    payment.invoice.paid_at = timezone.now()
                    payment.invoice.save()

                serializer = self.get_serializer(payment)
                return Response(serializer.data)

            elif intent.status == 'requires_payment_method':
                return Response(
                    {'error': 'Payment requires a payment method', 'client_secret': intent.client_secret},
                    status=status.HTTP_400_BAD_REQUEST
                )

            else:
                return Response(
                    {'error': 'Payment processing incomplete', 'status': intent.status},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            payment.status = 'failed'
            payment.failure_reason = str(e)
            payment.save()

            return Response(
                {'error': 'Payment processing failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Refund a payment using Stripe"""
        payment = self.get_object()

        if payment.status != 'succeeded':
            return Response(
                {'error': 'Only succeeded payments can be refunded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        refund_amount = Decimal(str(request.data.get('amount', payment.amount)))

        if refund_amount > payment.amount:
            return Response(
                {'error': 'Refund amount cannot exceed payment amount'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .stripe_service import StripePaymentService
            stripe_service = StripePaymentService()

            refund = stripe_service.create_refund(payment, refund_amount)

            payment.status = 'refunded'
            payment.save()

            # Update invoice status if fully refunded
            if payment.invoice:
                payment.invoice.status = 'refunded'
                payment.invoice.save()

            return Response({
                'message': f'Payment refunded successfully',
                'refunded_amount': refund_amount,
                'refund_id': refund.id
            })

        except Exception as e:
            return Response(
                {'error': 'Refund failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UsageRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing usage records"""

    queryset = UsageRecord.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UsageRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['usage_type', 'is_billable', 'is_included_in_plan']

    def get_queryset(self):
        try:
            company = self.request.user.company
            return UsageRecord.objects.filter(company=company).select_related(
                'company', 'subscription', 'shipment'
            )
        except AttributeError:
            # Fallback if company relationship fails
            try:
                company = Company.objects.get(user=self.request.user)
                return UsageRecord.objects.filter(company=company).select_related(
                    'company', 'subscription', 'shipment'
                )
            except Company.DoesNotExist:
                return UsageRecord.objects.none()

    def perform_create(self, serializer):
        """Set company from request user"""
        try:
            company = self.request.user.company
        except AttributeError:
            company = Company.objects.get(user=self.request.user)
        serializer.save(company=company)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get usage summary for current billing period"""
        try:
            company = request.user.company
        except AttributeError:
            company = Company.objects.get(user=request.user)

        # Get current month usage
        now = timezone.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        usage_summary = self.get_queryset().filter(
            billing_period_start=period_start,
            billing_period_end=period_end
        ).values('usage_type').annotate(
            total_quantity=Sum('quantity'),
            total_cost=Sum('total_cost'),
            count=models.Count('id')
        ).order_by('usage_type')

        return Response({
            'period': {
                'start': period_start,
                'end': period_end
            },
            'usage_by_type': list(usage_summary)
        })


class ShipmentTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shipment transactions"""

    queryset = ShipmentTransaction.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ShipmentTransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['billing_status', 'currency']

    def get_queryset(self):
        try:
            company = self.request.user.company
            return ShipmentTransaction.objects.filter(company=company).select_related(
                'company', 'shipment', 'invoice', 'payment'
            )
        except AttributeError:
            # Fallback if company relationship fails
            try:
                company = Company.objects.get(user=self.request.user)
                return ShipmentTransaction.objects.filter(company=company).select_related(
                    'company', 'shipment', 'invoice', 'payment'
                )
            except Company.DoesNotExist:
                return ShipmentTransaction.objects.none()

    def perform_create(self, serializer):
        """Set company from request user"""
        try:
            company = self.request.user.company
        except AttributeError:
            company = Company.objects.get(user=self.request.user)
        serializer.save(company=company)

    @action(detail=False, methods=['get'])
    def profit_summary(self, request):
        """Get profit summary for transactions"""
        queryset = self.get_queryset()

        # Date range filter
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )

        summary = queryset.aggregate(
            total_carrier_cost=Sum('carrier_cost'),
            total_platform_fee=Sum('platform_fee'),
            total_customer_charge=Sum('customer_charge'),
            total_gross_profit=Sum('gross_profit'),
            transaction_count=models.Count('id')
        )

        # Average profit margin
        avg_margin = queryset.exclude(customer_charge=0).aggregate(
            avg_margin=Sum('gross_profit') / Sum('customer_charge') * 100
        )

        return Response({
            'summary': summary,
            'average_margin_percent': avg_margin.get('avg_margin', 0),
            'date_range': {
                'start': start_date,
                'end': end_date
            }
        })

    @action(detail=True, methods=['post'])
    def mark_billed(self, request, pk=None):
        """Mark transaction as billed"""
        transaction = self.get_object()

        if transaction.billing_status == 'billed':
            return Response(
                {'error': 'Transaction is already billed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction.billing_status = 'billed'
        transaction.billed_at = timezone.now()
        transaction.save()

        serializer = self.get_serializer(transaction)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark transaction as paid"""
        transaction = self.get_object()

        if transaction.billing_status != 'billed':
            return Response(
                {'error': 'Transaction must be billed first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction.billing_status = 'paid'
        transaction.paid_at = timezone.now()
        transaction.save()

        serializer = self.get_serializer(transaction)
        return Response(serializer.data)
