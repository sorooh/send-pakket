"""
Carrier tests for Send-Pakket Platform
"""

import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from decimal import Decimal
from core.models import User, Company, Address
from .models import Carrier, CarrierService, CarrierCredentials, CarrierPricing, CarrierWebhook


class CarrierAPITestCase(APITestCase):
    """Test cases for Carrier API"""

    def setUp(self):
        """Set up test data"""
        # Create test user first
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        # Create test company linked to user
        self.company = Company.objects.create(
            user=self.user,
            name="Test Shipping Company",
            registration_number="123456789",
            vat_number="NL123456789B01",
            address_line1="Test Street 123",
            city="Amsterdam",
            postal_code="1000AA",
            country="NL",
            phone="+1234567890"
        )

        # Create test carriers
        self.carrier1 = Carrier.objects.create(
            name="PostNL",
            code="postnl",
            display_name="PostNL Netherlands",
            countries_served=["NL", "BE"],
            international_shipping=True,
            supports_tracking=True,
            supports_labels=True,
            is_active=True,
            is_featured=True
        )

        self.carrier2 = Carrier.objects.create(
            name="DHL",
            code="dhl",
            display_name="DHL Express",
            countries_served=["NL", "DE", "FR", "GB"],
            international_shipping=True,
            supports_tracking=True,
            supports_labels=True,
            is_active=True,
            is_featured=False
        )

        # Create test services
        self.service1 = CarrierService.objects.create(
            carrier=self.carrier1,
            name="Standard Delivery",
            code="std",
            display_name="PostNL Standard",
            service_type="standard",
            delivery_days_min=1,
            delivery_days_max=3,
            domestic_only=False,
            max_weight_kg=30,
            is_active=True
        )

        self.service2 = CarrierService.objects.create(
            carrier=self.carrier2,
            name="Express Delivery",
            code="express",
            display_name="DHL Express",
            service_type="express",
            delivery_days_min=1,
            delivery_days_max=1,
            domestic_only=False,
            max_weight_kg=30,
            is_active=True
        )

    def test_carrier_list(self):
        """Test listing carriers"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 2)

        # Check that featured carriers are included
        featured_carriers = [c for c in response.data['results'] if c['is_featured']]
        self.assertGreaterEqual(len(featured_carriers), 1)

    def test_carrier_detail(self):
        """Test retrieving carrier detail"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-detail', kwargs={'pk': self.carrier1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'PostNL')
        self.assertEqual(response.data['code'], 'postnl')
        self.assertIn('services', response.data)

    def test_carrier_services_action(self):
        """Test getting services for a carrier"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-services', kwargs={'pk': self.carrier1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(str(response.data[0]['carrier']), str(self.carrier1.pk))

    def test_carrier_featured_action(self):
        """Test getting featured carriers"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-featured')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include PostNL as it's featured
        carrier_codes = [c['code'] for c in response.data]
        self.assertIn('postnl', carrier_codes)

    def test_carrier_by_country_action(self):
        """Test getting carriers by country"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-by-country') + '?country=NL'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)  # Both carriers serve NL

    def test_carrier_by_country_no_param(self):
        """Test carriers by country without country parameter"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-by-country')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class CarrierServiceAPITestCase(APITestCase):
    """Test cases for Carrier Service API"""

    def setUp(self):
        """Set up test data"""
        # Create test user first
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        # Create test company linked to user
        self.company = Company.objects.create(
            user=self.user,
            name="Test Shipping Company",
            registration_number="123456789",
            vat_number="NL123456789B01",
            address_line1="Test Street 123",
            city="Amsterdam",
            postal_code="1000AA",
            country="NL",
            phone="+1234567890"
        )

        # Create test carrier
        self.carrier = Carrier.objects.create(
            name="PostNL",
            code="postnl",
            display_name="PostNL Netherlands",
            countries_served=["NL", "BE"],
            international_shipping=True,
            is_active=True
        )

        # Create test services
        self.service1 = CarrierService.objects.create(
            carrier=self.carrier,
            name="Standard Delivery",
            code="std",
            display_name="PostNL Standard",
            service_type="standard",
            delivery_days_min=1,
            delivery_days_max=3,
            domestic_only=False,
            max_weight_kg=30,
            is_active=True
        )

        self.service2 = CarrierService.objects.create(
            carrier=self.carrier,
            name="Express Delivery",
            code="express",
            display_name="PostNL Express",
            service_type="express",
            delivery_days_min=1,
            delivery_days_max=1,
            domestic_only=False,
            max_weight_kg=30,
            is_active=True
        )

    def test_service_list(self):
        """Test listing carrier services"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-service-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_service_detail(self):
        """Test retrieving service detail"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-service-detail', kwargs={'pk': self.service1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Standard Delivery')
        self.assertEqual(response.data['code'], 'std')

    def test_service_by_carrier_action(self):
        """Test getting services by carrier"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-service-by-carrier') + f'?carrier_id={self.carrier.pk}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)
        for service in response.data:
            self.assertEqual(str(service['carrier']), str(self.carrier.pk))

    def test_service_by_carrier_no_param(self):
        """Test services by carrier without carrier_id parameter"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-service-by-carrier')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class CarrierCredentialsAPITestCase(APITestCase):
    """Test cases for Carrier Credentials API"""

    def setUp(self):
        """Set up test data"""
        # Create test user first
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        # Create test company linked to user
        self.company = Company.objects.create(
            user=self.user,
            name="Test Shipping Company",
            registration_number="123456789",
            vat_number="NL123456789B01",
            address_line1="Test Street 123",
            city="Amsterdam",
            postal_code="1000AA",
            country="NL",
            phone="+1234567890"
        )

        # Create test carrier
        self.carrier = Carrier.objects.create(
            name="PostNL",
            code="postnl",
            display_name="PostNL Netherlands",
            is_active=True
        )

        # Create test credentials
        self.credentials = CarrierCredentials.objects.create(
            company=self.company,
            carrier=self.carrier,
            api_key="test_api_key",
            username="test_user",
            sandbox_mode=True,
            is_active=True
        )

    def test_credentials_list(self):
        """Test listing carrier credentials"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-credentials-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_credentials_detail(self):
        """Test retrieving credentials detail"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-credentials-detail', kwargs={'pk': self.credentials.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['carrier']), str(self.carrier.pk))
        self.assertEqual(str(response.data['company']), str(self.company.pk))
        # API key should be write-only
        self.assertNotIn('api_key', response.data)

    def test_credentials_create(self):
        """Test creating new credentials"""
        # Create a different carrier for this test
        other_carrier = Carrier.objects.create(
            name="UPS",
            code="ups",
            display_name="UPS Express",
            is_active=True
        )

        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-credentials-list')
        data = {
            'carrier': str(other_carrier.pk),
            'api_key': 'new_api_key',
            'username': 'new_user',
            'sandbox_mode': True
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data['carrier']), str(other_carrier.pk))
        self.assertEqual(str(response.data['company']), str(self.company.pk))

    def test_credentials_verify_action(self):
        """Test verifying credentials"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-credentials-verify', kwargs={'pk': self.credentials.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_verified'])


class CarrierPricingAPITestCase(APITestCase):
    """Test cases for Carrier Pricing API"""

    def setUp(self):
        """Set up test data"""
        # Create test user first
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        # Create test company linked to user
        self.company = Company.objects.create(
            user=self.user,
            name="Test Shipping Company",
            registration_number="123456789",
            vat_number="NL123456789B01",
            address_line1="Test Street 123",
            city="Amsterdam",
            postal_code="1000AA",
            country="NL",
            phone="+1234567890"
        )

        # Create test carrier and service
        self.carrier = Carrier.objects.create(
            name="PostNL",
            code="postnl",
            display_name="PostNL Netherlands",
            is_active=True
        )

        self.service = CarrierService.objects.create(
            carrier=self.carrier,
            name="Standard Delivery",
            code="std",
            display_name="PostNL Standard",
            is_active=True
        )

        # Create test pricing
        self.pricing = CarrierPricing.objects.create(
            carrier_service=self.service,
            origin_country="NL",
            destination_country="BE",
            weight_from_kg=0,
            weight_to_kg=10,
            base_price=Decimal('5.00'),
            price_per_kg=Decimal('1.50'),
            currency="EUR",
            fuel_surcharge_percent=Decimal('8.00'),
            effective_from=timezone.now(),
            is_active=True
        )

    def test_pricing_list(self):
        """Test listing carrier pricing"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-pricing-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_pricing_calculate_rate_action(self):
        """Test calculating shipping rate"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-pricing-calculate-rate')
        params = {
            'carrier_service_id': str(self.service.pk),
            'origin_country': 'NL',
            'destination_country': 'BE',
            'weight_kg': '2.5'
        }
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_price', response.data)
        self.assertIn('currency', response.data)
        self.assertEqual(response.data['currency'], 'EUR')

    def test_pricing_calculate_rate_missing_params(self):
        """Test calculating rate with missing parameters"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-pricing-calculate-rate')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class CarrierModelTestCase(TestCase):
    """Test cases for Carrier models"""

    def setUp(self):
        """Set up test data"""
        # Create test user first
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        # Create test company linked to user
        self.company = Company.objects.create(
            user=self.user,
            name="Test Company",
            registration_number="123456789",
            vat_number="NL123456789B01",
            address_line1="Test Street 123",
            city="Amsterdam",
            postal_code="1000AA",
            country="NL",
            phone="+1234567890"
        )

        self.carrier = Carrier.objects.create(
            name="Test Carrier",
            code="test",
            display_name="Test Carrier Display",
            is_active=True
        )

    def test_carrier_creation(self):
        """Test creating a carrier"""
        self.assertEqual(self.carrier.name, "Test Carrier")
        self.assertEqual(self.carrier.code, "test")
        self.assertTrue(self.carrier.is_active)
        self.assertIsNotNone(self.carrier.id)

    def test_carrier_service_creation(self):
        """Test creating a carrier service"""
        service = CarrierService.objects.create(
            carrier=self.carrier,
            name="Test Service",
            code="test_svc",
            display_name="Test Service Display",
            is_active=True
        )

        self.assertEqual(service.carrier, self.carrier)
        self.assertEqual(service.name, "Test Service")
        self.assertTrue(service.is_active)

    def test_carrier_credentials_creation(self):
        """Test creating carrier credentials"""
        credentials = CarrierCredentials.objects.create(
            company=self.company,
            carrier=self.carrier,
            api_key="test_key",
            sandbox_mode=True
        )

        self.assertEqual(credentials.company, self.company)
        self.assertEqual(credentials.carrier, self.carrier)
        self.assertEqual(credentials.api_key, "test_key")
        self.assertTrue(credentials.sandbox_mode)

    def test_carrier_pricing_creation(self):
        """Test creating carrier pricing"""
        service = CarrierService.objects.create(
            carrier=self.carrier,
            name="Test Service",
            code="test_svc",
            display_name="Test Service Display",
            is_active=True
        )

        pricing = CarrierPricing.objects.create(
            carrier_service=service,
            origin_country="NL",
            destination_country="BE",
            weight_from_kg=0,
            base_price=Decimal('10.00'),
            currency="EUR",
            effective_from=timezone.now(),
            is_active=True
        )

        self.assertEqual(pricing.carrier_service, service)
        self.assertEqual(pricing.origin_country, "NL")
        self.assertEqual(pricing.destination_country, "BE")
        self.assertEqual(pricing.base_price, Decimal('10.00'))

    def test_carrier_webhook_creation(self):
        """Test creating carrier webhook"""
        webhook = CarrierWebhook.objects.create(
            carrier=self.carrier,
            company=self.company,
            webhook_url="https://example.com/webhook",
            event_types=["shipment_delivered"]
        )

        self.assertEqual(webhook.carrier, self.carrier)
        self.assertEqual(webhook.company, self.company)
        self.assertEqual(webhook.webhook_url, "https://example.com/webhook")
        self.assertEqual(webhook.event_types, ["shipment_delivered"])


class CarrierAnalyticsAPITestCase(APITestCase):
    """Test cases for Carrier Analytics API"""

    def setUp(self):
        """Set up test data"""
        # Create test user first
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        # Create test company linked to user
        self.company = Company.objects.create(
            user=self.user,
            name="Test Shipping Company",
            registration_number="123456789",
            vat_number="NL123456789B01",
            address_line1="Test Street 123",
            city="Amsterdam",
            postal_code="1000AA",
            country="NL",
            phone="+1234567890"
        )

        # Create test carriers
        self.carrier1 = Carrier.objects.create(
            name="PostNL",
            code="postnl",
            display_name="PostNL Netherlands",
            countries_served=["NL", "BE"],
            international_shipping=True,
            is_active=True
        )

        self.carrier2 = Carrier.objects.create(
            name="DHL",
            code="dhl",
            display_name="DHL Express",
            countries_served=["NL", "DE"],
            international_shipping=True,
            is_active=True
        )

    def test_carrier_performance(self):
        """Test getting carrier performance statistics"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-analytics-performance', kwargs={'pk': self.carrier1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('carrier_name', response.data)
        self.assertIn('statistics', response.data)
        self.assertEqual(response.data['carrier_name'], 'PostNL Netherlands')

    def test_carrier_performance_invalid_carrier(self):
        """Test performance for non-existent carrier"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-analytics-performance', kwargs={'pk': 999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_carrier_compare(self):
        """Test comparing multiple carriers"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-analytics-compare') + f'?carrier_ids={self.carrier1.pk},{self.carrier2.pk}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('carriers', response.data)
        self.assertEqual(len(response.data['carriers']), 2)

    def test_carrier_compare_no_params(self):
        """Test comparing carriers without carrier_ids"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-analytics-compare')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class CarrierOptimizationAPITestCase(APITestCase):
    """Test cases for Carrier Optimization API"""

    def setUp(self):
        """Set up test data"""
        # Create test user first
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        # Create test company linked to user
        self.company = Company.objects.create(
            user=self.user,
            name="Test Shipping Company",
            registration_number="123456789",
            vat_number="NL123456789B01",
            address_line1="Test Street 123",
            city="Amsterdam",
            postal_code="1000AA",
            country="NL",
            phone="+1234567890"
        )

        # Create test carriers and services
        self.carrier1 = Carrier.objects.create(
            name="PostNL",
            code="postnl",
            display_name="PostNL Netherlands",
            countries_served=["NL", "BE"],
            international_shipping=True,
            is_active=True
        )

        self.carrier2 = Carrier.objects.create(
            name="DHL",
            code="dhl",
            display_name="DHL Express",
            countries_served=["NL", "DE"],
            international_shipping=True,
            is_active=True
        )

        self.service1 = CarrierService.objects.create(
            carrier=self.carrier1,
            name="Standard Delivery",
            code="std",
            display_name="PostNL Standard",
            service_type="standard",
            delivery_days_min=1,
            delivery_days_max=3,
            domestic_only=False,
            max_weight_kg=30,
            is_active=True
        )

        self.service2 = CarrierService.objects.create(
            carrier=self.carrier2,
            name="Express Delivery",
            code="express",
            display_name="DHL Express",
            service_type="express",
            delivery_days_min=1,
            delivery_days_max=1,
            domestic_only=False,
            max_weight_kg=30,
            is_active=True
        )

        # Create pricing for services
        CarrierPricing.objects.create(
            carrier_service=self.service1,
            origin_country="NL",
            destination_country="BE",
            weight_from_kg=0,
            base_price=Decimal('5.00'),
            price_per_kg=Decimal('1.50'),
            currency="EUR",
            fuel_surcharge_percent=Decimal('8.00'),
            effective_from=timezone.now(),
            is_active=True
        )

        CarrierPricing.objects.create(
            carrier_service=self.service2,
            origin_country="NL",
            destination_country="BE",
            weight_from_kg=0,
            base_price=Decimal('12.00'),
            price_per_kg=Decimal('2.50'),
            currency="EUR",
            fuel_surcharge_percent=Decimal('8.00'),
            effective_from=timezone.now(),
            is_active=True
        )

    def test_get_rates(self):
        """Test getting shipping rates"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-optimization-rates')
        data = {
            'origin_country': 'NL',
            'destination_country': 'BE',
            'weight_kg': 2.5
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rates', response.data)
        self.assertGreater(len(response.data['rates']), 0)

        # Check rate structure
        rate = response.data['rates'][0]
        self.assertIn('carrier_name', rate)
        self.assertIn('service_name', rate)
        self.assertIn('selling_price', rate)
        self.assertIn('currency', rate)

    def test_get_rates_missing_params(self):
        """Test getting rates with missing parameters"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-optimization-rates')
        data = {
            'origin_country': 'NL',
            'weight_kg': 2.5
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_optimize_selection(self):
        """Test optimizing carrier selection"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-optimization-select')
        data = {
            'origin_country': 'NL',
            'destination_country': 'BE',
            'weight_kg': 2.5,
            'priority_factors': {
                'cost': 0.6,
                'speed': 0.3,
                'reliability': 0.1
            }
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('optimized_selection', response.data)

        selection = response.data['optimized_selection']
        self.assertIn('carrier_name', selection)
        self.assertIn('service_name', selection)
        self.assertIn('composite_score', selection)

    def test_bulk_rate_calculation(self):
        """Test bulk rate calculation"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-optimization-bulk')
        data = {
            'shipments': [
                {
                    'origin_country': 'NL',
                    'destination_country': 'BE',
                    'weight_kg': 1.0
                },
                {
                    'origin_country': 'NL',
                    'destination_country': 'DE',
                    'weight_kg': 3.0
                }
            ]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)

        # Check first result
        result = response.data['results'][0]
        self.assertIn('shipment_index', result)
        self.assertIn('rates', result)

    def test_bulk_rate_calculation_empty(self):
        """Test bulk rate calculation with empty shipments"""
        self.client.force_authenticate(user=self.user)
        url = reverse('carrier-optimization-bulk')
        data = {'shipments': []}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
