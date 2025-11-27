"""
Payment API Serializers for Send-Pakket Platform
"""

from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .models import (
    Subscription, Invoice, InvoiceItem, Payment,
    UsageRecord, ShipmentTransaction
)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model"""

    company_name = serializers.CharField(source='company.name', read_only=True)
    days_until_renewal = serializers.SerializerMethodField()
    usage_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'company', 'company_name', 'plan_type', 'billing_cycle',
            'monthly_price', 'currency', 'monthly_shipment_limit',
            'api_calls_per_minute', 'included_features', 'status',
            'started_at', 'current_period_start', 'current_period_end',
            'cancelled_at', 'stripe_subscription_id', 'stripe_customer_id',
            'current_period_shipments', 'total_shipments', 'days_until_renewal',
            'usage_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'started_at', 'created_at', 'updated_at']

    def get_days_until_renewal(self, obj):
        """Calculate days until subscription renewal"""
        if obj.current_period_end:
            delta = obj.current_period_end - timezone.now()
            return max(0, delta.days)
        return 0

    def get_usage_percentage(self, obj):
        """Calculate usage percentage of monthly limit"""
        if obj.monthly_shipment_limit and obj.monthly_shipment_limit > 0:
            return min(100, (obj.current_period_shipments / obj.monthly_shipment_limit) * 100)
        return 0


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceItem model"""

    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'invoice', 'description', 'quantity', 'unit_price',
            'total_price', 'item_type', 'subscription', 'metadata'
        ]
        read_only_fields = ['id', 'total_price']

    def create(self, validated_data):
        """Calculate total_price on creation"""
        quantity = validated_data.get('quantity', 1)
        unit_price = validated_data.get('unit_price', 0)
        validated_data['total_price'] = quantity * unit_price
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Recalculate total_price on update"""
        quantity = validated_data.get('quantity', instance.quantity)
        unit_price = validated_data.get('unit_price', instance.unit_price)
        validated_data['total_price'] = quantity * unit_price
        return super().update(instance, validated_data)


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model"""

    company_name = serializers.CharField(source='company.name', read_only=True)
    subscription_plan = serializers.CharField(source='subscription.plan_type', read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    days_overdue = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'company', 'company_name', 'subscription', 'subscription_plan',
            'invoice_number', 'period_start', 'period_end', 'subtotal',
            'tax_amount', 'total_amount', 'currency', 'status', 'due_date',
            'paid_at', 'payment_method', 'stripe_invoice_id',
            'stripe_payment_intent_id', 'pdf_url', 'items', 'days_overdue',
            'payment_status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'company', 'items', 'created_at', 'updated_at'
        ]

    def get_days_overdue(self, obj):
        """Calculate days overdue if unpaid"""
        if obj.status in ['paid', 'cancelled', 'refunded']:
            return 0
        if obj.due_date and timezone.now().date() > obj.due_date.date():
            delta = timezone.now().date() - obj.due_date.date()
            return delta.days
        return 0

    def get_payment_status(self, obj):
        """Get payment status summary"""
        if obj.status == 'paid':
            return 'paid'
        elif obj.status == 'overdue':
            return 'overdue'
        elif obj.status in ['cancelled', 'refunded']:
            return 'cancelled'
        else:
            return 'pending'


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""

    company_name = serializers.CharField(source='company.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    gateway_fee = serializers.SerializerMethodField()
    net_amount = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'company', 'company_name', 'invoice', 'invoice_number',
            'amount', 'currency', 'payment_method', 'status',
            'stripe_payment_id', 'gateway_transaction_id', 'failure_reason',
            'gateway_response', 'processed_at', 'gateway_fee', 'net_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'company', 'processed_at', 'created_at', 'updated_at'
        ]

    def get_gateway_fee(self, obj):
        """Calculate gateway fee based on payment method"""
        # Simplified fee calculation - in real implementation, use actual gateway fees
        if obj.payment_method == 'card':
            return obj.amount * Decimal('0.029') + Decimal('0.25')  # 2.9% + €0.25
        elif obj.payment_method == 'paypal':
            return obj.amount * Decimal('0.035') + Decimal('0.35')  # 3.5% + €0.35
        return Decimal('0.00')

    def get_net_amount(self, obj):
        """Calculate net amount after fees"""
        gateway_fee = self.get_gateway_fee(obj)
        return obj.amount - gateway_fee


class UsageRecordSerializer(serializers.ModelSerializer):
    """Serializer for UsageRecord model"""

    company_name = serializers.CharField(source='company.name', read_only=True)
    subscription_plan = serializers.CharField(source='subscription.plan_type', read_only=True)
    shipment_number = serializers.SerializerMethodField()

    class Meta:
        model = UsageRecord
        fields = [
            'id', 'company', 'company_name', 'subscription', 'subscription_plan',
            'usage_type', 'quantity', 'unit_price', 'total_cost', 'is_billable',
            'is_included_in_plan', 'shipment', 'shipment_number',
            'billing_period_start', 'billing_period_end', 'invoice', 'metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'company', 'total_cost', 'created_at']

    def get_shipment_number(self, obj):
        """Get shipment number, handling None shipment"""
        return obj.shipment.shipment_number if obj.shipment else None

    def create(self, validated_data):
        """Calculate total_cost on creation"""
        quantity = validated_data.get('quantity', 1)
        unit_price = validated_data.get('unit_price', 0)
        validated_data['total_cost'] = quantity * unit_price
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Recalculate total_cost on update"""
        quantity = validated_data.get('quantity', instance.quantity)
        unit_price = validated_data.get('unit_price', instance.unit_price)
        validated_data['total_cost'] = quantity * unit_price
        return super().update(instance, validated_data)


class ShipmentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for ShipmentTransaction model"""

    company_name = serializers.CharField(source='company.name', read_only=True)
    shipment_number = serializers.SerializerMethodField()
    carrier_name = serializers.SerializerMethodField()

    class Meta:
        model = ShipmentTransaction
        fields = [
            'id', 'company', 'company_name', 'shipment', 'shipment_number',
            'carrier_name', 'carrier_cost', 'platform_fee', 'customer_charge',
            'gross_profit', 'profit_margin_percent', 'currency', 'billing_status',
            'invoice', 'payment', 'billed_at', 'paid_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'company', 'gross_profit', 'profit_margin_percent', 'created_at', 'updated_at'
        ]

    def get_shipment_number(self, obj):
        """Get shipment number, handling None shipment"""
        return obj.shipment.shipment_number if obj.shipment else None

    def get_carrier_name(self, obj):
        """Get carrier name, handling None shipment"""
        return obj.shipment.carrier.name if obj.shipment else None


# Specialized serializers for different use cases

class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating subscriptions"""

    class Meta:
        model = Subscription
        fields = [
            'company', 'plan_type', 'billing_cycle', 'monthly_price', 'currency',
            'monthly_shipment_limit', 'api_calls_per_minute', 'included_features'
        ]
        read_only_fields = ['company']

    def create(self, validated_data):
        """Create subscription with company from request context"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            company = request.user.company
            validated_data['company'] = company

            # Set current period dates based on billing cycle
            from datetime import datetime, timedelta
            now = timezone.now()

            if validated_data.get('billing_cycle') == 'monthly':
                period_end = now.replace(day=1, month=now.month + 1) - timedelta(days=1)
            elif validated_data.get('billing_cycle') == 'quarterly':
                # Calculate next quarter end
                quarter = ((now.month - 1) // 3) + 1
                if quarter == 4:
                    period_end = now.replace(month=12, day=31, year=now.year)
                else:
                    period_end = now.replace(month=quarter*3 + 1, day=1, year=now.year) - timedelta(days=1)
            else:  # yearly
                period_end = now.replace(month=12, day=31, year=now.year)

            validated_data['current_period_end'] = period_end

        return super().create(validated_data)


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating invoices"""

    items = InvoiceItemSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = [
            'company', 'subscription', 'period_start', 'period_end', 'subtotal',
            'tax_amount', 'total_amount', 'currency', 'due_date', 'items'
        ]
        read_only_fields = ['company']

    def create(self, validated_data):
        """Create invoice with company from subscription"""
        subscription = validated_data.get('subscription')
        if subscription:
            validated_data['company'] = subscription.company
        return super().create(validated_data)


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments"""

    class Meta:
        model = Payment
        fields = [
            'invoice', 'amount', 'currency', 'payment_method', 'status'
        ]
        read_only_fields = ['status']

    def create(self, validated_data):
        """Create payment with company from invoice"""
        invoice = validated_data.get('invoice')
        if invoice:
            validated_data['company'] = invoice.company
        return super().create(validated_data)