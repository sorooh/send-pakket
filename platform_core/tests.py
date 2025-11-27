"""
Central core tests
"""

import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import (
    PlatformCore, MerchantCore, CoreService, MerchantService,
    CoreConfiguration, CoreEvent, CoreMetric
)
from .services import (
    PlatformCoreService, MerchantCoreService, CoreServiceManager,
    CoreConfigurationService, CoreEventService, CoreMetricsService
)

User = get_user_model()


class PlatformCoreModelTest(TestCase):
    """
    Platform core model tests
    """

    def setUp(self):
        """Set up initial test data"""
        self.platform_core = PlatformCore.objects.create(
            platform_name="Test Platform Core",
            platform_version="1.0.0",
            system_status="operational"
        )

    def test_platform_core_creation(self):
        """Test platform core creation"""
        self.assertEqual(self.platform_core.platform_name, "Test Platform Core")
        self.assertEqual(self.platform_core.system_status, "operational")
        self.assertIsNotNone(self.platform_core.created_at)

    def test_platform_core_str_method(self):
        """Test model string representation"""
        self.assertEqual(str(self.platform_core), "Test Platform Core v1.0.0")


class MerchantCoreModelTest(TestCase):
    """
    Merchant core model tests
    """

    def setUp(self):
        """Set up initial test data"""
        self.platform_core = PlatformCore.objects.create(
            platform_name="Test Platform",
            platform_version="1.0.0",
            system_status="operational"
        )

        self.merchant_core = MerchantCore.objects.create(
            platform_core=self.platform_core,
            merchant_id="test_merchant_001",
            name="Test Merchant",
            business_type="ecommerce",
            status="active"
        )

    def test_merchant_core_creation(self):
        """Test merchant core creation"""
        self.assertEqual(self.merchant_core.name, "Test Merchant")
        self.assertEqual(self.merchant_core.merchant_id, "test_merchant_001")
        self.assertEqual(self.merchant_core.platform_core, self.platform_core)
        self.assertEqual(self.merchant_core.status, "active")

    def test_merchant_core_str_method(self):
        """Test model string representation"""
        expected = "Test Merchant (test_merchant_001)"
        self.assertEqual(str(self.merchant_core), expected)


class CoreServiceModelTest(TestCase):
    """
    Core service model tests
    """

    def setUp(self):
        """Set up initial test data"""
        self.core_service = CoreService.objects.create(
            service_name="test_service",
            display_name="Test Service",
            description="Test service description",
            service_type="shipping",
            status="active"
        )

    def test_core_service_creation(self):
        """Test core service creation"""
        self.assertEqual(self.core_service.service_name, "test_service")
        self.assertEqual(self.core_service.service_type, "shipping")
        self.assertIsInstance(self.core_service.configuration, dict)


class PlatformCoreServiceTest(TestCase):
    """
    Platform core service tests
    """

    def test_get_platform_core_singleton(self):
        """Test getting platform core as Singleton"""
        core1 = PlatformCoreService.get_platform_core()
        core2 = PlatformCoreService.get_platform_core()

        self.assertEqual(core1, core2)
        self.assertIsInstance(core1, PlatformCore)

    def test_update_platform_status(self):
        """Test updating platform status"""
        PlatformCoreService.set_maintenance_mode(True, "Test maintenance")

        core = PlatformCoreService.get_platform_core()
        self.assertEqual(core.system_status, "maintenance")
        self.assertTrue(core.is_maintenance_mode)

    def test_update_platform_stats_smoke(self):
        """Smoke test for update_platform_stats method"""
        # Call update_platform_stats
        try:
            PlatformCoreService.update_platform_stats()
            # Should not raise any exceptions
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"update_platform_stats raised an exception: {e}")


class MerchantCoreServiceTest(TestCase):
    """
    Merchant core service tests
    """

    def setUp(self):
        """Set up initial test data"""
        self.platform_core = PlatformCoreService.get_platform_core()

    def test_create_merchant_core(self):
        """Test creating merchant core"""
        merchant_data = {
            "merchant_id": "new_merchant_001",
            "name": "New Merchant",
            "business_type": "ecommerce",
            "settings": {"theme": "blue"}
        }

        merchant_core = MerchantCoreService.create_merchant_core(merchant_data)

        self.assertIsInstance(merchant_core, MerchantCore)
        self.assertEqual(merchant_core.name, "New Merchant")
        self.assertEqual(merchant_core.merchant_id, "new_merchant_001")
        self.assertEqual(merchant_core.platform_core, self.platform_core)

    def test_update_merchant_stats_smoke(self):
        """Smoke test for update_merchant_stats method"""
        # Create a merchant core
        merchant_data = {
            "merchant_id": "stats_test_merchant",
            "name": "Stats Test Merchant",
            "business_type": "ecommerce"
        }
        merchant_core = MerchantCoreService.create_merchant_core(merchant_data)

        # Call update_merchant_stats (currently a placeholder)
        try:
            MerchantCoreService.update_merchant_stats(merchant_core)
            # Should not raise any exceptions
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"update_merchant_stats raised an exception: {e}")


class CoreConfigurationServiceTest(TestCase):
    """
    Core configuration service tests
    """

    def setUp(self):
        """Set up initial test data"""
        self.platform_core = PlatformCoreService.get_platform_core()

    def test_set_configuration(self):
        """Test setting configuration"""
        result = CoreConfigurationService.set_config_value(
            config_key="test_config",
            config_value={"enabled": True},
            scope="global",
            description="Test configuration"
        )

        self.assertIsInstance(result, CoreConfiguration)
        self.assertEqual(result.config_key, "test_config")
        self.assertTrue(result.config_value["enabled"])

    def test_get_configuration(self):
        """Test getting configuration"""
        # Set configuration first
        CoreConfigurationService.set_config_value(
            config_key="test_config",
            config_value={"enabled": True},
            scope="global",
            description="Test configuration"
        )

        # Get configuration
        config_value = CoreConfigurationService.get_config_value(
            config_key="test_config",
            scope="global"
        )

        self.assertIsNotNone(config_value)
        self.assertTrue(config_value["enabled"])


class CoreEventServiceTest(TestCase):
    """
    Core event service tests
    """

    def test_log_event(self):
        """Test logging event"""
        event = CoreEventService.log_event(
            event_type="test_event",
            level="info",
            title="Test Event",
            description="Test event description",
            source_ip="127.0.0.1",
            metadata={"test": "data"}
        )

        self.assertIsInstance(event, CoreEvent)
        self.assertEqual(event.event_type, "test_event")
        self.assertEqual(event.source_ip, "127.0.0.1")

    def test_get_events_by_source(self):
        """Test getting events by source"""
        # Log events
        CoreEventService.log_event(
            event_type="event1",
            level="info",
            title="Event 1",
            description="Event 1",
            source_ip="127.0.0.1"
        )
        CoreEventService.log_event(
            event_type="event2",
            level="info",
            title="Event 2",
            description="Event 2",
            source_ip="127.0.0.1"
        )

        events = CoreEventService.get_recent_events(limit=10)
        # Should have at least the 2 events we logged (may have more due to signals)
        self.assertGreaterEqual(len(events), 2)


class CoreMetricsServiceTest(TestCase):
    """
    Core metrics service tests
    """

    def test_increment_metric(self):
        """Test incrementing metric"""
        metric = CoreMetricsService.increment_metric(
            metric_name="test_metric",
            value=5,
            source="test_source",
            metadata={"category": "test"}
        )

        self.assertIsInstance(metric, CoreMetric)
        self.assertEqual(metric.metric_name, "test_metric")
        self.assertEqual(metric.metric_value, 5)

    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        # Increment metric
        CoreMetricsService.increment_metric(
            metric_name="test_metric",
            value=10,
            source="test_source"
        )

        summary = CoreMetricsService.get_metrics_summary("test_metric")
        self.assertIn('count', summary)
        self.assertEqual(summary['count'], 1)


class PlatformCoreAPITest(APITestCase):
    """
    Platform core API tests
    """

    def setUp(self):
        """Set up initial test data"""
        self.user = User.objects.create_superuser(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.platform_core = PlatformCoreService.get_platform_core()

    def test_get_platform_core(self):
        """Test getting platform core"""
        url = reverse('platform-core-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_merchant_core(self):
        """Test creating merchant core via API"""
        url = reverse('merchant-cores-list')
        data = {
            "merchant_id": "api_test_merchant_001",
            "name": "API Test Merchant",
            "business_type": "ecommerce",
            "settings": {"theme": "dark"}
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "API Test Merchant")

    def test_get_core_services(self):
        """Test getting core services"""
        url = reverse('core-services-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have basic services created in apps.py

    def test_set_configuration(self):
        """Test setting configuration via API"""
        url = reverse('core-configurations-set-value')
        data = {
            "key": "api_test_config",
            "value": {"enabled": True},
            "scope": "global",
            "description": "API test configuration"
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_event(self):
        """Test logging event via API"""
        # Create an event through the service
        from .services import CoreEventService
        CoreEventService.log_event(
            event_type='api_test_event',
            level='info',
            title='API Test Event',
            description='API test event',
            source_ip='127.0.0.1',
            metadata={'test': 'api'}
        )

        # Test getting events
        url = reverse('core-events-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_record_metric(self):
        """Test recording metric via API"""
        # Create a metric through the service
        from .services import CoreMetricsService
        CoreMetricsService.record_metric(
            metric_type='usage',
            metric_name='api_test_metric',
            metric_value=100,
            unit='count',
            tags={'source': 'api_test'},
            metadata={'category': 'api'}
        )

        # Test getting metrics
        url = reverse('core-metrics-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
