"""
Contact App Serializers
"""
from rest_framework import serializers
from .models import ContactSubmission


class ContactSubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new contact submission (public)."""

    class Meta:
        model = ContactSubmission
        fields = [
            'name',
            'email',
            'phone',
            'message',
            'type',
        ]

    def validate_message(self, value):
        """Ensure message is not empty and has reasonable length."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        if len(value) > 5000:
            raise serializers.ValidationError("Message must be less than 5000 characters.")
        return value


class ContactSubmissionResponseSerializer(serializers.ModelSerializer):
    """Serializer for contact submission response."""

    class Meta:
        model = ContactSubmission
        fields = [
            'id',
            'name',
            'email',
            'created_at',
        ]


class ContactSubmissionAdminSerializer(serializers.ModelSerializer):
    """Full serializer for admin operations."""

    class Meta:
        model = ContactSubmission
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'message',
            'type',
            'read',
            'notes',
            'ip_address',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'name', 'email', 'phone', 'message', 'type', 'ip_address', 'created_at', 'updated_at']


class ContactSubmissionListSerializer(serializers.ModelSerializer):
    """Serializer for listing contact submissions (admin)."""

    class Meta:
        model = ContactSubmission
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'type',
            'read',
            'created_at',
        ]
