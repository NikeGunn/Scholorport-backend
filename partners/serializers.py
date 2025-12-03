"""
Partners App Serializers
"""
from rest_framework import serializers
from .models import Partner


class PartnerSerializer(serializers.ModelSerializer):
    """Serializer for Partner model."""

    class Meta:
        model = Partner
        fields = [
            'id',
            'name',
            'type',
            'country',
            'logo',
            'description',
            'website',
            'featured',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PartnerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing partners (public)."""

    class Meta:
        model = Partner
        fields = [
            'id',
            'name',
            'type',
            'country',
            'logo',
            'description',
            'website',
            'featured',
        ]


class PartnerAdminSerializer(serializers.ModelSerializer):
    """Full serializer for admin operations."""

    class Meta:
        model = Partner
        fields = [
            'id',
            'name',
            'type',
            'country',
            'logo',
            'description',
            'website',
            'featured',
            'is_active',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
