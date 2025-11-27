"""
Shipping API Tests - Send-Pakket Platform
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from decimal import Decimal
import json

from core.models import Company, User, Address
from carriers.models import Carrier, CarrierService
from .models import Shipment, TrackingEvent, ShipmentItem, ShipmentDocument, ShipmentRate


class ShipmentAPITestCase(APITestCase):
    """Test cases for Shipment API"""

    def setUp(self):
        """Set up test data"""
        # Create test user first
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test company
        self.company = Company.objects.create(
            user=self.user,
            name="Test Shipping Company",
            registration_number="TEST123456",
            vat_number="VAT123456",
            address_line1="123 Test St",
            city="Test City",
            postal_code="12345",
            country="US",
            phone="+1234567890"
        )

        # Create test carrier and service
        self.carrier = Carrier.objects.create(
            name="Test Carrier",
            code="TEST",
            display_name="Test Carrier Display",
            website="https://testcarrier.com",
            api_endpoint="https://api.testcarrier.com",
            is_active=True
        )

        self.service = CarrierService.objects.create(
            carrier=self.carrier,
            name="Standard Shipping",
            code="STD",
            display_name="Standard Shipping",
            service_type="standard",
            delivery_days_min=2,
            delivery_days_max=4,
            is_active=True
        )

        # Create test addresses
        self.sender_address = Address.objects.create(
            company=self.company,
            name="Sender Address",
            contact_person="Sender Name",
            phone="+1234567890",
            email="sender@example.com",
            address_line1="123 Sender St",
            city="Sender City",
            postal_code="12345",
            state_province="SC",
            country="US",
            address_type="pickup",
            is_default=True
        )

        self.recipient_address_data = {
            "name": "Recipient Name",
            "company": "Recipient Company",
            "street": "456 Recipient Ave",
            "city": "Recipient City",
            "state": "RC",
            "postal_code": "67890",
            "country": "US",
            "phone": "+0987654321"
        }

        # Create test shipment
        self.shipment = Shipment.objects.create(
            company=self.company,
            shipment_number="TEST001",
            reference="REF001",
            carrier=self.carrier,
            service=self.service,
            sender_address=self.sender_address,
            recipient_address=self.recipient_address_data,
            weight=Decimal('2.5'),
            description="Test shipment",
            contents="Test contents",
            declared_value=Decimal('100.00'),
            currency="USD",
            status="created"
        )

        # Create test shipment item
        self.shipment_item = ShipmentItem.objects.create(
            shipment=self.shipment,
            sku="TEST001",
            name="Test Item",
            quantity=2,
            unit_price=Decimal('25.00'),
            total_price=Decimal('50.00'),  # quantity * unit_price
            weight=Decimal('1.25'),
            country_of_origin="US"
        )

    def test_shipment_list(self):
        """Test listing shipments"""
        self.client.force_authenticate(user=self.user)
        url = reverse('shipment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have at least 1 shipment (created in setUp)
        self.assertGreaterEqual(len(response.data), 1)

    def test_shipment_detail(self):
        """Test retrieving shipment detail"""
        self.client.force_authenticate(user=self.user)
        url = reverse('shipment-detail', kwargs={'pk': self.shipment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['shipment_number'], 'TEST001')

    def test_shipment_create(self):
        """Test creating a new shipment"""
        self.client.force_authenticate(user=self.user)

        # Create a sender address for the new shipment
        new_sender_address = Address.objects.create(
            company=self.company,
            name="New Sender Address",
            contact_person="New Sender",
            phone="+1111111111",
            email="newsender@example.com",
            address_line1="789 New St",
            city="New City",
            postal_code="11111",
            country="US",
            address_type="pickup"
        )

        shipment_data = {
            "reference": "REF002",
            "carrier": self.carrier.id,
            "service": self.service.id,
            "sender_address": new_sender_address.id,
            "recipient_address": {
                "name": "New Recipient",
                "street": "321 New Ave",
                "city": "New City",
                "postal_code": "22222",
                "country": "US"
            },
            "weight": "3.0",
            "description": "New test shipment",
            "declared_value": "150.00",
            "currency": "USD",
            "items": [
                {
                    "sku": "NEW001",
                    "name": "New Item",
                    "quantity": 1,
                    "unit_price": "50.00",
                    "total_price": "50.00",  # quantity * unit_price
                    "weight": "1.5",
                    "country_of_origin": "US"
                }
            ]
        }

        url = reverse('shipment-list')
        response = self.client.post(url, shipment_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Shipment.objects.count(), 2)

    def test_shipment_ship_action(self):
        """Test shipping a shipment"""
        # First create a label
        self.shipment.status = 'label_created'
        self.shipment.save()

        self.client.force_authenticate(user=self.user)
        url = reverse('shipment-ship', kwargs={'pk': self.shipment.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shipment.refresh_from_db()
        self.assertEqual(self.shipment.status, 'shipped')
        self.assertIsNotNone(self.shipment.shipped_at)

    def test_shipment_tracking(self):
        """Test getting shipment tracking"""
        # Create tracking event
        TrackingEvent.objects.create(
            shipment=self.shipment,
            event_code="PICKUP",
            event_description="Package picked up",
            location="Test Location",
            event_timestamp=timezone.now()
        )

        self.client.force_authenticate(user=self.user)
        url = reverse('shipment-tracking', kwargs={'pk': self.shipment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_rates(self):
        """Test getting shipping rates"""
        self.client.force_authenticate(user=self.user)
        url = reverse('shipment-get-rates')

        rate_data = {
            "origin": {
                "country": "US",
                "postal_code": "12345",
                "city": "Test City"
            },
            "destination": {
                "country": "US",
                "postal_code": "67890",
                "city": "Dest City"
            },
            "weight": "2.5"
        }

        response = self.client.post(url, rate_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access shipments"""
        url = reverse('shipment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ShipmentModelTestCase(TestCase):
    """Test cases for Shipment model"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

        self.company = Company.objects.create(
            user=self.user,
            name="Test Company",
            registration_number="TEST789",
            vat_number="VAT789",
            address_line1="123 Test St",
            city="Test City",
            postal_code="12345",
            country="US",
            phone="+1234567890"
        )

        self.carrier = Carrier.objects.create(
            name="Test Carrier",
            code="TEST2",
            display_name="Test Carrier 2",
            website="https://testcarrier2.com",
            api_endpoint="https://api.testcarrier2.com",
            is_active=True
        )

        self.service = CarrierService.objects.create(
            carrier=self.carrier,
            name="Test Service",
            code="TEST",
            display_name="Test Service",
            service_type="standard",
            is_active=True
        )

        # Create test addresses
        self.sender_address = Address.objects.create(
            company=self.company,
            name="Test Sender Address",
            contact_person="Test Sender",
            phone="+1234567890",
            email="sender@example.com",
            address_line1="123 Test St",
            city="Test City",
            postal_code="12345",
            country="US",
            address_type="pickup",
            is_default=True
        )

    def test_shipment_creation(self):
        """Test creating a shipment"""
        shipment = Shipment.objects.create(
            company=self.company,
            carrier=self.carrier,
            service=self.service,
            sender_address=self.sender_address,
            recipient_address={"country": "US"},
            weight=Decimal('1.0'),
            description="Test shipment"
        )

        self.assertEqual(shipment.status, 'draft')
        self.assertIsNotNone(shipment.shipment_number)

    def test_shipment_item_total_calculation(self):
        """Test shipment item total price calculation"""
        shipment = Shipment.objects.create(
            company=self.company,
            carrier=self.carrier,
            service=self.service,
            sender_address=self.sender_address,
            recipient_address={"country": "US"},
            weight=Decimal('1.0'),
            description="Test shipment"
        )

        item = ShipmentItem.objects.create(
            shipment=shipment,
            sku="TEST",
            name="Test Item",
            quantity=2,
            unit_price=Decimal('10.00'),
            total_price=Decimal('20.00')  # quantity * unit_price
        )

        self.assertEqual(item.total_price, Decimal('20.00'))

    def test_tracking_event_creation(self):
        """Test creating tracking events"""
        shipment = Shipment.objects.create(
            company=self.company,
            carrier=self.carrier,
            service=self.service,
            sender_address=self.sender_address,
            recipient_address={"country": "US"},
            weight=Decimal('1.0'),
            description="Test shipment"
        )

        event = TrackingEvent.objects.create(
            shipment=shipment,
            event_code="CREATED",
            event_description="Shipment created",
            event_timestamp=timezone.now()
        )

        self.assertEqual(event.event_code, "CREATED")
        self.assertEqual(event.shipment, shipment)
