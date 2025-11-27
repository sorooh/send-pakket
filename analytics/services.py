"""
Advanced Analytics Services for Send-Pakket Platform
Using AI/ML for predictive analytics and customer insights
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from django.db.models import Q, Avg, Count, Sum, F
from django.utils import timezone

from .models import PerformanceMetric, CustomerInsight, CarrierPerformance, RevenueAnalytics


class PredictiveAnalyticsService:
    """AI-powered predictive analytics for shipping platform"""

    def __init__(self):
        self.scaler = StandardScaler()

    def predict_delivery_time(self, shipment_data: Dict) -> float:
        """
        Predict delivery time using ML model
        """
        # Prepare features
        features = self._prepare_delivery_features(shipment_data)

        # Load or train model (simplified for demo)
        model = self._get_delivery_time_model()

        # Make prediction
        prediction = model.predict([features])[0]

        return max(1.0, prediction)  # Minimum 1 hour

    def predict_customer_churn(self, customer_data: Dict) -> Tuple[str, float]:
        """
        Predict customer churn probability
        Returns: (risk_level, probability)
        """
        features = self._prepare_churn_features(customer_data)

        model = self._get_churn_model()

        probability = model.predict_proba([features])[0][1]

        if probability > 0.7:
            risk_level = 'high'
        elif probability > 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return risk_level, probability

    def forecast_revenue(self, historical_data: List[Dict], periods: int = 30) -> List[float]:
        """
        Forecast future revenue using time series analysis
        """
        if not historical_data:
            return [0] * periods

        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()

        # Simple exponential smoothing for demo
        if len(df) < 7:
            last_value = df['total_revenue'].iloc[-1] if not df.empty else 0
            return [last_value] * periods

        # Calculate growth rate
        recent_growth = df['total_revenue'].pct_change().tail(7).mean()

        forecasts = []
        last_value = df['total_revenue'].iloc[-1]

        for _ in range(periods):
            next_value = last_value * (1 + recent_growth)
            forecasts.append(float(next_value))
            last_value = next_value

        return forecasts

    def optimize_carrier_selection(self, shipment_requirements: Dict) -> List[Dict]:
        """
        Recommend optimal carriers based on historical performance
        """
        # Get carrier performance data
        carriers = CarrierPerformance.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).select_related('carrier')

        recommendations = []

        for carrier_perf in carriers:
            score = self._calculate_carrier_score(carrier_perf, shipment_requirements)
            recommendations.append({
                'carrier_id': carrier_perf.carrier.id,
                'carrier_name': carrier_perf.carrier.name,
                'score': score,
                'estimated_cost': float(carrier_perf.avg_cost_per_shipment or 0),
                'estimated_delivery_time': float(carrier_perf.avg_delivery_time_hours or 24),
                'success_rate': float(carrier_perf.delivery_success_rate or 0),
            })

        # Sort by score descending
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        return recommendations[:5]  # Top 5 recommendations

    def _prepare_delivery_features(self, shipment_data: Dict) -> List[float]:
        """Prepare features for delivery time prediction"""
        return [
            float(shipment_data.get('weight_kg', 1.0)),
            float(shipment_data.get('value_eur', 50.0)),
            shipment_data.get('is_international', 0),
            shipment_data.get('priority_level', 1),  # 1-5 scale
            len(shipment_data.get('origin_country', 'NL')),
            len(shipment_data.get('destination_country', 'NL')),
        ]

    def _prepare_churn_features(self, customer_data: Dict) -> List[float]:
        """Prepare features for churn prediction"""
        return [
            customer_data.get('account_age_days', 0),
            customer_data.get('total_shipments', 0),
            float(customer_data.get('total_spent', 0)),
            customer_data.get('days_since_last_activity', 30),
            customer_data.get('complaints_count', 0),
            float(customer_data.get('avg_delivery_rating', 3.0)),
        ]

    def _get_delivery_time_model(self) -> RandomForestRegressor:
        """Get or create delivery time prediction model"""
        # In production, this would load a trained model
        # For demo, create a simple model
        model = RandomForestRegressor(n_estimators=10, random_state=42)

        # Dummy training data
        X = np.random.rand(100, 6)
        y = np.random.rand(100) * 72 + 1  # 1-73 hours

        model.fit(X, y)
        return model

    def _get_churn_model(self) -> RandomForestClassifier:
        """Get or create churn prediction model"""
        # In production, this would load a trained model
        model = RandomForestClassifier(n_estimators=10, random_state=42)

        # Dummy training data
        X = np.random.rand(100, 6)
        y = np.random.randint(0, 2, 100)  # 0=no churn, 1=churn

        model.fit(X, y)
        return model

    def _calculate_carrier_score(self, carrier_perf: CarrierPerformance, requirements: Dict) -> float:
        """Calculate carrier recommendation score"""
        score = 0.0

        # Success rate (40% weight)
        success_rate = float(carrier_perf.delivery_success_rate or 0)
        score += success_rate * 0.4

        # Cost efficiency (30% weight) - lower cost is better
        avg_cost = float(carrier_perf.avg_cost_per_shipment or 100)
        max_cost = 200  # Assume max expected cost
        cost_score = max(0, (max_cost - avg_cost) / max_cost)
        score += cost_score * 0.3

        # Speed (20% weight) - faster is better
        avg_time = float(carrier_perf.avg_delivery_time_hours or 48)
        max_time = 96  # Assume max expected time
        speed_score = max(0, (max_time - avg_time) / max_time)
        score += speed_score * 0.2

        # API reliability (10% weight)
        api_uptime = float(carrier_perf.api_uptime_percent or 95)
        score += (api_uptime / 100) * 0.1

        return score


class CustomerSegmentationService:
    """AI-powered customer segmentation and personalization"""

    def segment_customers(self) -> Dict[str, List[int]]:
        """
        Segment customers based on behavior patterns
        Returns: {segment_name: [company_ids]}
        """
        customers = CustomerInsight.objects.all()

        segments = {
            'high_value': [],
            'growing': [],
            'stable': [],
            'at_risk': [],
            'new': []
        }

        for customer in customers:
            segment = self._classify_customer_segment(customer)
            segments[segment].append(customer.company.id)

        return segments

    def generate_personalized_recommendations(self, company_id: int) -> Dict:
        """
        Generate personalized recommendations for a customer
        """
        try:
            insight = CustomerInsight.objects.get(company_id=company_id)
        except CustomerInsight.DoesNotExist:
            return {'recommendations': []}

        recommendations = []

        # Analyze spending patterns
        if insight.total_spent > 1000:
            recommendations.append({
                'type': 'subscription_upgrade',
                'title': 'Upgrade to Premium Plan',
                'description': 'Based on your shipping volume, you could save with our premium plan.',
                'priority': 'high'
            })

        # Analyze carrier preferences
        if insight.preferred_carriers:
            top_carrier = max(insight.preferred_carriers.items(), key=lambda x: x[1])
            recommendations.append({
                'type': 'carrier_loyalty',
                'title': f'Special Offer from {top_carrier[0]}',
                'description': 'Exclusive discounts available for your preferred carrier.',
                'priority': 'medium'
            })

        # Analyze usage patterns
        if insight.avg_monthly_shipments < 10:
            recommendations.append({
                'type': 'usage_increase',
                'title': 'Increase Shipping Volume',
                'description': 'Consider bulk shipping options for better rates.',
                'priority': 'low'
            })

        return {'recommendations': recommendations}

    def _classify_customer_segment(self, customer: CustomerInsight) -> str:
        """Classify customer into segment"""
        if customer.total_spent > 5000 and customer.account_age_days > 180:
            return 'high_value'
        elif customer.monthly_growth_rate and customer.monthly_growth_rate > 0.2:
            return 'growing'
        elif customer.churn_risk_level == 'high':
            return 'at_risk'
        elif customer.account_age_days < 30:
            return 'new'
        else:
            return 'stable'


class PerformanceOptimizationService:
    """AI-powered performance optimization recommendations"""

    def analyze_performance_bottlenecks(self) -> List[Dict]:
        """
        Analyze system performance and identify bottlenecks
        """
        issues = []

        # Check API performance
        api_stats = APIUsageStats.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=7)
        ).aggregate(
            avg_response_time=Avg('avg_response_time_ms'),
            error_rate=Avg(F('failed_requests') * 100.0 / F('total_requests'))
        )

        if api_stats['avg_response_time'] and api_stats['avg_response_time'] > 1000:
            issues.append({
                'type': 'api_performance',
                'severity': 'high',
                'title': 'Slow API Response Times',
                'description': f'Average response time is {api_stats["avg_response_time"]:.1f}ms',
                'recommendation': 'Consider optimizing database queries and adding caching'
            })

        if api_stats['error_rate'] and api_stats['error_rate'] > 5:
            issues.append({
                'type': 'api_errors',
                'severity': 'high',
                'title': 'High API Error Rate',
                'description': f'Error rate is {api_stats["error_rate"]:.1f}%',
                'recommendation': 'Review error logs and improve error handling'
            })

        # Check carrier performance
        carrier_issues = CarrierPerformance.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=7),
            delivery_success_rate__lt=0.95
        )

        for carrier in carrier_issues:
            issues.append({
                'type': 'carrier_performance',
                'severity': 'medium',
                'title': f'Low Success Rate for {carrier.carrier.name}',
                'description': f'Success rate: {carrier.delivery_success_rate}%',
                'recommendation': 'Consider alternative carriers or negotiate better terms'
            })

        return issues

    def generate_optimization_recommendations(self) -> List[Dict]:
        """
        Generate system optimization recommendations
        """
        recommendations = []

        # Database optimization
        recommendations.append({
            'category': 'database',
            'title': 'Database Query Optimization',
            'description': 'Implement database indexing and query optimization',
            'impact': 'high',
            'effort': 'medium'
        })

        # Caching strategy
        recommendations.append({
            'category': 'caching',
            'title': 'Implement Redis Caching',
            'description': 'Add Redis caching for frequently accessed data',
            'impact': 'high',
            'effort': 'low'
        })

        # API rate limiting
        recommendations.append({
            'category': 'api',
            'title': 'Implement API Rate Limiting',
            'description': 'Add rate limiting to prevent API abuse',
            'impact': 'medium',
            'effort': 'low'
        })

        return recommendations