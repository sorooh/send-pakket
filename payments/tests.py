"""
Payment API Tests for Send-Pakket Platform
"""

import json
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from core.models import User, Company
from .models import (
    Subscription, Invoice, InvoiceItem, Payment,
    UsageRecord, ShipmentTransaction
)


class PaymentAPITestCase(APITestCase):
    """Base test case for payment API tests"""

    def setUp(self):
        """Set up test data"""
        # Create test user first - use class name to ensure uniqueness
        username = f"testuser_{self.__class__.__name__}"
        email = f"test_{self.__class__.__name__}@example.com"
        
        self.user = User.objects.create_user(
            username=username,
            email=email,
            password="testpass123",
            company_name="Test Shipping Company"
        )

        # Create test company linked to user
        self.company = Company.objects.create(
            user=self.user,
            name="Test Shipping Company",
            registration_number=f"123456789_{self.__class__.__name__}",
            vat_number=f"NL123456789B01_{self.__class__.__name__}",
            address_line1="Test Address 123",
            city="Amsterdam",
            postal_code="1000AA",
            country="NL",
            phone="+31123456789"
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests in this class"""
        # Clear all payment data to ensure isolation between test classes
        Subscription.objects.all().delete()
        Invoice.objects.all().delete()
        Payment.objects.all().delete()
        UsageRecord.objects.all().delete()
        ShipmentTransaction.objects.all().delete()
        Company.objects.all().delete()
        User.objects.all().delete()
        super().tearDownClass()


class SubscriptionAPITestCase(PaymentAPITestCase):
    """Test cases for Subscription API"""

    def setUp(self):
        super().setUp()

        # Create test subscription
        self.subscription = Subscription.objects.create(
            company=self.company,
            plan_type='business',
            billing_cycle='monthly',
            monthly_price=Decimal('99.99'),
            currency='EUR',
            monthly_shipment_limit=1000,
            status='active',
            current_period_end=timezone.now() + timedelta(days=30)
        )

    def test_list_subscriptions(self):
        """Test listing subscriptions for user's company"""
        url = reverse('subscription-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only the subscription created in setUp
        self.assertEqual(response.data['results'][0]['plan_type'], 'business')

    def test_create_subscription(self):
        """Test creating a new subscription"""
        # Delete existing subscription first since OneToOneField allows only one per company
        self.subscription.delete()
        
        url = reverse('subscription-list')
        data = {
            'plan_type': 'enterprise',
            'billing_cycle': 'yearly',
            'monthly_price': '199.99',
            'currency': 'EUR',
            'monthly_shipment_limit': 5000
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['plan_type'], 'enterprise')
        self.assertEqual(str(response.data['company']), str(self.company.id))

    def test_subscription_isolation(self):
        """Test that users only see their company's subscriptions"""
        # Create another user and company for isolation testing
        other_user = User.objects.create_user(
            username="otheruser_subscription_test",
            email="other_subscription@example.com",
            password="testpass123",
            company_name="Other Company"
        )

        other_company = Company.objects.create(
            user=other_user,
            name="Other Company",
            registration_number="987654321_subscription",
            vat_number="NL987654321B01_subscription",
            address_line1="Other Address 456",
            city="Rotterdam",
            postal_code="2000BB",
            country="NL",
            phone="+31987654321"
        )

        # Create subscription for other company
        Subscription.objects.create(
            company=other_company,
            plan_type='starter',
            billing_cycle='monthly',
            monthly_price=Decimal('49.99'),
            currency='EUR',
            current_period_end=timezone.now() + timedelta(days=30)
        )

        url = reverse('subscription-list')
        response = self.client.get(url)

        # Should only see own company's subscription
        self.assertEqual(len(response.data['results']), 1)  # Only the subscription created in setUp
        self.assertEqual(response.data['results'][0]['plan_type'], 'business')

    def test_cancel_subscription(self):
        """Test cancelling a subscription"""
        url = reverse('subscription-cancel', kwargs={'pk': self.subscription.id})
        
        # Mock Stripe service
        with patch('payments.stripe_service.StripePaymentService') as mock_stripe_class:
            mock_stripe = MagicMock()
            mock_stripe_class.return_value = mock_stripe
            
            # Mock subscription cancellation
            mock_stripe_subscription = MagicMock()
            mock_stripe.cancel_subscription.return_value = mock_stripe_subscription
            
            response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'cancelled')
        self.assertIsNotNone(self.subscription.cancelled_at)

    def test_subscription_usage(self):
        """Test getting subscription usage statistics"""
        url = reverse('subscription-usage', kwargs={'pk': self.subscription.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('current_period', response.data)
        self.assertIn('limits', response.data)


class InvoiceAPITestCase(PaymentAPITestCase):
    """Test cases for Invoice API"""

    def setUp(self):
        super().setUp()

        # Create test subscription
        self.subscription = Subscription.objects.create(
            company=self.company,
            plan_type='business',
            billing_cycle='monthly',
            monthly_price=Decimal('99.99'),
            currency='EUR',
            current_period_end=timezone.now() + timedelta(days=30)
        )

        # Create test invoice
        self.invoice = Invoice.objects.create(
            company=self.company,
            subscription=self.subscription,
            invoice_number='INV-202401-001',
            period_start=timezone.now().replace(day=1),
            period_end=timezone.now().replace(day=28),
            subtotal=Decimal('99.99'),
            tax_amount=Decimal('21.00'),
            total_amount=Decimal('120.99'),
            currency='EUR',
            due_date=timezone.now().date() + timedelta(days=30)
        )

    def test_list_invoices(self):
        """Test listing invoices"""
        url = reverse('invoice-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only the invoice created in setUp

    def test_create_invoice(self):
        """Test creating an invoice"""
        url = reverse('invoice-list')
        data = {
            'subscription': str(self.subscription.id),
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'subtotal': '150.00',
            'tax_amount': '31.50',
            'total_amount': '181.50',
            'currency': 'EUR',
            'due_date': '2024-02-15'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_amount'], '181.50')

    def test_mark_invoice_paid(self):
        """Test marking invoice as paid"""
        url = reverse('invoice-mark-paid', kwargs={'pk': self.invoice.id})
        data = {'payment_method': 'bank_transfer'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'paid')
        self.assertIsNotNone(self.invoice.paid_at)

    def test_invoice_summary(self):
        """Test getting invoice summary"""
        url = reverse('invoice-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('financial_summary', response.data)
        self.assertIn('status_counts', response.data)


class PaymentTestCase(PaymentAPITestCase):
    """Test cases for Payment API"""

    def setUp(self):
        super().setUp()

        # Create test subscription and invoice
        self.subscription = Subscription.objects.create(
            company=self.company,
            plan_type='business',
            billing_cycle='monthly',
            monthly_price=Decimal('99.99'),
            currency='EUR',
            current_period_end=timezone.now() + timedelta(days=30)
        )

        self.invoice = Invoice.objects.create(
            company=self.company,
            subscription=self.subscription,
            invoice_number='INV-202401-001',
            period_start=timezone.now().replace(day=1),
            period_end=timezone.now().replace(day=28),
            subtotal=Decimal('99.99'),
            tax_amount=Decimal('21.00'),
            total_amount=Decimal('120.99'),
            currency='EUR',
            due_date=timezone.now().date() + timedelta(days=30)
        )

        # Create test payment
        self.payment = Payment.objects.create(
            company=self.company,
            invoice=self.invoice,
            amount=Decimal('120.99'),
            currency='EUR',
            payment_method='card'
        )

    def test_list_payments(self):
        """Test listing payments"""
        url = reverse('payment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only the payment created in setUp

    def test_create_payment(self):
        """Test creating a payment"""
        url = reverse('payment-list')
        data = {
            'invoice': str(self.invoice.id),
            'amount': '120.99',
            'currency': 'EUR',
            'payment_method': 'bank_transfer'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '120.99')
        self.assertEqual(response.data['status'], 'pending')

    def test_process_payment(self):
        """Test processing a payment"""
        url = reverse('payment-process', kwargs={'pk': self.payment.id})
        
        # Mock Stripe service
        with patch('payments.stripe_service.StripePaymentService') as mock_stripe_class:
            mock_stripe = MagicMock()
            mock_stripe_class.return_value = mock_stripe
            
            # Mock payment intent
            mock_intent = MagicMock()
            mock_intent.status = 'succeeded'
            mock_intent.id = 'pi_test_123'
            mock_intent.client_secret = 'pi_test_secret'
            mock_stripe.create_payment_intent.return_value = mock_intent
            
            response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'succeeded')
        self.assertIsNotNone(self.payment.processed_at)

    def test_payment_refund(self):
        """Test refunding a payment"""
        # First process the payment
        self.payment.status = 'succeeded'
        self.payment.save()

        url = reverse('payment-refund', kwargs={'pk': self.payment.id})
        data = {'amount': '60.50'}

        # Mock Stripe service
        with patch('payments.stripe_service.StripePaymentService') as mock_stripe_class:
            mock_stripe = MagicMock()
            mock_stripe_class.return_value = mock_stripe
            
            # Mock refund
            mock_refund = MagicMock()
            mock_refund.id = 'rf_test_123'
            mock_stripe.create_refund.return_value = mock_refund
            
            response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'refunded')


class UsageRecordAPITestCase(PaymentAPITestCase):
    """Test cases for Usage Record API"""

    def setUp(self):
        super().setUp()

        # Create test subscription
        self.subscription = Subscription.objects.create(
            company=self.company,
            plan_type='business',
            billing_cycle='monthly',
            monthly_price=Decimal('99.99'),
            currency='EUR',
            current_period_end=timezone.now() + timedelta(days=30)
        )

        # Create test usage record
        self.usage_record = UsageRecord.objects.create(
            company=self.company,
            subscription=self.subscription,
            usage_type='shipment',
            quantity=Decimal('5.00'),
            unit_price=Decimal('2.50'),
            total_cost=Decimal('12.50'),
            is_billable=True,
            billing_period_start=timezone.now().replace(day=1),
            billing_period_end=timezone.now().replace(day=28)
        )

    def test_list_usage_records(self):
        """Test listing usage records"""
        url = reverse('usage-record-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only the usage record created in setUp

    def test_create_usage_record(self):
        """Test creating a usage record"""
        url = reverse('usage-record-list')
        data = {
            'subscription': str(self.subscription.id),
            'usage_type': 'api_call',
            'quantity': '100.00',
            'unit_price': '0.01',
            'is_billable': True,
            'billing_period_start': '2024-01-01',
            'billing_period_end': '2024-01-31'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_cost'], '1.00')  # 100 * 0.01

    def test_usage_summary(self):
        """Test getting usage summary"""
        url = reverse('usage-record-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('period', response.data)
        self.assertIn('usage_by_type', response.data)


class ShipmentTransactionAPITestCase(PaymentAPITestCase):
    """Test cases for Shipment Transaction API"""

    def setUp(self):
        super().setUp()

        # Create test shipment transaction (without shipment for simplicity)
        # In a real scenario, this would be created after shipment booking
        self.transaction = ShipmentTransaction.objects.create(
            company=self.company,
            carrier_cost=Decimal('15.00'),
            platform_fee=Decimal('2.50'),
            customer_charge=Decimal('20.00'),
            currency='EUR'
        )

    def test_list_shipment_transactions(self):
        """Test listing shipment transactions"""
        url = reverse('shipment-transaction-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only the transaction created in setUp

    def test_create_shipment_transaction(self):
        """Test creating a shipment transaction"""
        url = reverse('shipment-transaction-list')
        data = {
            'carrier_cost': '18.50',
            'platform_fee': '3.00',
            'customer_charge': '25.00',
            'currency': 'EUR'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['gross_profit'], '3.50')  # 25 - 18.5 - 3

    def test_profit_summary(self):
        """Test getting profit summary"""
        url = reverse('shipment-transaction-profit-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('average_margin_percent', response.data)

    def test_mark_transaction_billed(self):
        """Test marking transaction as billed"""
        url = reverse('shipment-transaction-mark-billed', kwargs={'pk': self.transaction.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.billing_status, 'billed')
        self.assertIsNotNone(self.transaction.billed_at)


class PaymentModelTestCase(TestCase):
    """Test cases for Payment models"""

    def setUp(self):
        # Create test user first
        self.user = User.objects.create_user(
            username="testuser_model_test",
            email="test_model@example.com",
            password="testpass123",
            company_name="Test Company"
        )

        self.company = Company.objects.create(
            user=self.user,
            name="Test Company",
            registration_number="123456789_model",
            vat_number="NL123456789B01_model",
            address_line1="Test Address 123",
            city="Amsterdam",
            postal_code="1000AA",
            country="NL",
            phone="+31123456789"
        )

    def test_subscription_creation(self):
        """Test subscription model creation"""
        subscription = Subscription.objects.create(
            company=self.company,
            plan_type='business',
            billing_cycle='monthly',
            monthly_price=Decimal('99.99'),
            currency='EUR',
            monthly_shipment_limit=1000,
            current_period_end=timezone.now() + timedelta(days=30)
        )

        self.assertEqual(subscription.plan_type, 'business')
        self.assertEqual(subscription.monthly_price, Decimal('99.99'))
        self.assertTrue(subscription.is_within_limits())

    def test_invoice_number_generation(self):
        """Test automatic invoice number generation"""
        invoice = Invoice.objects.create(
            company=self.company,
            subscription=Subscription.objects.create(
                company=self.company,
                plan_type='starter',
                billing_cycle='monthly',
                monthly_price=Decimal('49.99'),
                currency='EUR',
                current_period_end=timezone.now() + timedelta(days=30)
            ),
            period_start=timezone.now(),
            period_end=timezone.now() + timedelta(days=30),
            subtotal=Decimal('49.99'),
            tax_amount=Decimal('10.50'),
            total_amount=Decimal('60.49'),
            currency='EUR',
            due_date=timezone.now().date() + timedelta(days=30)
        )

        self.assertTrue(invoice.invoice_number.startswith('INV-'))
        self.assertTrue(len(invoice.invoice_number) > 10)

    def test_shipment_transaction_profit_calculation(self):
        """Test automatic profit calculation in shipment transactions"""
        transaction = ShipmentTransaction.objects.create(
            company=self.company,
            carrier_cost=Decimal('15.00'),
            platform_fee=Decimal('2.50'),
            customer_charge=Decimal('20.00'),
            currency='EUR'
        )

        # Check profit calculations
        self.assertEqual(transaction.gross_profit, Decimal('2.50'))  # 20 - 15 - 2.5
        self.assertEqual(transaction.profit_margin_percent, Decimal('12.5'))  # 2.5/20 * 100
