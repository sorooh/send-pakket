"""
Advanced Analytics Views for Send-Pakket Platform
AI-powered analytics and predictive insights
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    PerformanceMetric, CarrierPerformance, CustomerInsight,
    RevenueAnalytics, APIUsageStats
)
from .serializers import (
    PerformanceMetricSerializer, CarrierPerformanceSerializer,
    CustomerInsightSerializer, RevenueAnalyticsSerializer,
    APIUsageStatsSerializer
)
from .services import (
    PredictiveAnalyticsService, CustomerSegmentationService,
    PerformanceOptimizationService
)


class PerformanceMetricViewSet(viewsets.ModelViewSet):
    """Performance metrics management"""

    queryset = PerformanceMetric.objects.all()
    serializer_class = PerformanceMetricSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset


class CarrierPerformanceViewSet(viewsets.ModelViewSet):
    """Carrier performance tracking"""

    queryset = CarrierPerformance.objects.all()
    serializer_class = CarrierPerformanceSerializer
    permission_classes = [IsAuthenticated]


class CustomerInsightViewSet(viewsets.ModelViewSet):
    """Customer insights management"""

    queryset = CustomerInsight.objects.all()
    serializer_class = CustomerInsightSerializer
    permission_classes = [IsAuthenticated]


class RevenueAnalyticsViewSet(viewsets.ModelViewSet):
    """Revenue analytics and forecasting"""

    queryset = RevenueAnalytics.objects.all()
    serializer_class = RevenueAnalyticsSerializer
    permission_classes = [IsAuthenticated]


class APIUsageStatsViewSet(viewsets.ModelViewSet):
    """API usage statistics"""

    queryset = APIUsageStats.objects.all()
    serializer_class = APIUsageStatsSerializer
    permission_classes = [IsAuthenticated]


class PredictiveAnalyticsViewSet(viewsets.ViewSet):
    """AI-powered predictive analytics"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def predict_delivery_time(self, request):
        """Predict delivery time for a shipment"""
        service = PredictiveAnalyticsService()
        prediction = service.predict_delivery_time(request.data)

        return Response({
            'predicted_delivery_time_hours': prediction,
            'confidence_level': 'medium',  # Would be calculated in production
            'factors_considered': ['weight', 'value', 'distance', 'carrier_performance']
        })

    @action(detail=False, methods=['post'])
    def predict_customer_churn(self, request):
        """Predict customer churn probability"""
        service = PredictiveAnalyticsService()
        risk_level, probability = service.predict_customer_churn(request.data)

        return Response({
            'churn_risk_level': risk_level,
            'churn_probability': probability,
            'recommendations': self._get_churn_recommendations(risk_level)
        })

    @action(detail=False, methods=['get'])
    def forecast_revenue(self, request):
        """Forecast future revenue"""
        days = int(request.query_params.get('days', 30))

        # Get historical data (last 90 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)

        historical_data = list(
            PerformanceMetric.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).values('date', 'total_revenue')
        )

        service = PredictiveAnalyticsService()
        forecast = service.forecast_revenue(historical_data, days)

        return Response({
            'forecast_period_days': days,
            'forecasted_revenue': forecast,
            'forecast_method': 'exponential_smoothing',
            'confidence_interval': '80%'  # Would be calculated in production
        })

    @action(detail=False, methods=['post'])
    def optimize_carrier_selection(self, request):
        """Get optimal carrier recommendations"""
        service = PredictiveAnalyticsService()
        recommendations = service.optimize_carrier_selection(request.data)

        return Response({
            'recommendations': recommendations,
            'optimization_criteria': ['success_rate', 'cost', 'speed', 'reliability']
        })

    def _get_churn_recommendations(self, risk_level: str) -> list:
        """Get recommendations based on churn risk"""
        recommendations = {
            'high': [
                'Immediate intervention required',
                'Schedule customer success call',
                'Offer special retention pricing',
                'Review recent support tickets'
            ],
            'medium': [
                'Monitor closely',
                'Send personalized offers',
                'Request feedback survey',
                'Review usage patterns'
            ],
            'low': [
                'Customer stable',
                'Continue regular engagement',
                'Consider upselling opportunities'
            ]
        }
        return recommendations.get(risk_level, [])


class CustomerSegmentationViewSet(viewsets.ViewSet):
    """Customer segmentation and personalization"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def segments(self, request):
        """Get customer segments"""
        service = CustomerSegmentationService()
        segments = service.segment_customers()

        return Response({
            'segments': segments,
            'segment_definitions': {
                'high_value': 'High spending, long-term customers',
                'growing': 'Rapidly increasing usage',
                'stable': 'Consistent, reliable customers',
                'at_risk': 'High churn risk',
                'new': 'Recently acquired customers'
            }
        })

    @action(detail=True, methods=['get'])
    def personalized_recommendations(self, request, pk=None):
        """Get personalized recommendations for a customer"""
        service = CustomerSegmentationService()
        recommendations = service.generate_personalized_recommendations(int(pk))

        return Response(recommendations)


class PerformanceOptimizationViewSet(viewsets.ViewSet):
    """Performance optimization recommendations"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def bottlenecks(self, request):
        """Analyze performance bottlenecks"""
        service = PerformanceOptimizationService()
        issues = service.analyze_performance_bottlenecks()

        return Response({
            'bottlenecks': issues,
            'analysis_period': 'last_7_days',
            'total_issues': len(issues)
        })

    @action(detail=False, methods=['get'])
    def optimization_recommendations(self, request):
        """Get optimization recommendations"""
        service = PerformanceOptimizationService()
        recommendations = service.generate_optimization_recommendations()

        return Response({
            'recommendations': recommendations,
            'categories': ['database', 'caching', 'api', 'infrastructure']
        })
