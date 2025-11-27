"""
Core API Serializers - Send-Pakket Platform
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Company, Address, APIKey, ActivityLog


class UserSerializer(serializers.ModelSerializer):
    """User serializer"""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'is_active', 'is_staff', 'date_joined', 'last_login',
            'company'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    """User creation serializer"""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'password', 'password_confirm'
        ]

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['email'],  # Since USERNAME_FIELD is email
            **validated_data
        )
        return user


class CompanySerializer(serializers.ModelSerializer):
    """Company serializer"""

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'registration_number', 'tax_id', 'website',
            'phone', 'email', 'address', 'business_type', 'industry',
            'is_verified', 'verification_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'verification_status', 'created_at', 'updated_at']


class AddressSerializer(serializers.ModelSerializer):
    """Address serializer"""

    class Meta:
        model = Address
        fields = [
            'id', 'company', 'type', 'name', 'street_address',
            'city', 'state', 'postal_code', 'country',
            'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class APIKeySerializer(serializers.ModelSerializer):
    """API Key serializer"""

    class Meta:
        model = APIKey
        fields = [
            'id', 'company', 'name', 'key', 'permissions',
            'is_active', 'expires_at', 'last_used', 'created_at'
        ]
        read_only_fields = ['id', 'key', 'last_used', 'created_at']


class ActivityLogSerializer(serializers.ModelSerializer):
    """Activity log serializer"""

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'company', 'user', 'action', 'resource_type',
            'resource_id', 'details', 'ip_address', 'user_agent',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']