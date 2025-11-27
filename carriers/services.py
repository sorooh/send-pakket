"""
Carrier services for Send-Pakket Platform
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import logging

from .models import Carrier, CarrierService, CarrierPricing, CarrierCredentials

logger = logging.getLogger(__name__)


class CarrierService:
    """Service for managing carriers and carrier operations"""

    @staticmethod
    def get_active_carriers() -> models.QuerySet:
        """Get all active carriers ordered by priority"""
        return Carrier.objects.filter(is_active=True).order_by('priority', 'name')

    @staticmethod
    def get_carriers_for_route(origin_country: str, destination_country: str) -> models.QuerySet:
        """Get carriers that serve a specific route"""
        return Carrier.objects.filter(
            is_active=True,
            countries_served__contains=[origin_country],
            countries_served__contains=[destination_country]
        ).order_by('priority')

    @staticmethod
    def get_carrier_services(carrier: Carrier, origin_country: str = None, destination_country: str = None) -> models.QuerySet:
        """Get active services for a carrier, optionally filtered by route"""
        queryset = CarrierService.objects.filter(carrier=carrier, is_active=True)

        if origin_country and destination_country:
            # Filter services that cover the route
            queryset = queryset.filter(
                models.Q(domestic_only=True, countries_available__contains=[origin_country]) |
                models.Q(international_only=False) &
                (
                    models.Q(countries_available__contains=[destination_country]) |
                    models.Q(countries_available__isnull=True) |
                    models.Q(countries_available=[])
                )
            ).exclude(countries_excluded__contains=[destination_country])

        return queryset.order_by('service_type', 'delivery_days_min')

    @staticmethod
    def calculate_carrier_rate(
        carrier_service: CarrierService,
        weight_kg: float,
        origin_country: str,
        destination_country: str,
        dimensions: Dict = None
    ) -> Optional[Dict]:
        """
        Calculate shipping rate for a carrier service

        Returns dict with cost_price, selling_price, estimated_days, etc.
        """
        try:
            # Get applicable pricing rule
            pricing_rule = CarrierPricing.objects.filter(
                carrier_service=carrier_service,
                origin_country=origin_country,
                destination_country=destination_country,
                weight_from_kg__lte=weight_kg,
                is_active=True,
                effective_from__lte=timezone.now()
            ).filter(
                models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=timezone.now())
            ).order_by('-weight_from_kg').first()

            if not pricing_rule:
                # Try without specific countries (general pricing)
                pricing_rule = CarrierPricing.objects.filter(
                    carrier_service=carrier_service,
                    weight_from_kg__lte=weight_kg,
                    is_active=True,
                    effective_from__lte=timezone.now()
                ).filter(
                    models.Q(origin_country='') | models.Q(origin_country__isnull=True),
                    models.Q(destination_country='') | models.Q(destination_country__isnull=True),
                    models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=timezone.now())
                ).order_by('-weight_from_kg').first()

            if not pricing_rule:
                return None

            # Calculate base cost
            base_cost = pricing_rule.base_price
            weight_cost = pricing_rule.price_per_kg * Decimal(str(weight_kg))

            # Add surcharges
            fuel_surcharge = (base_cost + weight_cost) * (pricing_rule.fuel_surcharge_percent / 100)

            # Check for dimensional weight if dimensions provided
            dimensional_weight = None
            if dimensions:
                length = dimensions.get('length', 0)
                width = dimensions.get('width', 0)
                height = dimensions.get('height', 0)
                if length and width and height:
                    # Standard dimensional weight calculation (length x width x height / 5000)
                    dimensional_weight = (length * width * height) / 5000
                    if dimensional_weight > weight_kg:
                        weight_cost = pricing_rule.price_per_kg * Decimal(str(dimensional_weight))

            total_cost = base_cost + weight_cost + fuel_surcharge

            # Apply markup for selling price (default 20% markup)
            markup_multiplier = Decimal('1.20')
            selling_price = total_cost * markup_multiplier

            return {
                'carrier_service': carrier_service,
                'cost_price': total_cost,
                'selling_price': selling_price,
                'currency': pricing_rule.currency,
                'estimated_days': carrier_service.delivery_days_max or carrier_service.delivery_days_min,
                'service_type': carrier_service.service_type,
                'dimensional_weight': dimensional_weight,
                'pricing_rule': pricing_rule
            }

        except Exception as e:
            logger.error(f"Error calculating carrier rate: {e}")
            return None

    @staticmethod
    def get_best_carrier_rates(
        origin_country: str,
        destination_country: str,
        weight_kg: float,
        dimensions: Dict = None,
        preferred_service_type: str = None,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Get the best carrier rates for a shipment

        Returns list of rate dictionaries sorted by selling price
        """
        rates = []

        # Get carriers that serve this route
        carriers = CarrierService.get_carriers_for_route(origin_country, destination_country)

        for carrier in carriers:
            services = CarrierService.get_carrier_services(carrier, origin_country, destination_country)

            # Filter by preferred service type if specified
            if preferred_service_type:
                services = services.filter(service_type=preferred_service_type)

            for service in services:
                rate = CarrierService.calculate_carrier_rate(
                    service, weight_kg, origin_country, destination_country, dimensions
                )
                if rate:
                    rates.append(rate)

        # Sort by selling price (lowest first)
        rates.sort(key=lambda x: x['selling_price'])

        return rates[:max_results]

    @staticmethod
    def get_carrier_performance_stats(carrier: Carrier, days: int = 30) -> Dict:
        """Get performance statistics for a carrier"""
        from django.db.models import Count, Avg, Q
        from shipping.models import Shipment

        cutoff_date = timezone.now() - timezone.timedelta(days=days)

        shipments = Shipment.objects.filter(
            carrier=carrier,
            created_at__gte=cutoff_date
        )

        total_shipments = shipments.count()
        delivered_shipments = shipments.filter(status='delivered').count()
        failed_shipments = shipments.filter(status__in=['failed_delivery', 'returned']).count()

        # Calculate on-time delivery rate
        on_time_deliveries = shipments.filter(
            status='delivered',
            delivered_at__lte=models.F('estimated_delivery')
        ).count()

        return {
            'total_shipments': total_shipments,
            'delivery_rate': (delivered_shipments / total_shipments * 100) if total_shipments > 0 else 0,
            'failure_rate': (failed_shipments / total_shipments * 100) if total_shipments > 0 else 0,
            'on_time_rate': (on_time_deliveries / delivered_shipments * 100) if delivered_shipments > 0 else 0,
            'average_delivery_days': shipments.filter(status='delivered').aggregate(
                avg_days=Avg(models.F('delivered_at') - models.F('shipped_at'))
            )['avg_days']
        }

    @staticmethod
    def optimize_carrier_selection(
        origin_country: str,
        destination_country: str,
        weight_kg: float,
        priority_factors: Dict = None
    ) -> Optional[Dict]:
        """
        Advanced carrier selection with optimization

        priority_factors can include:
        - 'cost': weight for cost optimization (0-1)
        - 'speed': weight for delivery speed (0-1)
        - 'reliability': weight for reliability (0-1)
        """
        if not priority_factors:
            priority_factors = {'cost': 0.4, 'speed': 0.3, 'reliability': 0.3}

        rates = CarrierService.get_best_carrier_rates(
            origin_country, destination_country, weight_kg, max_results=10
        )

        if not rates:
            return None

        optimized_rates = []

        for rate in rates:
            carrier = rate['carrier_service'].carrier

            # Get performance stats
            performance = CarrierService.get_carrier_performance_stats(carrier, days=30)

            # Calculate composite score
            cost_score = 1 - (rate['selling_price'] / max(r['selling_price'] for r in rates))  # Lower cost = higher score
            speed_score = 1 - ((rate['estimated_days'] or 30) / 30)  # Faster = higher score
            reliability_score = performance['delivery_rate'] / 100  # Higher delivery rate = higher score

            composite_score = (
                priority_factors.get('cost', 0.4) * cost_score +
                priority_factors.get('speed', 0.3) * speed_score +
                priority_factors.get('reliability', 0.3) * reliability_score
            )

            rate['composite_score'] = composite_score
            rate['performance'] = performance
            optimized_rates.append(rate)

        # Sort by composite score (highest first)
        optimized_rates.sort(key=lambda x: x['composite_score'], reverse=True)

        return optimized_rates[0] if optimized_rates else None


class CarrierIntegrationService:
    """Service for handling carrier API integrations"""

    @staticmethod
    def get_carrier_credentials(company, carrier: Carrier) -> Optional[CarrierCredentials]:
        """Get active credentials for a company-carrier pair"""
        return CarrierCredentials.objects.filter(
            company=company,
            carrier=carrier,
            is_active=True,
            is_verified=True
        ).first()

    @staticmethod
    def validate_credentials(credentials: CarrierCredentials) -> Tuple[bool, str]:
        """Validate carrier credentials by making a test API call"""
        # This would implement actual API validation for each carrier
        # For now, return mock validation
        try:
            # Mock validation logic
            if credentials.api_key and credentials.api_secret:
                credentials.is_verified = True
                credentials.last_verified_at = timezone.now()
                credentials.verification_error = ""
                credentials.save()
                return True, "Credentials validated successfully"
            else:
                credentials.is_verified = False
                credentials.verification_error = "Missing API credentials"
                credentials.save()
                return False, "Missing API credentials"
        except Exception as e:
            credentials.is_verified = False
            credentials.verification_error = str(e)
            credentials.save()
            return False, f"Validation failed: {e}"

    @staticmethod
    def create_shipment_with_carrier(shipment_data: Dict, carrier: Carrier) -> Dict:
        """Create a shipment with the carrier's API"""
        # This would implement the actual carrier API integration
        # For now, return mock response
        return {
            'success': True,
            'tracking_number': f"{carrier.code.upper()}{shipment_data.get('id', '123456')}",
            'label_url': f"https://api.{carrier.code}.com/labels/{shipment_data.get('id')}",
            'carrier_shipment_id': f"{carrier.code}_{shipment_data.get('id')}"
        }