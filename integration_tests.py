"""
Integration tests for the central core system and tenant isolation.
Tests the Company-MerchantCore relationship and data isolation across apps.
"""
import uuid
from decimal import Decimal
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from core.models import Company, Address
from platform_core.models import MerchantCore
from payments.models import Subscription
from shipping.models import Shipment
from carriers.models import Carrier, CarrierService

User = get_user_model()


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
})
class CentralCoreIntegrationTestCase(APITestCase):
    """Test integration between central core and all apps.

    Uses an in-memory cache to avoid external Redis dependency during tests.
    """

    def setUp(self):
        """Set up test data for integration testing."""
        # Create companies (tenants)
        self.company1 = Company.objects.create(
            user=User.objects.create_user(
                username="user1@test1.com",
                email="user1@test1.com",
                password="password123"
            ),
            name="Test Company 1",
            registration_number="REG001",
            vat_number="VAT001",
            address_line1="123 Test St",
            city="Test City",
            postal_code="12345",
            country="NL",
            phone="+1234567890",
            is_active=True
        )
        self.company2 = Company.objects.create(
            user=User.objects.create_user(
                username="user2@test2.com",
                email="user2@test2.com",
                password="password123"
            ),
            name="Test Company 2",
            registration_number="REG002",
            vat_number="VAT002",
            address_line1="456 Test Ave",
            city="Test City 2",
            postal_code="67890",
            country="NL",
            phone="+0987654321",
            is_active=True
        )

        # Set user roles for admin access
        self.company1.user.role = 'admin'
        self.company2.user.role = 'admin'
        self.company1.user.save()
        self.company2.user.save()

        # Get merchant cores created by signals
        self.merchant_core1 = self.company1.merchant_core
        self.merchant_core2 = self.company2.merchant_core

        # Get users from companies (already created above)
        self.user1 = self.company1.user
        self.user2 = self.company2.user

        # Create test data for each tenant
        self.subscription1 = Subscription.objects.create(
            company=self.company1,
            stripe_subscription_id=f"sub_test1_{uuid.uuid4()}",
            status="active",
            current_period_start="2024-01-01T00:00:00Z",
            current_period_end="2024-12-31T23:59:59Z"
        )
        self.subscription2 = Subscription.objects.create(
            company=self.company2,
            stripe_subscription_id=f"sub_test2_{uuid.uuid4()}",
            status="active",
            current_period_start="2024-01-01T00:00:00Z",
            current_period_end="2024-12-31T23:59:59Z"
        )

        # Create addresses for shipments
        self.address1 = Address.objects.create(
            company=self.company1,
            address_type='business',
            name='Test Sender',
            address_line1='123 Test Street',
            city='Test City',
            postal_code='12345',
            country='NL',
            phone='+1234567890'
        )
        self.address2 = Address.objects.create(
            company=self.company2,
            address_type='business',
            name='Test Sender 2',
            address_line1='456 Test Avenue',
            city='Test City 2',
            postal_code='67890',
            country='NL',
            phone='+0987654321'
        )

        # Create carriers (global, not company-specific)
        self.carrier1 = Carrier.objects.create(
            name="Test Carrier 1",
            code="TC1",
            display_name="Test Carrier One",
            is_active=True,
            requires_account=False,
            requires_api_key=False
        )
        self.carrier_service1 = CarrierService.objects.create(
            carrier=self.carrier1,
            name="Standard Service",
            code="STD",
            display_name="Standard Delivery",
            service_type="standard"
        )

        self.carrier2 = Carrier.objects.create(
            name="Test Carrier 2",
            code="TC2",
            display_name="Test Carrier Two",
            is_active=True,
            requires_account=False,
            requires_api_key=False
        )
        self.carrier_service2 = CarrierService.objects.create(
            carrier=self.carrier2,
            name="Express Service",
            code="EXP",
            display_name="Express Delivery",
            service_type="express"
        )

        # Create shipments with all required fields
        self.shipment1 = Shipment.objects.create(
            company=self.company1,
            carrier=self.carrier1,
            service=self.carrier_service1,
            sender_address=self.address1,
            recipient_address={
                'name': 'Test Recipient',
                'address_line1': '789 Recipient Street',
                'city': 'Recipient City',
                'postal_code': '54321',
                'country': 'NL',
                'phone': '+1122334455'
            },
            weight=Decimal('1.5'),
            description='Test shipment',
            contents=[],
            tracking_number=f"TN_test1_{uuid.uuid4()}",
            status="pending"
        )
        self.shipment2 = Shipment.objects.create(
            company=self.company2,
            carrier=self.carrier2,
            service=self.carrier_service2,
            sender_address=self.address2,
            recipient_address={
                'name': 'Test Recipient 2',
                'address_line1': '321 Recipient Avenue',
                'city': 'Recipient City 2',
                'postal_code': '09876',
                'country': 'NL',
                'phone': '+5566778899'
            },
            weight=Decimal('2.0'),
            description='Test shipment 2',
            contents=[],
            tracking_number=f"TN_test2_{uuid.uuid4()}",
            status="pending"
        )

    def test_merchant_core_automatic_creation(self):
        """Test that merchant cores are automatically created for companies."""
        # Create a new company
        new_user = User.objects.create_user(
            username="newuser@test.com",
            email="newuser@test.com",
            password="password123"
        )
        new_company = Company.objects.create(
            user=new_user,
            name="New Test Company",
            registration_number="REG003",
            vat_number="VAT003",
            address_line1="789 Test Blvd",
            city="New Test City",
            postal_code="11111",
            country="NL",
            phone="+1122334455",
            is_active=True
        )

        # Verify merchant core was created
        self.assertTrue(hasattr(new_company, 'merchant_core'))
        self.assertIsNotNone(new_company.merchant_core)
        self.assertEqual(new_company.merchant_core.name, "New Test Company Core")

    def test_tenant_isolation_payments(self):
        """Test that payment data is properly isolated by tenant."""
        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)

        # Get subscriptions - should only see company1's subscription
        url = reverse('subscription-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only return subscription1
        subscriptions = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(subscriptions), 1)
        self.assertEqual(subscriptions[0]['stripe_subscription_id'], self.subscription1.stripe_subscription_id)

        # Switch to user2
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only return subscription2
        subscriptions = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(subscriptions), 1)
        self.assertEqual(subscriptions[0]['stripe_subscription_id'], self.subscription2.stripe_subscription_id)

    def test_tenant_isolation_shipping(self):
        """Test that shipping data is properly isolated by tenant."""
        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)

        # Get shipments - should only see company1's shipment
        url = reverse('shipment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only return shipment1
        shipments = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(shipments), 1)
        self.assertEqual(shipments[0]['tracking_number'], self.shipment1.tracking_number)

        # Switch to user2
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only return shipment2
        shipments = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(shipments), 1)
        self.assertEqual(shipments[0]['tracking_number'], self.shipment2.tracking_number)

    def test_tenant_isolation_carriers(self):
        """Test that carrier data is properly isolated by tenant."""
        # Note: Carriers are global services, not tenant-isolated
        # Companies have credentials for carriers they use
        # This test verifies that carrier credentials are properly isolated

        # Create carrier credentials for company1
        from carriers.models import CarrierCredentials
        cred1 = CarrierCredentials.objects.create(
            company=self.company1,
            carrier=self.carrier1,
            api_key="test_key_1",
            is_active=True
        )

        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)

        # Get carrier credentials - should only see company1's credentials
        url = reverse('carrier-credentials-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only return credentials for company1
        credentials = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(credentials), 1)
        self.assertEqual(str(credentials[0]['carrier']), str(self.carrier1.id))

        # Switch to user2
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should return empty list (no credentials for company2)
        credentials = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(credentials), 0)

    def test_platform_core_tenant_isolation(self):
        """Test that platform core data is properly isolated by tenant."""
        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)

        # Get merchant core - should only see company1's merchant core
        url = reverse('merchant-cores-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only return merchant_core1
        merchant_cores = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(merchant_cores), 1)
        self.assertEqual(merchant_cores[0]['id'], str(self.merchant_core1.id))

        # Switch to user2
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only return merchant_core2
        merchant_cores = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(merchant_cores), 1)
        self.assertEqual(merchant_cores[0]['id'], str(self.merchant_core2.id))

    def test_cross_tenant_data_isolation(self):
        """Test that users cannot access data from other tenants."""
        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)

        # Try to access company2's subscription directly by ID
        url = reverse('subscription-detail', kwargs={'pk': self.subscription2.pk})
        response = self.client.get(url)
        # Should return 404 (not found) due to tenant filtering
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Try to access company2's shipment
        url = reverse('shipment-detail', kwargs={'pk': self.shipment2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Try to access company2's carrier credentials
        from carriers.models import CarrierCredentials
        cred2 = CarrierCredentials.objects.create(
            company=self.company2,
            carrier=self.carrier2,
            api_key="test_key_2",
            is_active=True
        )
        url = reverse('carrier-credentials-detail', kwargs={'pk': cred2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Try to access company2's merchant core
        url = reverse('merchant-cores-detail', kwargs={'pk': self.merchant_core2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_merchant_core_relationship_integrity(self):
        """Test that the Company-MerchantCore relationship is maintained."""
        # Verify all companies have merchant cores
        companies = Company.objects.all()
        for company in companies:
            self.assertTrue(hasattr(company, 'merchant_core'))
            self.assertIsNotNone(company.merchant_core)
            self.assertEqual(company.merchant_core.name, f"{company.name} Core")

        # Verify merchant cores are unique per company
        merchant_cores = MerchantCore.objects.all()
        companies_with_cores = Company.objects.filter(merchant_core__isnull=False)
        self.assertEqual(len(merchant_cores), companies_with_cores.count())  # No duplicates

    def test_central_core_service_integration(self):
        """Test that central core services work with tenant isolation."""
        from platform_core.services import MerchantCoreService

        # Test service methods work with tenant context
        # Get merchant core for company1
        merchant_core = MerchantCoreService.get_merchant_core(self.company1)
        self.assertEqual(merchant_core, self.merchant_core1)

        # Get merchant core for company2
        merchant_core = MerchantCoreService.get_merchant_core(self.company2)
        self.assertEqual(merchant_core, self.merchant_core2)

        # Verify they are different
        self.assertNotEqual(
            MerchantCoreService.get_merchant_core(self.company1),
            MerchantCoreService.get_merchant_core(self.company2)
        )