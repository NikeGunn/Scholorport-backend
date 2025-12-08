"""
Jobs/Careers App Serializers

Serializers for job posting API endpoints.
"""
from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Job


class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for Job model.
    Used for both listing and detail views.
    """

    class Meta:
        model = Job
        fields = [
            'id',
            'title',
            'slug',
            'department',
            'location',
            'type',
            'description',
            'requirements',
            'responsibilities',
            'application_email',
            'application_method',
            'is_active',
            'is_featured',
            'posted_at',
            'expires_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class JobListSerializer(serializers.ModelSerializer):
    """
    Serializer for job listings.
    Lighter version with essential fields for list views.
    """

    class Meta:
        model = Job
        fields = [
            'id',
            'title',
            'slug',
            'department',
            'location',
            'type',
            'description',
            'requirements',
            'responsibilities',
            'application_email',
            'application_method',
            'is_active',
            'is_featured',
            'posted_at',
            'expires_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class JobDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed job view.
    Returns all fields for a single job.
    """
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id',
            'title',
            'slug',
            'department',
            'location',
            'type',
            'description',
            'requirements',
            'responsibilities',
            'application_email',
            'application_method',
            'is_active',
            'is_featured',
            'posted_at',
            'expires_at',
            'created_at',
            'updated_at',
            'is_expired',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_expired']

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_expired(self, obj):
        """Return whether the job has expired."""
        return obj.is_expired


class JobCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new job posting.
    Handles validation and auto-generation of slug.
    """
    slug = serializers.SlugField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    is_featured = serializers.BooleanField(default=False)

    class Meta:
        model = Job
        fields = [
            'title',
            'slug',
            'department',
            'location',
            'type',
            'description',
            'requirements',
            'responsibilities',
            'application_email',
            'application_method',
            'is_active',
            'is_featured',
            'expires_at',
        ]

    def validate_application_email(self, value):
        """Validate email format."""
        if not value:
            raise serializers.ValidationError("Application email is required.")
        return value

    def validate_title(self, value):
        """Validate title."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title is required.")
        return value.strip()

    def validate_description(self, value):
        """Validate description."""
        if not value or not value.strip():
            raise serializers.ValidationError("Description is required.")
        return value

    def validate_type(self, value):
        """Validate job type if provided."""
        if value:
            valid_types = ['full-time', 'part-time', 'contract', 'internship']
            if value not in valid_types:
                raise serializers.ValidationError(
                    f"Invalid job type. Must be one of: {', '.join(valid_types)}"
                )
        return value

    def validate_expires_at(self, value):
        """Validate expiration date is in the future."""
        if value and value < timezone.now():
            raise serializers.ValidationError(
                "Expiration date must be in the future."
            )
        return value

    def create(self, validated_data):
        """Create a new job posting."""
        # If slug is empty or not provided, it will be auto-generated in model save()
        if 'slug' in validated_data and not validated_data['slug']:
            validated_data.pop('slug')
        return super().create(validated_data)


class JobUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing job posting.
    All fields are optional for partial updates.
    """
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = Job
        fields = [
            'title',
            'slug',
            'department',
            'location',
            'type',
            'description',
            'requirements',
            'responsibilities',
            'application_email',
            'application_method',
            'is_active',
            'is_featured',
            'posted_at',
            'expires_at',
        ]
        extra_kwargs = {
            'title': {'required': False},
            'description': {'required': False},
            'application_email': {'required': False},
        }

    def validate_type(self, value):
        """Validate job type if provided."""
        if value:
            valid_types = ['full-time', 'part-time', 'contract', 'internship']
            if value not in valid_types:
                raise serializers.ValidationError(
                    f"Invalid job type. Must be one of: {', '.join(valid_types)}"
                )
        return value

    def update(self, instance, validated_data):
        """Update job posting."""
        # Handle empty slug - regenerate from title if slug is cleared
        if 'slug' in validated_data and not validated_data['slug']:
            validated_data.pop('slug')
            # Force slug regeneration
            instance.slug = ''

        return super().update(instance, validated_data)
